import json

from rest_framework import status

from django.contrib.auth import get_user_model
from django.urls import reverse

from artworks.models import Album, Artwork, PermissionsRelation

from .. import APITestCase, temporary_image
from . import VERSION


class AutocompleteTests(APITestCase):
    def test_autocomplete(self):
        """Test the retrieval of autocomplete results."""

        url = reverse('autocomplete', kwargs={'version': VERSION})

        # test general parameter parsing
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(f'{url}?q=a', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(f'{url}?type=users', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(f'{url}?q=a&type=nonexistenttype', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(f'{url}?q=a&type=users&limit=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test single autocomplete type
        response = self.client.get(f'{url}?q=student&type=users', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['id'], 's1234567')
        self.assertEqual(content[0]['label'], 'Test Student')

        # test multiple autocomplete types
        requested_types = ['titles', 'artists', 'users', 'keywords', 'locations']
        response = self.client.get(
            f'{url}?q=test&type={",".join(requested_types)}',
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(type(content), list)
        self.assertEqual(len(content), 5)
        for i, result_type in enumerate(content):
            self.assertEqual(type(result_type), dict)
            self.assertEqual(result_type['id'], requested_types[i])
            self.assertEqual(type(result_type['data']), list)
            for item in result_type['data']:
                self.assertEqual(type(item), dict)
                self.assertEqual('id' in item, True)
                self.assertEqual('label' in item, True)
        self.assertEqual(len(content[1]['data']), 0)  # no artists
        self.assertEqual(len(content[3]['data']), 0)  # no keywords
        self.assertEqual(len(content[4]['data']), 0)  # no locations
        self.assertEqual(len(content[2]['data']), 2)  # 2 users
        self.assertLess(3, len(content[0]['data']))  # more than 3 artwork titles
        self.assertEqual(
            content[2]['data'][0]['label'],
            'Test Lecturer',
        )  # alphabetic ordering
        self.assertEqual(
            content[2]['data'][1]['label'],
            'Test Student',
        )  # alphabetic ordering

        # test (default) limiting
        response = self.client.get(f'{url}?q=e&type=titles', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content), 10)  # default limit

        response = self.client.get(f'{url}?q=e&type=titles&limit=100', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content), 15)

        response = self.client.get(f'{url}?q=e&type=titles&limit=5', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content), 5)

        # now also test multi type response
        response = self.client.get(f'{url}?q=e&type=titles,locations', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content[0]['data']), 10)  # default limit
        self.assertEqual(len(content[0]['data']), 10)  # default limit

        response = self.client.get(
            f'{url}?q=e&type=titles,locations&limit=100',
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(10, len(content[0]['data']))
        self.assertLess(10, len(content[0]['data']))

        response = self.client.get(
            f'{url}?q=e&type=titles,locations&limit=5',
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content[0]['data']), 5)
        self.assertEqual(len(content[0]['data']), 5)

    def test_name_english_locations(self):
        url = reverse('autocomplete', kwargs={'version': VERSION})

        # Check if the 'name_en' is returned when 'accept-language' header is 'en'
        response = self.client.get(
            f'{url}?q=Bad Eisenkappel&type=locations',
            format='json',
            headers={'accept-language': 'en'},
        )
        first_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(first_result), 2)
        self.assertEqual(first_result['label'], 'Bad Eisenkappel, English')

        # Check if the 'name' is returned when 'accept-language' header is 'en' and 'name_en' is empty
        response = self.client.get(
            f'{url}?q=Galerie Vorspann&type=locations',
            format='json',
            headers={'accept-language': 'en'},
        )
        first_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(first_result), 2)
        self.assertEqual(
            first_result['label'],
            'Galerie Vorspann',
        )

        # Check if the 'name' is returned when 'accept-language' header is 'de'
        response = self.client.get(
            f'{url}?q=Bad Eisenkappel&type=locations',
            format='json',
            headers={'accept-language': 'de'},
        )
        first_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(first_result), 2)
        self.assertEqual(
            first_result['label'],
            'Bad Eisenkappel',
        )

    def test_name_english_keywords(self):
        url = reverse('autocomplete', kwargs={'version': VERSION})

        # Check if the 'name_en' is returned when 'accept-language' header is 'en'
        response = self.client.get(
            f'{url}?q=Art Déco&type=keywords',
            format='json',
            headers={'accept-language': 'en'},
        )
        first_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(first_result), 2)
        self.assertEqual(first_result['label'], 'Art Déco, English')

        # Check if the 'name' is returned when 'accept-language' header is 'en', although name_en is empty
        response = self.client.get(
            f'{url}?q=Art Brut&type=keywords',
            format='json',
            headers={'accept-language': 'en'},
        )
        first_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(first_result), 2)
        self.assertEqual(first_result['label'], 'Art Brut')

        # Check if the 'name' is returned when 'accept-language' header is 'de'
        response = self.client.get(
            f'{url}?q=Art Brut&type=keywords',
            format='json',
            headers={'accept-language': 'de'},
        )
        first_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(first_result), 2)
        self.assertEqual(first_result['label'], 'Art Brut')

    def test_title(self):
        # test if unpublished artworks are returned
        Artwork.objects.create(
            title='Test Artwork 1',
            image_original=temporary_image(),
            published=False,
        )
        url = reverse('autocomplete', kwargs={'version': VERSION})
        response = self.client.get(
            f'{url}?q=Test Artwork 1&type=titles',
            format='json',
        )
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(content), 0)

        # Check if the 'title' is returned when 'accept-language' header is 'de'
        response = self.client.get(
            f'{url}?q=loc test aut&type=titles',
            format='json',
            headers={'accept-language': 'de'},
        )
        fist_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(fist_result), 3)
        self.assertEqual(fist_result['label'], 'loc test aut')

        # Check if the 'title' is returned when 'accept-language' header is 'en'
        response = self.client.get(
            f'{url}?q=loc test aut&type=titles',
            format='json',
            headers={'accept-language': 'en'},
        )
        fist_result = json.loads(response.content)[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(fist_result), 3)
        self.assertEqual(fist_result['label'], 'loc test aut')

    def test_user_permissions_albums(self):
        # retrieve student and lecturer
        User = get_user_model()  # noqa: N806
        lecturer = User.objects.get(username='p0001234')
        student = User.objects.get(username='s1234567')
        lecturer_album1 = Album.objects.get(title='Lecturer album 1', user=lecturer)
        student_album1 = Album.objects.get(title='Student album 1', user=student)

        # provide rights to user
        PermissionsRelation.objects.create(
            user=self.user,
            album=lecturer_album1,
            permissions='VIEW',
        )
        PermissionsRelation.objects.create(
            user=self.user,
            album=student_album1,
            permissions='EDIT',
        )

        url = reverse('autocomplete', kwargs={'version': VERSION})
        response = self.client.get(
            f'{url}?q=album&type=user_albums_editable',
            format='json',
        )
        content = response.json()

        self.assertEqual(response.status_code, 200)

        # extract returned ids of albums
        album_ids = [item['id'] for item in content]

        # test if user can see their own albums
        own_albums = Album.objects.filter(user=self.user).values_list('id', flat=True)
        for album_id in own_albums:
            self.assertIn(album_id, album_ids)

        # test if user can see albums with EDIT permissions
        editable_albums = PermissionsRelation.objects.filter(
            user=self.user,
            permissions='EDIT',
        ).values_list('album__id', flat=True)
        for album_id in editable_albums:
            self.assertIn(album_id, album_ids)

        # test if user can not see albums with VIEW permissions
        not_viewable_albums = PermissionsRelation.objects.filter(
            user=self.user,
            permissions='VIEW',
        ).values_list('album__id', flat=True)
        for album_id in not_viewable_albums:
            self.assertNotIn(album_id, album_ids)
