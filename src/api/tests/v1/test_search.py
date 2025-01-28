import json

from rest_framework import status

from django.urls import reverse

from artworks.models import (
    Artwork,
    Location,
    Person,
)

from ...search.filters import FILTERS
from .. import APITestCase, temporary_image
from . import VERSION


class SearchTests(APITestCase):
    def test_search(self):
        """Test the search."""
        # TODO extend with further use cases

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

        url = reverse('search-list', kwargs={'version': VERSION})
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
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 2)
        self.assertEqual(content['results'][0]['title'], artwork2.title)
        self.assertEqual(content['results'][1]['artists'][0]['value'], artist.name)

        # test searching with artist id
        data = {
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': [{'id': artist.id}],
                },
            ],
        }
        response = self.client.post(
            url,
            data,
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 2)
        self.assertEqual(content['results'][0]['title'], artwork1.title)
        self.assertEqual(content['results'][1]['artists'][0]['value'], artist.name)

    def test_search_location(self):
        """Test search for locations, place of production."""

        url = reverse('search-list', kwargs={'version': VERSION})
        data = {
            'filters': [
                {
                    'id': 'location',
                    'filter_values': ['Eisenkappel'],
                },
            ],
        }
        response = self.client.post(
            url,
            data,
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            content['results'][0]['title'],
            'loc test zelez',
        )

        # test search for place of production
        location = Location.objects.get(name='Bad Eisenkappel')
        aw1 = Artwork.objects.create(
            title='Place of Production Test Artwork',
            image_original=temporary_image(),
            published=True,
        )
        aw1.place_of_production.set([location])
        data = {
            'filters': [
                {
                    'id': 'place_of_production',
                    'filter_values': ['Eisenkappel'],
                },
            ],
        }
        response = self.client.post(
            url,
            data,
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            content['results'][0]['title'],
            'Place of Production Test Artwork',
        )

    def test_search_keyword(self):
        """Test search for keywords."""

        url = reverse('search-list', kwargs={'version': VERSION})
        data = {
            'filters': [
                {
                    'id': 'keywords',
                    'filter_values': ['Architektur'],
                },
            ],
        }
        response = self.client.post(
            url,
            data,
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            content['results'][0]['title'],
            'kw test arch + profan',
        )

    def test_search_title(self):
        """Test search for titles."""

        url = reverse('search-list', kwargs={'version': VERSION})
        data = {
            'filters': [
                {
                    'id': 'title',
                    'filter_values': ['Lucretia'],
                },
            ],
        }
        response = self.client.post(
            url,
            data,
            format='json',
        )
        content = json.loads(response.content)

        # test searching with title de
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            content['results'][0]['title'],
            'Lucretia',
        )

        # test searching with id
        aw1 = Artwork.objects.create(
            title='Test title id 1',
            image_original=temporary_image(),
            published=True,
        )
        data = {
            'filters': [
                {
                    'id': 'title',
                    'filter_values': [{'id': aw1.id}],
                },
            ],
        }
        response = self.client.post(
            url,
            data,
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            content['results'][0]['title'],
            'Test title id 1',
        )

    def test_search_date(self):
        """Test search for dates."""
        url = reverse('search-list', kwargs={'version': VERSION})

        # Initialize base data structure with "id": "date"
        data = {
            'filters': [
                {
                    'id': 'date',
                    'filter_values': {},
                },
            ],
        }

        # test missing filter values
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            content['detail'],
            'Invalid filter_value format for date filter.',
        )

        # test date search with correct date_from, date_to provided
        data['filters'][0]['filter_values'] = {
            'date_from': '1642',
            'date_to': '1643',
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 1)
        self.assertEqual(content['results'][0]['date'], '1642/1643')

        # test invalid format of date_from and date_to (non-integer strings)
        data['filters'][0]['filter_values'] = {
            'date_from': 'A',
            'date_to': 'B',
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            content['detail'],
            'Invalid format of at least one filter_value for date filter.',
        )

        # test with float date values
        data['filters'][0]['filter_values'] = {
            'date_from': '2000.5',
            'date_to': '2010.5',
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            content['detail'],
            'Invalid format of at least one filter_value for date filter.',
        )

        # test when date_from is greater than date_to
        data['filters'][0]['filter_values'] = {
            'date_from': '2025',
            'date_to': '2020',
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            content['detail'],
            'date_from needs to be less than or equal to date_to.',
        )

    def test_search_filters(self):
        url = reverse('search-filters', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, FILTERS)
