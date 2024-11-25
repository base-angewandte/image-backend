import io
import json
import zipfile

from rest_framework import status

from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from artworks.models import Album, Artwork, Person

from .. import APITestCase, temporary_image
from . import VERSION


class ArtworkTests(APITestCase):
    def test_artworks_list(
        self,
    ):
        """Test the retrieval of all artworks for a user."""

        url = reverse('artwork-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

        # test retrieving artwork, when artwork does not exist
        self.artwork_does_not_exist('artwork-detail', 'get', 'Artwork')

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

        # test retrieving artwork, when artwork does not exist
        self.artwork_does_not_exist('artwork-detail', 'get', 'Artwork')

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
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['title'], _('Title'))
        self.assertEqual(content['keywords'], _('Keywords'))

    def test_artworks_retrieve_albums(self):
        """Test the retrieval of the albums current user has added this artwork
        to."""

        Artwork.objects.create(title='Test Artwork', image_original=temporary_image())
        album = Album.objects.create(title='Test Album1', user=self.user)

        url = reverse('album-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 4)
        self.assertEqual(content['results'][3]['id'], album.id)

        # test retrieving artwork, when artwork does not exist
        self.artwork_does_not_exist('artwork-detail', 'get', 'Artwork')

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

        # test retrieving artwork, when artwork does not exist
        self.artwork_does_not_exist('artwork-detail', 'get', 'Artwork')
