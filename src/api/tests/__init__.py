import json
import shutil
from io import BytesIO

from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase as RestFrameworkAPITestCase

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from artworks.models import Album, Artwork, Keyword, Location, Material, Person


def temporary_image():  # from https://stackoverflow.com/a/67611074
    bts = BytesIO()
    img = Image.new('RGB', (100, 100))
    img.save(bts, 'jpeg')
    return SimpleUploadedFile('test.jpg', bts.getvalue())


@override_settings(
    MEDIA_ROOT=settings.MEDIA_ROOT_TESTS,
    MEDIA_ROOT_PATH=settings.MEDIA_ROOT_TESTS,
)
class APITestCase(RestFrameworkAPITestCase):
    def setUp(self):
        # create and log in user
        User = get_user_model()  # noqa: N806
        self.user = User.objects.create_user(
            'temporary',
            'temporary@uni-ak.ac.at',
            tos_accepted=True,
        )
        self.client.force_login(self.user)

        # add two other users
        lecturer = User.objects.create_user(
            username='p0001234',
            email='temp_p@uni-ak.ac.at',
            first_name='Test',
            last_name='Lecturer',
        )
        student = User.objects.create_user(
            username='s1234567',
            email='temp_s@uni-ak.ac.at',
            first_name='Test',
            last_name='Student',
        )

        # add keywords
        epochs = Keyword.objects.create(name='Epochen / Stile')
        art_brut = Keyword.objects.create(name='Art Brut', parent=epochs)
        art_deco = Keyword.objects.create(
            name='Art Déco',
            name_en='Art Déco, English',
            parent=epochs,
        )
        topics = Keyword.objects.create(name='Gattungen / Medien / Themen')
        Keyword.objects.create(name='Angewandte Kunst', parent=topics)
        Keyword.objects.create(name='Partizipatorische Kunst', parent=topics)
        Keyword.objects.create(name='Tanz', parent=topics)
        arch = Keyword.objects.create(name='Architektur', parent=topics)
        profan = Keyword.objects.create(name='Profanbau', parent=arch)
        Keyword.objects.create(name='Profaner Repräsentationsbau', parent=profan)
        Keyword.objects.create(name='Wohnbau', parent=profan)
        # add locations
        au = Location.objects.create(name='Australien')
        syd = Location.objects.create(name='Sydney', parent=au)
        Location.objects.create(name='Museum of Contemporary Art', parent=syd)
        aut = Location.objects.create(name='Österreich')
        linz = Location.objects.create(name='Linz', parent=aut)
        Location.objects.create(name='Offenes Kulturhaus', parent=linz)
        wien = Location.objects.create(name='Wien', parent=aut)
        Location.objects.create(name='PARALLEL Vienna', parent=wien)
        mak = Location.objects.create(
            name='Museum für Angewandte Kunst (MAK)',
            parent=wien,
        )
        Location.objects.create(name='Archiv Peichl', parent=mak)
        zelez = Location.objects.create(
            name='Bad Eisenkappel',
            name_en='Bad Eisenkappel, English',
            parent=aut,
            synonyms=['Železna Kapla'],
        )
        Location.objects.create(
            name='Galerie Vorspann',
            parent=zelez,
            synonyms=['Galerija Vprega'],
        )

        # add materials
        material_canvas = Material.objects.create(
            name='Öl auf Leinwand',
            name_en='Oil on canvas',
        )
        material_paper = Material.objects.create(
            name='Bleistift auf Papier',
            name_en='Pencil on paper',
        )
        material_poster = Material.objects.create(name='Plakat', name_en='Poster')

        # add artists
        artemisia = Person.objects.create(name='Artemisia Gentileschi')
        warwara = Person.objects.create(
            name='Warwara Fjodorowna Stepanowa',
            synonyms=['Stepanova'],
        )
        valie = Person.objects.create(name='VALIE EXPORT')
        Person.objects.create(name='Wangechi Mutu')
        Person.objects.create(name='Lina Bo Bardi')
        Person.objects.create(name='Inés Lombardi', synonyms=['Ines Lombardi'])

        # add artworks
        aw1 = Artwork.objects.create(
            title='Lucretia',
            title_english='Lucretia',
            date='1642/1643',
            date_year_from=1642,
            date_year_to=1643,
            published=True,
            checked=True,
            comments_de='Neapel, Palazzo Reale\n(Zuschreibung durch Mary D. Garrard, bisland Massimo Stanzione zugeschrieben)',
            credits='Stolzenwald, Susanna: Artemisia Gentileschi. Bindung und Befreiung in Leben und Werk einer Malerin, Belser Verlag, Stuttgart/Zürich, 1991, S. 96.',
            image_original=temporary_image(),
        )
        aw1.artists.add(artemisia)
        aw1.materials.add(material_canvas)
        aw2 = Artwork.objects.create(
            title='Die UDSSR im Aufbau [СССР на стройке] Nr. 12',  # noqa: RUF001
            title_english='The USSR in Construction [СССР на стройке] , No. 12',  # noqa: RUF001
            date='1935',
            date_year_from=1935,
            date_year_to=1935,
            published=True,
            checked=True,
            comments_de='Propagandazeitschrift der Sowjetunion, 1930-1991',
            credits='Margarita Tupitsyn/ Museum Fokwang Essen (Hg.), Glaube, Hoffnung - Anpassung, Sowjetische Bilder 1928 - 1945, 1996 Okart, S.131',
            image_original=temporary_image(),
        )
        aw2.artists.add(warwara)
        aw2.materials.add(material_poster)
        aw3 = Artwork.objects.create(
            title='Homometer II',
            title_english='Homometer II',
            date='1976',
            date_year_from=1976,
            date_year_to=1976,
            dimensions_display='je 40,5 x 28,5 cm',
            published=True,
            checked=True,
            comments_de='Essen, Brot',
            credits='Mahlzeit - Essen in der Kunst, Ausstellungskatalog, Galerie im Traklhaus, Salzburg 2009. S.51',
            image_original=temporary_image(),
        )
        aw3.artists.add(valie)
        aw3.materials.add(material_paper)
        Artwork.objects.create(
            title='multiple artists test',
            published=True,
            checked=True,
            image_original=temporary_image(),
        ).artists.add(artemisia, warwara, valie)
        Artwork.objects.create(
            title='date test 1',
            date_year_from=10,
            date_year_to=50,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )
        Artwork.objects.create(
            title='date test 2',
            date_year_from=-200,
            date_year_to=200,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )
        Artwork.objects.create(
            title='date test 3',
            date_year_from=1900,
            date_year_to=2000,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )
        Artwork.objects.create(
            title='date test 4',
            date_year_from=2000,
            date_year_to=2050,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )
        Artwork.objects.create(
            title='kw test art_brut + art_deco + art_profan',
            published=True,
            checked=True,
            image_original=temporary_image(),
        ).keywords.add(art_brut, art_deco, profan)
        Artwork.objects.create(
            title='kw test epochs',
            published=True,
            checked=True,
            image_original=temporary_image(),
        ).keywords.add(epochs)
        Artwork.objects.create(
            title='kw test arch + profan',
            published=True,
            checked=True,
            image_original=temporary_image(),
        ).keywords.add(arch, profan)
        Artwork.objects.create(
            title='loc test zelez',
            title_english='loc test zelez, English',
            location=zelez,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )
        Artwork.objects.create(
            title='loc test mak',
            location=mak,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )
        Artwork.objects.create(
            title='loc test wien',
            location=wien,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )
        Artwork.objects.create(
            title='loc test aut',
            location=aut,
            published=True,
            checked=True,
            image_original=temporary_image(),
        )

        # add albums
        Album.objects.create(title='My own album 1', user=self.user)
        Album.objects.create(title='My own album 2', user=self.user)
        Album.objects.create(title='My own album 3', user=self.user)
        Album.objects.create(title='Lecturer album 1', user=lecturer)
        Album.objects.create(title='Lecturer album 2', user=lecturer)
        Album.objects.create(title='Student album 1', user=student)
        Album.objects.create(title='Student album 2', user=student)
        # TODO: set slides and add permissions here, when the album endpoint tests are extended

        # No test folders, as currently only a root folder is implemented,
        # which should be created on demand.

    def limit_test(self, url, limit, max_items):
        # Check basic limit setting
        response = self.client.get(f'{url}?limit={limit}', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(content, dict):
            self.assertEqual(len(content['results']), min(limit, max_items))
        else:
            self.assertEqual(len(content), min(limit, max_items))

        # Check setting a negative limit
        response = self.client.get(f'{url}?limit=-1', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content['detail'], 'limit must be a positive integer')

        # Check setting 0 as limit
        response = self.client.get(f'{url}?limit=0', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content['detail'], 'limit must be a positive integer')

    def offset_test(self, url, combinations, max_items):
        # Test different limit and offset combinations
        for val in combinations:
            response = self.client.get(
                f'{url}?limit={val["limit"]}&offset={val["offset"]}',
                format='json',
            )
            content = json.loads(response.content)

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            num = max(min(max_items - val['offset'], val['limit']), 0)
            if isinstance(content, dict):
                self.assertEqual(len(content['results']), num)
            else:
                self.assertEqual(len(content), num)

        # Check setting a negative offset
        response = self.client.get(f'{url}?offset=-1', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(content['detail'], 'negative offset is not allowed')

        # Check setting a 0 offset
        response = self.client.get(f'{url}?offset=0', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(content, dict):
            self.assertEqual(content['total'], max_items)
            self.assertEqual(len(content['results']), max_items)
        else:
            self.assertEqual(len(content), max_items)

        # Check setting no limit but setting offset
        offset = 5
        response = self.client.get(f'{url}?offset={offset}', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(content, dict):
            self.assertEqual(content['total'], max_items)
            self.assertEqual(len(content['results']), max(0, max_items - offset))
        else:
            self.assertEqual(len(content), max(0, max_items - offset))

        # Check setting offset more than the maximum available items
        response = self.client.get(f'{url}?offset={max_items + 1}', format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(content, dict):
            self.assertEqual(len(content['results']), 0)
        else:
            self.assertEqual(len(content), 0)

        # Check setting offset but with a small limit
        response = self.client.get(f'{url}?limit=1&offset=2', format='json')
        content = json.loads(response.content)

        if isinstance(content, dict):
            self.assertEqual(len(content['results']), 1)
        else:
            self.assertEqual(len(content), 1)

    def album_does_not_exist(self, view_name, http_method, data=None):
        # test the retrieval/deletion/updating/etc of an album, when album doesn't exist
        url = reverse(view_name, kwargs={'pk': 11111, 'version': 'v1'})
        response = getattr(self.client, http_method)(url, data=data, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(content['detail'], 'Album does not exist')

    def tearDown(self):
        # delete temporary files again
        shutil.rmtree(settings.MEDIA_ROOT_TESTS, ignore_errors=True)
