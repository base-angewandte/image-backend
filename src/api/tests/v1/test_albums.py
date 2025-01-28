import json

import shortuuid
from rest_framework import status

from django.contrib.auth import get_user_model
from django.urls import reverse

from artworks.models import (
    Album,
    Artwork,
    PermissionsRelation,
)

from .. import APITestCase, temporary_image
from . import VERSION

User = get_user_model()


class AlbumsTests(APITestCase):
    def test_albums_list(self):
        """Test the retrieval of all albums for a user."""

        Album.objects.create(title='Test Album1', user=self.user)
        Album.objects.create(title='Test Album2', user=self.user)

        url = reverse('album-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        num_results = 6
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
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['title'], album.title)
        self.assertEqual(content['number_of_artworks'], 0)
        self.assertEqual(content['slides'], [])
        self.assertEqual(content['owner']['id'], self.user.username)
        self.assertEqual(content['permissions'], [])

        # test retrieving non-existent album
        self.check_for_nonexistent_object(
            view_name='album-detail',
            http_method='get',
            object_type='Album',
        )

    def test_albums_update(self):
        """Test the updating of an album."""

        album = Album.objects.create(title='Test Album', user=self.user)

        url = reverse('album-detail', kwargs={'pk': album.pk, 'version': VERSION})
        data = {'title': 'Test Album'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test updating non-existing album
        self.check_for_nonexistent_object(
            view_name='album-detail',
            http_method='put',
            object_type='Album',
            data=data,
        )

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

        # test destroying non-existing album
        self.check_for_nonexistent_object(
            view_name='album-detail',
            http_method='delete',
            object_type='Album',
        )

    def test_albums_append_artwork(self):
        """Test the appending of artworks to album slides."""

        album = Album.objects.create(title='Test Album', user=self.user)
        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=True,
        )
        artwork2 = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=False,
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

        # try appending unpublished artwork
        data = {'id': artwork2.pk}
        response = self.client.post(url_post, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content['detail'], 'Artwork does not exist')

        # test appending non-existent album
        self.check_for_nonexistent_object(
            view_name='album-append-artwork',
            http_method='post',
            object_type='Album',
            data=data,
        )

    def test_albums_slides(self):
        """Test the retrieval of album slides."""

        id1 = shortuuid.uuid()
        id2 = shortuuid.uuid()

        album = Album.objects.create(
            title='Test Album',
            user=self.user,
            slides=[
                {'id': id1, 'items': [{'id': 1}, {'id': 2}]},
                {'id': id2, 'items': [{'id': 3}]},
            ],
        )

        url = reverse('album-slides', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        slides = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(slides), list)
        self.assertEqual(len(slides), 2)
        self.assertEqual(slides[0]['id'], id1)
        self.assertEqual(slides[1]['id'], id2)
        self.assertEqual(len(slides[0]['items']), 2)
        self.assertEqual(len(slides[1]['items']), 1)
        self.assertEqual(slides[0]['items'][0]['id'], 1)
        self.assertEqual(slides[0]['items'][1]['id'], 2)
        self.assertEqual(slides[1]['items'][0]['id'], 3)

        # test retrieval of a slide of non-existing album
        self.check_for_nonexistent_object(
            view_name='album-slides',
            http_method='get',
            object_type='Album',
        )

        # test slide with details retrieval
        url = reverse('album-slides', kwargs={'pk': self.album4.pk, 'version': VERSION})
        response = self.client.get(f'{url}?details=true', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test existence and correct content of slide
        self.assertEqual(len(content[0]['items']), 1)
        self.assertIn('id', content[0])
        self.assertEqual(content[0]['items'][0]['title'], 'Homometer II')
        self.assertEqual(content[0]['items'][0]['date'], '1976')
        self.assertEqual(content[0]['items'][0]['artists'][0]['value'], 'VALIE EXPORT')

    def test_albums_create_slides(self):
        """Test the creation of album slides."""

        album = Album.objects.create(title='Test Album', user=self.user)

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
        artwork3 = Artwork.objects.create(
            title='Test Artwork 3',
            image_original=temporary_image(),
            published=True,
        )
        artwork4 = Artwork.objects.create(
            title='Test Artwork 4',
            image_original=temporary_image(),
            published=False,
        )

        url = reverse('album-slides', kwargs={'pk': album.pk, 'version': VERSION})
        data = [
            {'items': [{'id': artwork1.pk}, {'id': artwork2.pk}]},
            {'items': [{'id': artwork3.pk}]},
        ]
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

        # test creating slide with unpublished artwork:
        data = [
            {'items': [{'id': artwork4.pk}]},
        ]
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content['detail'], 'Artwork does not exist')

        # test creating slides with non-existent album
        self.check_for_nonexistent_object(
            view_name='album-slides',
            http_method='post',
            object_type='Album',
            data=data,
        )

        # test slide with details retrieval
        url = reverse('album-slides', kwargs={'pk': self.album4.pk, 'version': VERSION})
        response = self.client.get(f'{url}?details=true', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test existence and correct content of slide
        self.assertEqual(len(content[0]['items']), 1)
        self.assertIn('id', content[0])
        self.assertEqual(content[0]['items'][0]['title'], 'Homometer II')
        self.assertEqual(content[0]['items'][0]['date'], '1976')
        self.assertEqual(content[0]['items'][0]['artists'][0]['value'], 'VALIE EXPORT')

    def test_albums_permissions(self):
        """Test the retrieval of album permissions."""

        album = Album.objects.create(title='Test Album', user=self.user)
        user = User.objects.create(username='abc1def2')
        PermissionsRelation.objects.create(album=album, user=user)
        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content[0]['user']['id'], user.username)
        self.assertEqual(content[0]['permissions'][0]['id'], 'VIEW')

        # test retrieving album permissions of non-existent album
        self.check_for_nonexistent_object(
            view_name='album-permissions',
            http_method='get',
            object_type='Album',
        )

        # test if the user is not the owner of the album, only return the permissions of this user
        lecturer = get_user_model().objects.get(username='p0001234')
        foreign_album = Album.objects.create(title='Foreign Album', user=lecturer)

        # provide permissions to self.user on lecturer's album
        PermissionsRelation.objects.create(
            user=self.user,
            album=foreign_album,
            permissions='VIEW',
        )

        url = reverse(
            'album-permissions',
            kwargs={'pk': foreign_album.pk, 'version': VERSION},
        )
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content[0]['user']['id'], self.user.username)
        self.assertEqual(content[0]['permissions'][0]['id'], 'VIEW')

    def test_albums_create_permissions(self):
        """Test the creation of album permissions."""

        album = Album.objects.create(title='Test Album', user=self.user)
        new_user = User.objects.create(username='abc1def2')

        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        data = [{'user': f'{new_user.username}', 'permissions': [{'id': 'VIEW'}]}]
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content[0]['permissions'][0]['id'], 'VIEW')
        self.assertEqual(content[0]['user']['id'], new_user.username)

        # test permission assignment when user is already the owner of the album
        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        data = [{'user': f'{self.user.username}', 'permissions': [{'id': 'VIEW'}]}]
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content['detail'], 'User is already the owner of album.')

        # test permission assignment when user does not exist
        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        data = [{'user': 'user-does-not-exist-test', 'permissions': [{'id': 'VIEW'}]}]
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content['detail'], 'User does not exist')

    def test_albums_destroy_permissions(self):
        """Test the deletion of album permissions."""

        album = Album.objects.create(title='Test Album', user=self.user)

        url = reverse('album-permissions', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # test destroying album permissions of non-existing album
        self.check_for_nonexistent_object(
            view_name='album-permissions',
            http_method='delete',
            object_type='Album',
        )

        # test deleting all permissions on an album,
        # when the user is not the owner and gets only their permissions removed
        other_user = get_user_model().objects.get(username='p0001234')
        other_user_album = Album.objects.create(title='Foreign Album', user=other_user)

        # provide permissions to self.user on owner's album
        PermissionsRelation.objects.create(
            user=self.user,
            album=other_user_album,
            permissions='EDIT',
        )
        # assert existence of the permission
        self.assertTrue(
            PermissionsRelation.objects.filter(
                user=self.user,
                album=other_user_album,
            ).exists(),
        )

        # perform the DELETE request
        url = reverse(
            'album-permissions',
            kwargs={'pk': other_user_album.pk, 'version': VERSION},
        )
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert non-existence of the permission
        self.assertFalse(
            PermissionsRelation.objects.filter(
                user=self.user,
                album=other_user_album,
            ).exists(),
        )

        # test that the album itself still exists after deletion of permissions for self.user
        album = Album.objects.get(pk=other_user_album.pk)
        self.assertTrue(
            Album.objects.filter(pk=album.pk).exists(),
        )

    def test_albums_download(self):
        """Test the download of an album."""

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
        artwork3 = Artwork.objects.create(
            title='Test Artwork 3',
            image_original=temporary_image(),
            published=True,
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

        # test album pdf download
        url = reverse('album-download', kwargs={'pk': album.pk, 'version': VERSION})
        response = self.client.get(f'{url}?download_format=pdf', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # assert the content type is a PDF
        self.assertEqual(
            response.headers['Content-Type'],
            'application/pdf',
        )

        # test downloading non-existing album
        self.check_for_nonexistent_object(
            view_name='album-download',
            http_method='get',
            object_type='Album',
        )
