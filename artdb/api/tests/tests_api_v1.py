import json

from artworks.models import Album, Artwork, Folder
from rest_framework import status

from django.urls import reverse

from . import APITestCase

VERSION = 'v1'


class ArtworkTests(APITestCase):
    def test_artworks_list(self):
        """Test the retrieval of all artworks for a user."""
        Artwork.objects.create(title='Test Artwork1', material='wood')
        Artwork.objects.create(title='Test Artwork2')
        url = reverse('artwork-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 2)
        self.assertEqual(len(content['results']), 2)

    def test_artworks_retrieve(self):
        """Test the retrieval of an artwork."""
        artwork = Artwork.objects.create(title='Test Artwork')
        url = reverse('artwork-detail', kwargs={'pk': artwork.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], artwork.title)
        self.assertEqual(content['image_original'], 0)
        self.assertEqual(content['artists'], [])

    def test_artworks_image(self):
        """Test the retrieval of the albums current user has added this artwork
        to."""
        # todo, should we implement this, and therefore actions as well?
        pass

    def test_artworks_retrieve_albums(self):
        """Test the retrieval of the albums current user has added this artwork
        to."""
        # todo, should we implement this, and therefore actions as well?
        pass

    def test_artworks_download(self):
        """Test the download of an artwork + metadata."""
        # todo, should we implement this, and therefore actions as well?
        pass


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
            # todo
            url = reverse('album-list', kwargs={'version': VERSION})
            data = {'title': 'Test Album', 'pk': 3}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(Album.objects.count(), 1)
            self.assertEqual(Album.objects.get().title, data['title'])

        def test_albums_destroy(self):
            """Test the deletion of an album."""
            # todo
            pass

        def test_albums_append_artwork(self):
            """Test the appending of artworks to album slides."""
            # todo
            pass

        def test_albums_slides(self):
            """Test the retrieval of album slides."""
            # todo
            pass

        def test_albums_create_slides(self):
            """Test the creation of album slides."""
            # todo
            pass

        def test_albums_permissions(self):
            """Test the retrieval of album permissions."""
            # todo
            pass

        def test_albums_create_permissions(self):
            """Test the creation of album permissions."""
            # todo
            pass

        def test_albums_destroy_permissions(self):
            """Test the deletion of album permissions."""
            # todo
            pass

        def test_albums_download(self):
            """Test the download of an album."""
            # todo
            pass


class FoldersTests(APITestCase):
    def test_folders_list(self):
        """Test the retrieval of all albums for a user."""
        Folder.objects.create(title='Test Folder', owner=self.user)
        Folder.objects.create(title='Test Folder2', owner=self.user)
        url = reverse('folder-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        print(content)
        self.assertEqual(content['total'], 2)
        self.assertEqual(len(content['results']), 2)

    def test_folder_retrieve(self):
        """Test the retrieval of an album."""
        folder = Folder.objects.create(title='Test Folder', owner=self.user)
        url = reverse('album-detail', kwargs={'pk': folder.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], folder.title)


# todo continue with Labels, Permissions
