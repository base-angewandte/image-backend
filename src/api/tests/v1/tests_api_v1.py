import io
import json
import zipfile

import shortuuid
from rest_framework import status

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from artworks.models import (
    Album,
    Artwork,
    DiscriminatoryTerm,
    Folder,
    PermissionsRelation,
    Person,
)

from .. import APITestCase, temporary_image
from . import VERSION

User = get_user_model()


class ArtworkTests(APITestCase):
    def test_artworks_list(
        self,
    ):
        """Test the retrieval of all artworks for a user."""
        url = reverse('artwork-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        num_results = 15
        self.assertEqual(content['total'], num_results)
        self.assertEqual(len(content['results']), num_results)
        self.limit_test(url, 5, num_results)
        combinations = [
            {'limit': 5, 'offset': 5},
            {'limit': 3, 'offset': 6},
            {'limit': 10, 'offset': 2},
            {'limit': 4, 'offset': 4},
        ]
        self.offset_test(url, combinations, num_results)

    def test_artworks_retrieve(self):
        """Test the retrieval of an artwork."""
        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=True,
        )
        url = reverse('artwork-detail', kwargs={'pk': artwork.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], artwork.title)
        self.assertEqual(
            content['image_original'],
            f'http://testserver{artwork.image_original.url}',
        )
        self.assertEqual(
            content['image_fullsize'],
            f'http://testserver{artwork.image_fullsize.url}',
        )
        self.assertEqual(content['artists'], [])

    def test_artworks_image(self):
        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=True,
        )
        url = reverse(
            'artwork-image',
            kwargs={
                'pk': artwork.pk,
                'height': 30,
                'width': 30,
                'method': 'crop',
                'version': VERSION,
            },
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_labels_list(self):
        """Test the retrieval of artwork labels."""
        Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            checked=True,
            published=True,
        )
        url = reverse('artwork-labels', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], _('Title'))
        self.assertEqual(content['keywords'], _('Keywords'))

    def test_artworks_retrieve_albums(self):
        """Test the retrieval of the albums current user has added this artwork
        to."""
        Artwork.objects.create(title='Test Artwork', image_original=temporary_image())
        album = Album.objects.create(title='Test Album1', user=self.user)
        url = reverse('album-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 4)
        self.assertEqual(content['results'][3]['id'], album.id)

    def test_artworks_download(self):
        """Test the download of an artwork + metadata."""

        # create artwork
        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=True,
        )

        # create person and add as artist
        artist = Person.objects.create(name='TestArtist')
        artwork.artists.add(artist)

        url = reverse('artwork-download', kwargs={'pk': artwork.pk, 'version': VERSION})
        response = self.client.get(url, format='json')

        file_name = slugify(artwork.title)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.get('Content-Disposition'),
            f'attachment; filename="{file_name}.zip"',
        )

        with (
            io.BytesIO(b''.join(response.streaming_content)) as buf_bytes,
            zipfile.ZipFile(buf_bytes, 'r') as zip_file,
        ):
            self.assertIsNone(zip_file.testzip())

            metadata_file = f'{file_name}_metadata.txt'
            self.assertIn(metadata_file, zip_file.namelist())

            with zip_file.open(metadata_file) as f:
                metadata_content = f.read().decode('utf-8')
                self.assertIn(artwork.title, metadata_content)
                self.assertIn(artist.name, metadata_content)


class AlbumsTests(APITestCase):
    def test_albums_list(self):
        """Test the retrieval of all albums for a user."""
        Album.objects.create(title='Test Album1', user=self.user)
        Album.objects.create(title='Test Album2', user=self.user)
        url = reverse('album-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        num_results = 5
        self.assertEqual(content['total'], num_results)
        self.assertEqual(len(content['results']), num_results)
        self.limit_test(url, 5, num_results)
        combinations = [
            {'limit': 1, 'offset': 2},
            {'limit': 2, 'offset': 3},
            {'limit': 2, 'offset': 1},
        ]
        self.offset_test(url, combinations, num_results)

    def test_albums_create(self):
        """Test the creation of a new album."""
        url = reverse('album-list', kwargs={'version': VERSION})
        data = {'title': 'Test Album'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # TODO: these old tests rely on no other available test data at all and don't
        #   seem to be very useful in a more elaborated test scenario. Therefore
        #   they are deactivated but left here, until the whole test case is reworked
        # self.assertEqual(Album.objects.count(), 1)
        # self.assertEqual(Album.objects.get().title, data['title'])

    def test_albums_retrieve(self):
        """Test the retrieval of an album."""
        album = Album.objects.create(title='Test Album', user=self.user)
        url = reverse('album-detail', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], album.title)
        self.assertEqual(content['number_of_artworks'], 0)
        self.assertEqual(content['slides'], [])
        self.assertEqual(content['owner']['id'], self.user.username)
        self.assertEqual(content['permissions'], [])

    def test_albums_update(self):
        """Test the updating of an album."""
        album = Album.objects.create(title='Test Album', user=self.user)
        url = reverse('album-detail', kwargs={'pk': album.pk, 'version': VERSION})
        data = {'title': 'Test Album'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TODO: these old tests rely on no other available test data at all and don't
        #   seem to be very useful in a more elaborated test scenario. Therefore
        #   they are deactivated but left here, until the whole test case is reworked
        # self.assertEqual(Album.objects.count(), 1)
        # self.assertEqual(Album.objects.get().title, data['title'])

    def test_albums_destroy(self):
        """Test the deletion of an album."""
        album = Album.objects.create(title='Test Album', user=self.user)
        url = reverse('album-detail', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_albums_append_artwork(self):
        """Test the appending of artworks to album slides."""
        album = Album.objects.create(title='Test Album', user=self.user)
        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
        )
        url_post = reverse(
            'album-append-artwork',
            kwargs={'pk': album.pk, 'version': VERSION},
        )
        data = {'id': artwork.pk}
        response = self.client.post(url_post, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Also check if the slide was appended properly
        url_get = reverse('album-detail', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url_get, format='json')
        content = json.loads(response.content)
        slide = content['slides'][0]
        self.assertEqual(type(slide['id']), str)
        self.assertEqual(len(slide['id']), 22)  # default length of a shortuuid
        self.assertEqual(type(slide['items'][0]), dict)
        self.assertEqual(slide['items'][0]['id'], artwork.pk)
        response = self.client.get(f'{url_get}?details=true', format='json')
        content = json.loads(response.content)
        slide = content['slides'][0]
        self.assertEqual(slide['items'][0]['title'], artwork.title)
        # also try to append a non-existing artworks
        data = {'id': 98765}
        response = self.client.post(url_post, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_albums_slides(self):
        """Test the retrieval of album slides."""
        album = Album.objects.create(title='Test Album', user=self.user)
        id1 = shortuuid.uuid()
        id2 = shortuuid.uuid()
        album.slides = [
            {'id': id1, 'items': [{'id': 1}, {'id': 2}]},
            {'id': id2, 'items': [{'id': 3}]},
        ]
        album.save()
        url = reverse('album-slides', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slides = json.loads(response.content)
        self.assertEqual(type(slides), list)
        self.assertEqual(len(slides), 2)
        self.assertEqual(slides[0]['id'], id1)
        self.assertEqual(slides[1]['id'], id2)
        self.assertEqual(len(slides[0]['items']), 2)
        self.assertEqual(len(slides[1]['items']), 1)
        self.assertEqual(slides[0]['items'][0]['id'], 1)
        self.assertEqual(slides[0]['items'][1]['id'], 2)
        self.assertEqual(slides[1]['items'][0]['id'], 3)

    def test_albums_create_slides(self):
        """Test the creation of album slides."""
        album = Album.objects.create(title='Test Album', user=self.user)
        artwork1 = Artwork.objects.create(
            title='Test Artwork 1',
            image_original=temporary_image(),
        )
        artwork2 = Artwork.objects.create(
            title='Test Artwork 2',
            image_original=temporary_image(),
        )
        artwork3 = Artwork.objects.create(
            title='Test Artwork 3',
            image_original=temporary_image(),
        )
        url = reverse('album-slides', kwargs={'pk': album.pk, 'version': VERSION})
        data = [
            {'items': [{'id': artwork1.pk}, {'id': artwork2.pk}]},
            {'items': [{'id': artwork3.pk}]},
        ]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 2)
        self.assertEqual(type(content[0]), dict)
        self.assertEqual(type(content[1]), dict)
        self.assertEqual(content[0].get('items'), data[0]['items'])
        self.assertEqual(content[1].get('items'), data[1]['items'])
        # also test creating slides with non-existing artworks
        data.append({'items': [{'id': 98765}]})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_albums_permissions(self):
        """Test the retrieval of album permissions."""
        album = Album.objects.create(title='Test Album', user=self.user)
        user = User.objects.create(username='abc1def2')
        PermissionsRelation.objects.create(album=album, user=user)
        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)
        self.assertEqual(content[0]['user']['id'], user.username)
        self.assertEqual(content[0]['permissions'][0]['id'], 'VIEW')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_albums_create_permissions(self):
        """Test the creation of album permissions."""
        album = Album.objects.create(title='Test Album', user=self.user)
        new_user = User.objects.create(username='abc1def2')
        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        data = [{'user': f'{new_user.username}', 'permissions': [{'id': 'VIEW'}]}]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content[0]['permissions'][0]['id'], 'VIEW')
        self.assertEqual(content[0]['user']['id'], new_user.username)

    def test_albums_destroy_permissions(self):
        """Test the deletion of album permissions."""
        album = Album.objects.create(title='Test Album', user=self.user)
        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_albums_download(self):
        """Test the download of an album."""
        artwork1 = Artwork.objects.create(
            title='Test Artwork 1',
            image_original=temporary_image(),
        )
        artwork2 = Artwork.objects.create(
            title='Test Artwork 2',
            image_original=temporary_image(),
        )
        artwork3 = Artwork.objects.create(
            title='Test Artwork 3',
            image_original=temporary_image(),
        )
        album = Album.objects.create(
            title='Test Album',
            user=self.user,
            slides=[
                {
                    'id': shortuuid.uuid(),
                    'items': [
                        {'id': artwork1.id},
                        {'id': artwork2.id},
                    ],
                },
                {
                    'id': shortuuid.uuid(),
                    'items': [
                        {'id': artwork3.id},
                    ],
                },
            ],
        )
        url = reverse('album-download', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(response.content), bytes)


class FoldersTests(APITestCase):
    def test_folders_list(self):
        """Test the retrieval of all albums for a user."""
        folder1 = Folder.objects.create(title='Test Folder', owner=self.user)
        folder2 = Folder.objects.create(title='Test Folder2', owner=self.user)
        Folder.objects.create(title='Test Folder3', owner=self.user)
        Folder.objects.create(title='Test Folder4', owner=self.user)
        url = reverse('folder-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        num_results = 4
        self.assertEqual(len(content), num_results)
        self.assertEqual(content[0]['title'], folder1.title)
        self.assertEqual(content[0]['id'], folder1.id)
        self.assertEqual(content[1]['title'], folder2.title)
        self.assertEqual(content[1]['id'], folder2.id)
        self.limit_test(url, 4, num_results)
        combinations = [
            {'limit': 1, 'offset': 0},
            {'limit': 1, 'offset': 1},
            {'limit': 2, 'offset': 2},
            {'limit': 3, 'offset': 0},
        ]
        self.offset_test(url, combinations, num_results)

    def test_folder_retrieve(self):
        """Test the retrieval of an album."""
        folder = Folder.objects.create(title='Test Folder', owner=self.user)
        url = reverse('folder-detail', kwargs={'pk': folder.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], folder.title)
        self.assertEqual(content['id'], folder.id)

    def test_folder_create(self):
        # Todo: endpoint is only a placeholder at this time
        pass


class DiscriminatoryTermsTests(APITestCase):
    def test_discriminatory_terms(self):
        """Test the retrieval of the discriminatory terms list."""
        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=True,
        )
        dt1 = DiscriminatoryTerm.objects.create(term='Barbarian')
        dt2 = DiscriminatoryTerm.objects.create(term='Colored')
        dt3 = DiscriminatoryTerm.objects.create(term='Disabled')
        artwork.discriminatory_terms.add(dt1, dt2, dt3)
        url = reverse('artwork-detail', kwargs={'pk': artwork.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(type(content), dict)
        terms = content.get('discriminatory_terms')
        self.assertEqual(type(terms), list)
        self.assertEqual(len(terms), 3)
        self.assertEqual(terms[2], 'Disabled')


class PermissionsTests(APITestCase):
    def test_labels_list(self):
        """Test the retrieval of permissions."""
        url = reverse('permission-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content[0]['id'], 'VIEW')
        self.assertEqual(content[0]['label'], _('VIEW'))
        self.assertEqual(content[1]['id'], 'EDIT')
        self.assertEqual(content[1]['label'], _('EDIT'))


class SearchTests(APITestCase):
    def test_search(self):
        """Test the search."""
        # Todo (possible): extend? as there are several usecases

        artist = Person.objects.create(name='TestArtist')
        artwork1 = Artwork.objects.create(
            title='Test Artwork 1',
            image_original=temporary_image(),
            published=True,
        )
        artwork2 = Artwork.objects.create(
            title='Test Artwork 2',
            image_original=temporary_image(),
            published=True,
        )
        artwork1.artists.add(artist)
        artwork2.artists.add(artist)
        artwork1.save()
        artwork2.save()
        data = {
            'limit': 30,
            'offset': 0,
            'exclude': [],
            'q': 'test',
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': ['artist'],
                },
            ],
        }
        url = reverse('search', kwargs={'version': VERSION})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 2)
        self.assertEqual(content['results'][0]['title'], artwork2.title)
        self.assertEqual(content['results'][1]['artists'][0]['value'], artist.name)

    def test_search_location(self):
        # location test title_english
        data = {
            'filters': [
                {
                    'id': 'location',
                    'filter_values': ['Eisenkappel'],
                },
            ],
        }
        url = reverse('search', kwargs={'version': VERSION})
        response = self.client.post(
            url,
            data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(
            content['results'][0]['title'],
            'loc test zelez',
        )

    def test_search_labels_list(self):
        url = reverse('search-filters', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title']['type'], 'array')
        self.assertEqual(len(content['place_of_production']['items']), 2)


class TosTests(APITestCase):
    def test_tos_accept(self):
        self.user.tos_accepted = False
        self.user.save()
        url_get = reverse('tos-list', kwargs={'version': VERSION})
        response = self.client.get(url_get, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(type(content), dict)
        self.assertEqual(content['tos_accepted'], False)
        self.assertEqual(type(content['tos_text']), str)
        url_post = reverse('tos-accept', kwargs={'version': VERSION})
        response = self.client.post(url_post, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(url_post, format='json')  # try once more
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url_get, format='json')
        content = json.loads(response.content)
        self.assertEqual(content['tos_accepted'], True)

    def test_permitted_endpoints(self):
        self.user.tos_accepted = False
        self.user.save()
        # routes which should be accessible without accepted ToS
        # excluding tos-list and tos-accepted, which are tested above
        routes_200 = ['api-root', 'user-list']
        # sample (and simple get) routes which should not be accessible without accepted ToS
        routes_403 = [
            'album-list',
            'artwork-list',
            'artwork-labels',
            'folder-list',
            'permission-list',
            'search-filters',
        ]
        for route in routes_200:
            url = reverse(route, kwargs={'version': VERSION})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        for route in routes_403:
            url = reverse(route, kwargs={'version': VERSION})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # now again with accepted tos
        self.user.tos_accepted = True
        self.user.save()
        for route in routes_403:
            url = reverse(route, kwargs={'version': VERSION})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserDataTests(APITestCase):
    def test_user_data(self):
        """Test the retrieval of current user data."""
        url = reverse('user-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['id'], 'temporary')
        self.assertEqual(content['email'], 'temporary@uni-ak.ac.at')

    def test_user_preferences(self):
        """Test retrieving and setting user preferences."""

        def check_get_user(images, folders):
            """Sends a GET request to /user/ and tests the result."""
            url = reverse('user-list', kwargs={'version': VERSION})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            content = json.loads(response.content)
            self.assertEqual(type(content['preferences']), dict)
            self.assertEqual(content['preferences']['display_images'], images)
            self.assertEqual(content['preferences']['display_folders'], folders)

        def check_get_preferences(images, folders):
            """Sends a GET request to /user/preferences/ and tests the
            result."""
            url = reverse('user-preferences', kwargs={'version': VERSION})
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            content = json.loads(response.content)
            self.assertEqual(type(content), dict)
            self.assertEqual(content['display_images'], images)
            self.assertEqual(content['display_folders'], folders)

        # check the default response from /user/ and /user/prefereces/ endpoint
        check_get_user('crop', 'list')
        check_get_preferences('crop', 'list')

        # change and check both preferences through POST to /user/preferences/
        url = reverse('user-preferences', kwargs={'version': VERSION})
        data = {'display_images': 'resize', 'display_folders': 'grid'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(type(content), dict)
        self.assertEqual(content['display_images'], 'resize')
        self.assertEqual(content['display_folders'], 'grid')
        check_get_preferences('resize', 'grid')
        check_get_user('resize', 'grid')

        # change and check one option at a time through PATCH to /user/preferences/
        response = self.client.patch(url, {'display_images': 'crop'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(type(content), dict)
        self.assertEqual(content['display_images'], 'crop')
        response = self.client.patch(url, {'display_folders': 'list'}, format='json')
        content = json.loads(response.content)
        self.assertEqual(content['display_folders'], 'list')
        check_get_preferences('crop', 'list')

    def test_user_preferences_parameters(self):
        """Test for the validity of POST/PATCH request parameters."""
        url = reverse('user-preferences', kwargs={'version': VERSION})
        response = self.client.patch(url, {'display_folders': 'abc'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'display_images': 'abc', 'display_folders': 'grid'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(url, {'display_folders': 'grid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AutocompleteTests(APITestCase):
    def test_autocomplete(self):
        """Test the retrieval of autocomplete results."""
        url = reverse('autocomplete', kwargs={'version': VERSION})

        # test general parameter parsing
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(f'{url}?q=a', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(f'{url}?type=users', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(f'{url}?q=a&type=nonexistenttype', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(f'{url}?q=a&type=users&limit=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test single autocomplete type
        response = self.client.get(f'{url}?q=student&type=users', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['id'], 's1234567')
        self.assertEqual(content[0]['label'], 'Test Student')

        # test multiple autocomplete types
        requested_types = ['titles', 'artists', 'users', 'keywords', 'locations']
        response = self.client.get(
            f'{url}?q=test&type={",".join(requested_types)}',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 5)
        for i, result_type in enumerate(content):
            self.assertEqual(type(result_type), dict)
            self.assertEqual(result_type['id'], requested_types[i])
            self.assertEqual(type(result_type['data']), list)
            for item in result_type['data']:
                self.assertEqual(type(item), dict)
                self.assertEqual('id' in item, True)
                self.assertEqual('label' in item, True)
        self.assertEqual(len(content[1]['data']), 0)  # no artists
        self.assertEqual(len(content[3]['data']), 0)  # no keywords
        self.assertEqual(len(content[4]['data']), 0)  # no locations
        self.assertEqual(len(content[2]['data']), 2)  # 2 users
        self.assertLess(3, len(content[0]['data']))  # more than 3 artwork titles
        self.assertEqual(
            content[2]['data'][0]['label'],
            'Test Lecturer',
        )  # alphabetic ordering
        self.assertEqual(
            content[2]['data'][1]['label'],
            'Test Student',
        )  # alphabetic ordering

        # test (default) limiting
        response = self.client.get(f'{url}?q=e&type=titles', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 10)  # default limit
        response = self.client.get(f'{url}?q=e&type=titles&limit=100', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 15)
        response = self.client.get(f'{url}?q=e&type=titles&limit=5', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 5)
        # now also test multi type response
        response = self.client.get(f'{url}?q=e&type=titles,locations', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content[0]['data']), 10)  # default limit
        self.assertEqual(len(content[0]['data']), 10)  # default limit
        response = self.client.get(
            f'{url}?q=e&type=titles,locations&limit=100',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertLess(10, len(content[0]['data']))
        self.assertLess(10, len(content[0]['data']))
        response = self.client.get(
            f'{url}?q=e&type=titles,locations&limit=5',
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content[0]['data']), 5)
        self.assertEqual(len(content[0]['data']), 5)

    def test_name_english_locations(self):
        url = reverse('autocomplete', kwargs={'version': VERSION})
        # Check if the 'name_en' is returned when 'accept-language' header is 'en'
        response = self.client.get(
            f'{url}?q=Bad Eisenkappel&type=locations',
            format='json',
            headers={'accept-language': 'en'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 2)
        self.assertEqual(content['label'], 'Bad Eisenkappel, English')

        # Check if the 'name' is returned when 'accept-language' header is 'en' and 'name_en' is empty
        response = self.client.get(
            f'{url}?q=Galerie Vorspann&type=locations',
            format='json',
            headers={'accept-language': 'en'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 2)
        self.assertEqual(
            content['label'],
            'Galerie Vorspann',
        )

        # Check if the 'name' is returned when 'accept-language' header is 'de'
        response = self.client.get(
            f'{url}?q=Bad Eisenkappel&type=locations',
            format='json',
            headers={'accept-language': 'de'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 2)
        self.assertEqual(
            content['label'],
            'Bad Eisenkappel',
        )

    def test_name_english_keywords(self):
        url = reverse('autocomplete', kwargs={'version': VERSION})
        # Check if the 'name_en' is returned when 'accept-language' header is 'en'
        response = self.client.get(
            f'{url}?q=Art Déco&type=keywords',
            format='json',
            headers={'accept-language': 'en'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 2)
        self.assertEqual(content['label'], 'Art Déco, English')
        # Check if the 'name' is returned when 'accept-language' header is 'en', although name_en is empty
        response = self.client.get(
            f'{url}?q=Art Brut&type=keywords',
            format='json',
            headers={'accept-language': 'en'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 2)
        self.assertEqual(content['label'], 'Art Brut')
        # Check if the 'name' is returned when 'accept-language' header is 'de'
        response = self.client.get(
            f'{url}?q=Art Brut&type=keywords',
            format='json',
            headers={'accept-language': 'de'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 2)
        self.assertEqual(content['label'], 'Art Brut')

    def test_title(self):
        url = reverse('autocomplete', kwargs={'version': VERSION})
        # Check if the 'title' is returned when 'accept-language' header is 'de'
        response = self.client.get(
            f'{url}?q=loc test aut&type=titles',
            format='json',
            headers={'accept-language': 'de'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 3)
        self.assertEqual(content['label'], 'loc test aut')
        # Check if the 'title' is returned when 'accept-language' header is 'en'
        response = self.client.get(
            f'{url}?q=loc test aut&type=titles',
            format='json',
            headers={'accept-language': 'en'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)[0]
        self.assertEqual(len(content), 3)
        self.assertEqual(content['label'], 'loc test aut')
