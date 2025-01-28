import io
import json
import zipfile

import shortuuid
from rest_framework import status

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from artworks.models import Album, Artwork, PermissionsRelation, Person

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
        self.check_for_nonexistent_object('artwork-detail', 'get', 'Artwork')

    def test_artworks_image(self):
        """Test crop/resize and default image generation."""

        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=True,
        )

        test_cases = [
            {
                'method': 'crop',
                'expected_status': status.HTTP_302_FOUND,
                'expected_suffix': '-crop-c0-5__0-5-30x30-92.jpg',
            },
            {
                'method': 'resize',
                'expected_status': status.HTTP_302_FOUND,
                'expected_suffix': '-thumbnail-30x30-92.jpg',
            },
            {
                'method': 'test',
                'expected_status': status.HTTP_400_BAD_REQUEST,
                'expected_suffix': None,
            },
        ]

        for case in test_cases:
            url = reverse(
                'artwork-image',
                kwargs={
                    'pk': artwork.pk,
                    'height': 30,
                    'width': 30,
                    'method': case['method'],
                    'version': VERSION,
                },
            )
            response = self.client.get(url, format='json')

            self.assertEqual(
                response.status_code,
                case['expected_status'],
            )

            if case['expected_suffix']:
                self.assertIn('Location', response.headers)
                self.assertTrue(
                    response.headers['Location'].endswith(case['expected_suffix']),
                )

        # test retrieving artwork, when artwork does not exist
        self.check_for_nonexistent_object('artwork-detail', 'get', 'Artwork')

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

        # test specific labels
        self.assertEqual(content['title'], _('Title'))
        self.assertEqual(content['keywords'], _('Keywords'))
        self.assertEqual(content['comments'], _('Comments'))
        self.assertEqual(
            content['material_description'],
            _('Material/Technique description'),
        )
        self.assertEqual(content['license'], Artwork.get_license_label())
        self.assertEqual(content['comments_de'], _('Comments (DE)'))
        self.assertEqual(content['comments_en'], _('Comments (EN)'))
        self.assertEqual(
            content['material_description_de'],
            _('Material/Technique description (DE)'),
        )
        self.assertEqual(
            content['material_description_en'],
            _('Material/Technique description (EN)'),
        )

        # test that excluded fields are not present
        excluded_fields = [
            'id',
            'archive_id',
            'checked',
            'published',
            'date_created',
            'date_changed',
            'search_persons',
            'search_locations',
            'search_keywords',
            'search_materials',
            'search_vector',
        ]
        for field in excluded_fields:
            self.assertNotIn(field, content)

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

        # Create another test artwork and albums
        aw1 = Artwork.objects.create(
            title='Test Artwork 1',
            image_original=temporary_image(),
            published=True,
        )

        lecturer_album = Album.objects.create(
            title='Test Album2',
            user=get_user_model().objects.get(username='p0001234'),
            slides=[
                {
                    'id': shortuuid.uuid(),
                    'items': [{'id': aw1.pk}],
                },
            ],
        )
        user_album = Album.objects.create(title='Test Album3', user=self.user)

        # in order for the self.user to append the artwork to the album,
        # we need to provide them with an EDIT permission.
        # After the artwork is appended to the lecturer's album, we remove the PermissionsRelation
        PermissionsRelation.objects.create(
            user=self.user,
            album=lecturer_album,
            permissions='EDIT',
        )

        # append the artwork to lecturer's album
        url_post_lecturer = reverse(
            'album-append-artwork',
            kwargs={'pk': lecturer_album.pk, 'version': VERSION},
        )
        data = {'id': aw1.pk}
        response = self.client.post(url_post_lecturer, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # append the artwork to self.user's album
        url = reverse(
            'album-append-artwork',
            kwargs={'pk': user_album.pk, 'version': VERSION},
        )
        data = {'id': aw1.pk}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # test retrieval of albums that contain the artwork
        url = reverse(
            'artwork-retrieve-albums',
            kwargs={'pk': aw1.pk, 'version': VERSION},
        )
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.json()
        self.assertEqual(len(content), 2)

        # test retrieval with 'permissions=EDIT'
        response = self.client.get(f'{url}?permissions=EDIT', format='json')
        content = json.loads(response.content)

        # test that lecturer's album is retrieved where the self.user has an EDIT permission set
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # both albums are retrieved (as the self.user per default has EDIT permissions on own album)
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0]['title'], 'Test Album2')

        # remove the permission to show that only owned album is retrieved
        # (because when EDIT is set, self.user has owner rights)
        PermissionsRelation.objects.filter(
            user=self.user,
            album=lecturer_album,
            permissions='EDIT',
        ).delete()

        # test retrieval with 'owner=true'
        response = self.client.get(f'{url}?owner=true', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.json()
        self.assertEqual(len(content), 1)

        # test retrieving artwork, when artwork does not exist
        self.check_for_nonexistent_object('artwork-detail', 'get', 'Artwork')

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

        # test apply_strikethrough functionality to a string
        discriminatory_terms = ['discrimination']
        title_with_dt = 'This is a discrimination example.'
        for term in discriminatory_terms:
            if term in title_with_dt:
                strikethrough_term = term[0] + ''.join(
                    [char + '\u0336' for char in term[1:]],
                )
                title_with_dt = title_with_dt.replace(term, strikethrough_term)
        expected_result = 'This is a di\u0336s\u0336c\u0336r\u0336i\u0336m\u0336i\u0336n\u0336a\u0336t\u0336i\u0336o\u0336n\u0336 example.'
        self.assertEqual(title_with_dt, expected_result)

        # test retrieving artwork, when artwork does not exist
        self.check_for_nonexistent_object('artwork-detail', 'get', 'Artwork')
