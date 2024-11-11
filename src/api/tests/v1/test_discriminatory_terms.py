import json

from rest_framework import status

from django.urls import reverse

from artworks.models import Artwork, DiscriminatoryTerm

from .. import APITestCase, temporary_image
from . import VERSION


class DiscriminatoryTermsTests(APITestCase):
    def test_discriminatory_terms(self):
        """Test the retrieval of the discriminatory terms list."""

        artwork = Artwork.objects.create(
            title='Test Artwork',
            image_original=temporary_image(),
            published=True,
        )
        dt1 = DiscriminatoryTerm.objects.create(term='Barbarian')
        dt2 = DiscriminatoryTerm.objects.create(term='Colored')
        dt3 = DiscriminatoryTerm.objects.create(term='Disabled')
        artwork.discriminatory_terms.add(dt1, dt2, dt3)

        url = reverse('artwork-detail', kwargs={'pk': artwork.pk, 'version': VERSION})
        response = self.client.get(url, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(type(content), dict)

        terms = content.get('discriminatory_terms')

        self.assertEqual(type(terms), list)
        self.assertEqual(len(terms), 3)
        self.assertEqual(terms[2], 'Disabled')
