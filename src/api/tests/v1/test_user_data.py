import json

from rest_framework import status

from django.urls import reverse

from .. import APITestCase
from . import VERSION


class UserDataTests(APITestCase):
    def test_user_data(self):
        """Test the retrieval of current user data."""

        url = reverse('user-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['id'], 'temporary')
        self.assertEqual(content['email'], 'temporary@uni-ak.ac.at')

    def test_user_preferences(self):
        """Test retrieving and setting user preferences."""

        def check_get_user(images, folders):
            """Sends a GET request to /user/ and tests the result."""

            u = reverse('user-list', kwargs={'version': VERSION})
            r = self.client.get(u, format='json')
            c = json.loads(r.content)

            self.assertEqual(r.status_code, status.HTTP_200_OK)
            self.assertEqual(type(c['preferences']), dict)
            self.assertEqual(c['preferences']['display_images'], images)
            self.assertEqual(c['preferences']['display_folders'], folders)

        def check_get_preferences(images, folders):
            """Sends a GET request to /user/preferences/ and tests the
            result."""

            u = reverse('user-preferences', kwargs={'version': VERSION})
            r = self.client.get(u, format='json')
            c = json.loads(r.content)

            self.assertEqual(r.status_code, status.HTTP_200_OK)
            self.assertEqual(type(c), dict)
            self.assertEqual(c['display_images'], images)
            self.assertEqual(c['display_folders'], folders)

        # check the default response from /user/ and /user/prefereces/ endpoint
        check_get_user('crop', 'list')
        check_get_preferences('crop', 'list')

        # change and check both preferences through POST to /user/preferences/
        url = reverse('user-preferences', kwargs={'version': VERSION})
        data = {'display_images': 'resize', 'display_folders': 'grid'}
        response = self.client.post(url, data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), dict)
        self.assertEqual(content['display_images'], 'resize')
        self.assertEqual(content['display_folders'], 'grid')
        check_get_preferences('resize', 'grid')
        check_get_user('resize', 'grid')

        # change and check one option at a time through PATCH to /user/preferences/
        response = self.client.patch(url, {'display_images': 'crop'}, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), dict)
        self.assertEqual(content['display_images'], 'crop')

        response = self.client.patch(url, {'display_folders': 'list'}, format='json')
        content = json.loads(response.content)

        self.assertEqual(content['display_folders'], 'list')
        check_get_preferences('crop', 'list')

    def test_user_preferences_parameters(self):
        """Test for the validity of POST/PATCH request parameters."""

        url = reverse('user-preferences', kwargs={'version': VERSION})
        response = self.client.patch(url, {'display_folders': 'abc'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'display_images': 'abc', 'display_folders': 'grid'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(url, {'display_folders': 'grid'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
