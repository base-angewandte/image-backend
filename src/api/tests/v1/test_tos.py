import json

from rest_framework import status

from django.urls import reverse

from .. import APITestCase
from . import VERSION


class TosTests(APITestCase):
    def test_tos_accept(self):
        self.user.tos_accepted = False
        self.user.save()

        url_get = reverse('tos-list', kwargs={'version': VERSION})
        response = self.client.get(url_get, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), dict)
        self.assertEqual(content['tos_accepted'], False)
        self.assertEqual(type(content['tos_text']), str)

        url_post = reverse('tos-accept', kwargs={'version': VERSION})
        response = self.client.post(url_post, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # try once more
        response = self.client.post(url_post, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(url_get, format='json')
        content = json.loads(response.content)

        self.assertEqual(content['tos_accepted'], True)

    def test_permitted_endpoints(self):
        self.user.tos_accepted = False
        self.user.save()

        # routes which should be accessible without accepted ToS
        # excluding tos-list and tos-accepted, which are tested above
        routes_200 = ['api-root', 'user-list']

        # sample (and simple get) routes which should not be accessible without accepted ToS
        routes_403 = [
            'album-list',
            'artwork-list',
            'artwork-labels',
            'folder-list',
            'permission-list',
            'search-filters',
        ]

        for route in routes_200:
            url = reverse(route, kwargs={'version': VERSION})
            response = self.client.get(url, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)

        for route in routes_403:
            url = reverse(route, kwargs={'version': VERSION})
            response = self.client.get(url, format='json')

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # now again with accepted tos
        self.user.tos_accepted = True
        self.user.save()

        for route in routes_403:
            url = reverse(route, kwargs={'version': VERSION})
            response = self.client.get(url, format='json')

            self.assertEqual(response.status_code, status.HTTP_200_OK)
