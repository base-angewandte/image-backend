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

        # test searching when offset higher then total
        data = {
            'limit': 15,
            'offset': 15,
            'exclude': [],
            'q': 'test',
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 14)
        self.assertEqual(len(content['results']), 0)

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

    def test_search_returns_roles_in_preview(self):
        """Test search for roles in preview."""

        author_only = Person.objects.create(name='TestAuthor')
        photographer_only = Person.objects.create(name='TestPhotographer')
        both_roles = Person.objects.create(name='TestBothRoles')
        unrelated = Person.objects.create(name='UnrelatedPerson')

        aw_author = Artwork.objects.create(
            title='Author Only Artwork',
            image_original=temporary_image(),
            published=True,
        )
        aw_author.authors.add(author_only)
        aw_author.save()

        aw_photographer = Artwork.objects.create(
            title='Photographer Only Artwork',
            image_original=temporary_image(),
            published=True,
        )
        aw_photographer.photographers.add(photographer_only)
        aw_photographer.save()

        aw_both = Artwork.objects.create(
            title='Both Roles Artwork',
            image_original=temporary_image(),
            published=True,
        )
        aw_both.authors.add(both_roles)
        aw_both.photographers.add(both_roles)
        aw_both.save()

        aw_mixed = Artwork.objects.create(
            title='Mixed Roles Artwork',
            image_original=temporary_image(),
            published=True,
        )
        aw_mixed.authors.add(author_only)
        aw_mixed.photographers.add(photographer_only)
        aw_mixed.artists.add(unrelated)
        aw_mixed.save()

        url = reverse('search-list', kwargs={'version': VERSION})

        # test author search returns author-only artwork and mixed artwork
        data = {
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': ['author'],
                },
            ],
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 2)

        titles = {r['title'] for r in content['results']}
        self.assertIn('Author Only Artwork', titles)
        self.assertIn('Mixed Roles Artwork', titles)
        self.assertNotIn('Photographer Only Artwork', titles)
        self.assertNotIn('Both Roles Artwork', titles)

        # test payload contract (role keys exist even if empty)
        for result in content['results']:
            self.assertIn('artists', result)
            self.assertIn('authors', result)
            self.assertIn('photographers', result)
            self.assertIn('graphic_designers', result)

        # test existing field artist stays empty for author-only results
        author_only_result = next(
            r for r in content['results'] if r['title'] == 'Author Only Artwork'
        )
        self.assertEqual(author_only_result['artists'], [])
        self.assertEqual(author_only_result['authors'][0]['value'], author_only.name)
        self.assertEqual(author_only_result['photographers'], [])
        self.assertEqual(author_only_result['graphic_designers'], [])

        # test if user is an author, search for photographer,but the user isn't a photographer
        data = {
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': ['author'],
                },
            ],
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)
        self.assertNotIn(
            'Photographer Only Artwork',
            {r['title'] for r in content['results']},
        )

        # test with second user, only one of the two matches the criteria
        data = {
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': ['unrelated'],
                },
            ],
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 1)
        self.assertEqual(content['results'][0]['title'], 'Mixed Roles Artwork')

        # test photographer-only + mixed
        data = {
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': ['photographer'],
                },
            ],
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 2)

        titles = {r['title'] for r in content['results']}
        self.assertIn('Photographer Only Artwork', titles)
        self.assertIn('Mixed Roles Artwork', titles)
        self.assertNotIn('Author Only Artwork', titles)
        self.assertNotIn('Both Roles Artwork', titles)

        # test person is author and photographer
        data = {
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': ['bothroles'],
                },
            ],
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 1)
        self.assertEqual(content['results'][0]['title'], 'Both Roles Artwork')
        self.assertEqual(content['results'][0]['artists'], [])
        self.assertEqual(content['results'][0]['authors'][0]['value'], both_roles.name)
        self.assertEqual(
            content['results'][0]['photographers'][0]['value'],
            both_roles.name,
        )
        self.assertIn('graphic_designers', content['results'][0])
        self.assertEqual(content['results'][0]['graphic_designers'], [])

        # test search by id
        data = {
            'filters': [
                {
                    'id': 'artists',
                    'filter_values': [{'id': author_only.id}],
                },
            ],
        }
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['total'], 2)
        titles = {r['title'] for r in content['results']}
        self.assertIn('Author Only Artwork', titles)
        self.assertIn('Mixed Roles Artwork', titles)
