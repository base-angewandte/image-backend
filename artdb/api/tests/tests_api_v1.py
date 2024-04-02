import json
from io import BytesIO

from artworks.models import Album, Artist, Artwork, Folder, PermissionsRelation, User
from PIL import Image
from rest_framework import status

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from . import APITestCase

VERSION = 'v1'


def temporary_image():  # from https://stackoverflow.com/a/67611074
    bts = BytesIO()
    img = Image.new('RGB', (100, 100))
    img.save(bts, 'jpeg')
    return SimpleUploadedFile('test.jpg', bts.getvalue())


class ArtworkTests(APITestCase):
    def test_artworks_list(
        self,
    ):
        """Test the retrieval of all artworks for a user."""
        Artwork.objects.create(
            title='Test Artwork 1',
            image_original=temporary_image(),
            checked=True,
            published=True,
        )
        Artwork.objects.create(
            title='Test Artwork 2',
            image_original=temporary_image(),
            checked=True,
            published=True,
        )
        url = reverse('artwork-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 2)
        self.assertEqual(len(content['results']), 2)

    def test_artworks_retrieve(self):
        """Test the retrieval of an artwork."""
        artwork = Artwork.objects.create(
            title='Test Artwork', image_original=temporary_image(), published=True
        )
        url = reverse('artwork-detail', kwargs={'pk': artwork.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], artwork.title)
        self.assertEqual(
            content['image_original'], f'http://testserver{artwork.image_original.url}'
        )
        self.assertEqual(content['artists'], [])

    def test_artworks_image(self):
        artwork = Artwork.objects.create(
            title='Test Artwork', image_original=temporary_image(), published=True
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

    def test_artworks_retrieve_albums(self):
        """Test the retrieval of the albums current user has added this artwork
        to."""
        Artwork.objects.create(title='Test Artwork', image_original=temporary_image())
        album = Album.objects.create(title='Test Album1', user=self.user)
        url = reverse('album-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 1)
        self.assertEqual(content['results'][0]['id'], album.id)

    def test_artworks_download(self):
        """Test the download of an artwork + metadata."""
        artwork = Artwork.objects.create(
            title='Test Artwork', image_original=temporary_image(), published=True
        )
        artist = Artist.objects.create(name='TestArtist')
        artwork.artists.add(artist)
        url = reverse('artwork-download', kwargs={'pk': artwork.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AlbumsTests(APITestCase):
    def test_albums_list(self):
        """Test the retrieval of all albums for a user."""
        Album.objects.create(title='Test Album1', user=self.user)
        Album.objects.create(title='Test Album2', user=self.user)
        url = reverse('album-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 2)
        self.assertEqual(len(content['results']), 2)

    def test_albums_create(self):
        """Test the creation of a new album."""
        url = reverse('album-list', kwargs={'version': VERSION})
        data = {'title': 'Test Album'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Album.objects.count(), 1)
        self.assertEqual(Album.objects.get().title, data['title'])

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
        self.assertEqual(Album.objects.count(), 1)
        self.assertEqual(Album.objects.get().title, data['title'])

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
            title='Test Artwork', image_original=temporary_image()
        )
        url = reverse(
            'album-append-artwork', kwargs={'pk': album.pk, 'version': VERSION}
        )
        data = {'id': artwork.pk}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_albums_slides(self):
        """Test the retrieval of album slides."""
        album = Album.objects.create(title='Test Album', user=self.user)
        album.slides = [[{'id': 1}, {'id': 2}], [{'id': 3}]]
        album.save()
        url = reverse('album-slides', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0][0].get('id'), 1)

    def test_albums_create_slides(self):
        """Test the creation of album slides."""
        album = Album.objects.create(title='Test Album', user=self.user)
        artwork1 = Artwork.objects.create(
            title='Test Artwork 1', image_original=temporary_image()
        )
        artwork2 = Artwork.objects.create(
            title='Test Artwork 2', image_original=temporary_image()
        )
        artwork3 = Artwork.objects.create(
            title='Test Artwork 3', image_original=temporary_image()
        )
        url = reverse('album-slides', kwargs={'pk': album.pk, 'version': VERSION})
        data = [[{'id': artwork1.pk}, {'id': artwork2.pk}], [{'id': artwork3.pk}]]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content, data)

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
        album = Album.objects.create(title='Test Album', user=self.user)
        url = reverse('album-download', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(response.content), bytes)


class FoldersTests(APITestCase):
    def test_folders_list(self):
        """Test the retrieval of all albums for a user."""
        folder1 = Folder.objects.create(title='Test Folder', owner=self.user)
        folder2 = Folder.objects.create(title='Test Folder2', owner=self.user)
        url = reverse('folder-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[1]['title'], folder1.title)
        self.assertEqual(content[1]['id'], folder1.id)
        self.assertEqual(content[0]['title'], folder2.title)
        self.assertEqual(content[0]['id'], folder2.id)

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


class LabelsTests(APITestCase):
    def test_labels_list(self):
        """Test the retrieval of labels."""
        Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            checked=True,
            published=True,
        )
        url = reverse('label-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], 'Titel')
        self.assertEqual(content['keywords'], 'Schlagworte')


class PermissionsTests(APITestCase):
    def test_labels_list(self):
        """Test the retrieval of permissions."""
        url = reverse('permission-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content[0]['id'], 'VIEW')
        self.assertEqual(content[1]['label'], 'EDIT')


class SearchTests(APITestCase):
    def test_search(self):
        """Test the search."""
        # Todo (possible): extend? as there are several usecases
        artist = Artist.objects.create(name='TestArtist')
        artwork1 = Artwork.objects.create(
            title='Test Artwork 1', image_original=temporary_image(), published=True
        )
        artwork2 = Artwork.objects.create(
            title='Test Artwork 2', image_original=temporary_image(), published=True
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
                }
            ],
        }
        url = reverse('search', kwargs={'version': VERSION})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 2)
        self.assertEqual(content['results'][0]['title'], artwork1.title)
        self.assertEqual(content['results'][1]['artists'][0]['value'], artist.name)

    def test_search_labels_list(self):
        url = reverse('search-filters', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title']['type'], 'array')
        self.assertEqual(len(content['place_of_production']['items']), 2)


class UserDataTests(APITestCase):
    def test_user_data(self):
        """Test the retrieval of current user data."""
        url = reverse('user', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['id'], 'temporary')
        self.assertEqual(content['email'], 'temporary@uni-ak.ac.at')


# todo continue with Autocomplete


class AutocompleteTests(APITestCase):
    # todo
    pass
