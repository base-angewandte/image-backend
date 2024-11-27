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

    def test_search_filters(self):
        url = reverse('search-filters', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content, FILTERS)
