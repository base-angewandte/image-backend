import json

from rest_framework import status

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .. import APITestCase
from . import VERSION


class PermissionsTests(APITestCase):
    def test_labels_list(self):
        """Test the retrieval of permissions."""

        url = reverse('permission-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content[0]['id'], 'VIEW')
        self.assertEqual(content[0]['label'], _('VIEW'))
        self.assertEqual(content[1]['id'], 'EDIT')
        self.assertEqual(content[1]['label'], _('EDIT'))
