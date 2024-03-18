import json

from artworks.models import Album
from rest_framework import status

from django.urls import reverse

from . import APITestCase

VERSION = 'v1'


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
