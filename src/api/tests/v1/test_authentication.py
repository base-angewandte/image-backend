from rest_framework import status
from rest_framework.test import APITestCase

from django.urls import reverse

from . import VERSION


class AuthenticationTestCase(APITestCase):
    def test_unauthorized_requests(self):
        # check that all urls return 401 for unauthenticated users
        urls = [
            reverse('artwork-list', kwargs={'version': VERSION}),
            reverse('artwork-detail', kwargs={'pk': 1, 'version': VERSION}),
            reverse(
                'artwork-image',
                kwargs={
                    'pk': 1,
                    'height': 30,
                    'width': 30,
                    'method': 'crop',
                    'version': VERSION,
                },
            ),
            reverse('artwork-download', kwargs={'pk': 1, 'version': VERSION}),
            reverse('artwork-labels', kwargs={'version': VERSION}),
            reverse('album-list', kwargs={'version': VERSION}),
            reverse('album-detail', kwargs={'pk': 1, 'version': VERSION}),
            reverse(
                'album-append-artwork',
                kwargs={'pk': 1, 'version': VERSION},
            ),
            reverse('album-slides', kwargs={'pk': 1, 'version': VERSION}),
            reverse('album-permissions', kwargs={'pk': 1, 'version': VERSION}),
            reverse('album-download', kwargs={'pk': 1, 'version': VERSION}),
            reverse('folder-list', kwargs={'version': VERSION}),
            reverse('folder-detail', kwargs={'pk': 1, 'version': VERSION}),
            reverse('permission-list', kwargs={'version': VERSION}),
            reverse('search', kwargs={'version': VERSION}),
            reverse('search-filters', kwargs={'version': VERSION}),
            reverse('tos-list', kwargs={'version': VERSION}),
            reverse('tos-accept', kwargs={'version': VERSION}),
            reverse('user-list', kwargs={'version': VERSION}),
            reverse('user-preferences', kwargs={'version': VERSION}),
            reverse('autocomplete', kwargs={'version': VERSION}),
        ]
        for url in urls:
            for method in ['get', 'post', 'put', 'patch', 'delete']:
                response = getattr(self.client, method)(url, format='json')
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
