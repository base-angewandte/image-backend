import json

from rest_framework import status

from django.urls import reverse

from artworks.models import Folder

from .. import APITestCase
from . import VERSION


class FoldersTests(APITestCase):
    def test_folders_list(self):
        """Test the retrieval of all albums for a user."""

        folder1 = Folder.objects.create(title='Test Folder', owner=self.user)
        folder2 = Folder.objects.create(title='Test Folder2', owner=self.user)
        Folder.objects.create(title='Test Folder3', owner=self.user)
        Folder.objects.create(title='Test Folder4', owner=self.user)

        url = reverse('folder-list', kwargs={'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        num_results = 4

        self.assertEqual(len(content), num_results)
        self.assertEqual(content[0]['title'], folder1.title)
        self.assertEqual(content[0]['id'], folder1.id)
        self.assertEqual(content[1]['title'], folder2.title)
        self.assertEqual(content[1]['id'], folder2.id)
        self.limit_test(url, 4, num_results)

        combinations = [
            {'limit': 1, 'offset': 0},
            {'limit': 1, 'offset': 1},
            {'limit': 2, 'offset': 2},
            {'limit': 3, 'offset': 0},
        ]
        self.offset_test(url, combinations, num_results)

    def test_folder_retrieve(self):
        """Test the retrieval of an album."""

        root_folder = Folder.objects.create(
            title='Root Folder',
            owner=self.user,
            parent=None,
        )
        folder = Folder.objects.create(
            title='Test Folder',
            owner=self.user,
            parent=root_folder,
        )

        # test retrieval of child folder
        url = reverse('folder-detail', kwargs={'pk': folder.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['title'], folder.title)
        self.assertEqual(content['id'], folder.id)

        # test retrieval of root folder
        url = reverse('folder-detail', kwargs={'pk': 'root', 'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(content['title'], root_folder.title)
        self.assertEqual(content['id'], root_folder.id)

        # test retrieval of non-existent folder
        self.check_for_nonexistent_object('folder-detail', 'get', 'Folder')
