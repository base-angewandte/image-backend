import json
from io import BytesIO

from artworks.models import Album, Artwork, Folder
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
    ):  # todo: does not find URL, throws a 401, a 404, or is empty
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
        print(content)
        self.assertEqual(content['total'], 2)
        self.assertEqual(len(content['results']), 2)

    #
    # def test_artworks_retrieve(self): # todo: does not find URL, throws a 401, a 404, or is empty
    #     """Test the retrieval of an artwork."""
    #     artwork = Artwork.objects.create(title="Test Artwork", image_original=temporary_image())
    #     url = reverse('artwork-detail', kwargs={'pk': artwork.pk, 'version': VERSION})
    #     response = self.client.get(url, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     content = json.loads(response.content)
    #     self.assertEqual(content['title'], artwork.title)
    #     self.assertEqual(content['image_original'], 0)
    #     self.assertEqual(content['artists'], [])

    def test_artworks_image(self):
        # TODO
        pass

    def test_artworks_retrieve_albums(self):
        """Test the retrieval of the albums current user has added this artwork
        to."""
        Artwork.objects.create(
            title='Test Artwork', image_original=temporary_image()
        )  # todo why does this show even though it is F checked and published?
        album = Album.objects.create(title='Test Album1', user=self.user)
        url = reverse('album-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['total'], 1)
        self.assertEqual(content['results'][0]['id'], album.id)

    # def test_artworks_download(self):  # todo  Reverse for 'download' not found. 'download' is not a valid view function or pattern name.
    #
    #     """Test the download of an artwork + metadata."""
    #     artwork=Artwork.objects.create(title="Test Artwork", image_original=temporary_image())
    #     url = reverse('download', kwargs={'pk': artwork.pk, 'version': VERSION})
    #
    #     #url = "http://127.0.0.1:8300/api/v1/artworks/1/download/"
    #     print(url)
    #     response = self.client.get(url, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     content = json.loads(response.content)
    #     self.assertEqual(content['total'], 1)
    #     self.assertEqual(content['results'][0]['id'], 1)


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

    # def test_albums_append_artwork(
    #     self,
    # ):  # TODO Reverse for 'append-artwork' not found. 'append-artwork' is not a valid view function or pattern name.
    #     """Test the appending of artworks to album slides."""
    #     album = Album.objects.create(title='Test Album', user=self.user)
    #     artwork = Artwork.objects.create(
    #         title='Test Artwork', image_original=temporary_image()
    #     )
    #     url = reverse('append-artwork', kwargs={'pk': album.pk, 'version': VERSION})
    #     data = {'id': artwork.pk}
    #     response = self.client.put(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_albums_slides(
        self,
    ):  # todo this does not seem enough to test the endpoint, change when you actually update url
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

    # def test_albums_create_slides(self):  # todo url not recognised, try basename + action like above or if it is the same url use the same and use different method
    #     """Test the creation of album slides."""
    #     #url = views.reverse_action('create-slides', kwargs={'version': VERSION})
    #     url = reverse('album-slides', kwargs={'version': VERSION})
    #     data = [[{'id': 1}, {'id': 2}], [{'id': 3}]]
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     content = json.loads(response.content)
    #     self.assertEqual(content, data)


#
#         def test_albums_permissions(self):
#             """Test the retrieval of album permissions."""
#             # todo
#             pass
#
#         def test_albums_create_permissions(self):
#             """Test the creation of album permissions."""
#             # todo
#             pass
#
#         def test_albums_destroy_permissions(self):
#             """Test the deletion of album permissions."""
#             # todo
#             pass
#
#         def test_albums_download(self):
#             """Test the download of an album."""
#             # todo
#             pass


class FoldersTests(APITestCase):  # todo double check
    def test_folders_list(self):
        """Test the retrieval of all albums for a user."""
        first_folder = Folder.objects.create(title='Test Folder', owner=self.user)
        Folder.objects.create(title='Test Folder2', owner=self.user)
        url = reverse('folder-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[1]['title'], first_folder.title)
        # self.assertEqual(content[0]['content'], isinstance(content[0]['content'], dict))

    def test_folder_retrieve(self):
        """Test the retrieval of an album."""
        folder = Folder.objects.create(title='Test Folder', owner=self.user)
        url = reverse('folder-detail', kwargs={'pk': folder.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['title'], folder.title)


# todo continue with Labels, Permissions, Autocomplete?, Search
