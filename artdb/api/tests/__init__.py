from io import BytesIO

from artworks.models import Album, Artist, Artwork, Keyword, Location
from PIL import Image
from rest_framework.test import APITestCase as RestFrameworkAPITestCase

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile


def temporary_image():  # from https://stackoverflow.com/a/67611074
    bts = BytesIO()
    img = Image.new('RGB', (100, 100))
    img.save(bts, 'jpeg')
    return SimpleUploadedFile('test.jpg', bts.getvalue())


class APITestCase(RestFrameworkAPITestCase):
    def setUp(self):
        # create and log in user
        User = get_user_model()
        self.user = User.objects.create_user('temporary', 'temporary@uni-ak.ac.at')
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
        art_deco = Keyword.objects.create(name='Art Déco', parent=epochs)
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
            parent=aut,
            synonyms='Železna Kapla',
        )
        Location.objects.create(
            name='Galerie Vorspann',
            parent=zelez,
            synonyms='Galerija Vprega',
        )

        # add artists
        artemisia = Artist.objects.create(name='Artemisia Gentileschi')
        warwara = Artist.objects.create(
            name='Warwara Fjodorowna Stepanowa',
            synonyms='Stepanova',
        )
        valie = Artist.objects.create(name='VALIE EXPORT')
        Artist.objects.create(name='Wangechi Mutu')
        Artist.objects.create(name='Lina Bo Bardi')
        Artist.objects.create(name='Inés Lombardi', synonyms='Ines Lombardi')

        # add artworks
        Artwork.objects.create(
            title='Lucretia',
            title_english='Lucretia',
            date='1642/1643',
            date_year_from=1642,
            date_year_to=1643,
            material='Öl auf Leinwand',
            published=True,
            checked=True,
            comments='Neapel, Palazzo Reale\n(Zuschreibung durch Mary D. Garrard, bisland Massimo Stanzione zugeschrieben)',
            credits='Stolzenwald, Susanna: Artemisia Gentileschi. Bindung und Befreiung in Leben und Werk einer Malerin, Belser Verlag, Stuttgart/Zürich, 1991, S. 96.',
            image_original=temporary_image(),
        ).artists.add(artemisia)
        Artwork.objects.create(
            title='Die UDSSR im Aufbau [СССР на стройке] Nr. 12',
            title_english='The USSR in Construction [СССР на стройке] , No. 12',
            date='1935',
            date_year_from=1935,
            date_year_to=1935,
            material='Plakat',
            published=True,
            checked=True,
            comments='Propagandazeitschrift der Sowjetunion, 1930-1991',
            credits='Margarita Tupitsyn/ Museum Fokwang Essen (Hg.), Glaube, Hoffnung - Anpassung, Sowjetische Bilder 1928 - 1945, 1996 Okart, S.131',
            image_original=temporary_image(),
        ).artists.add(warwara)
        Artwork.objects.create(
            title='Homometer II',
            title_english='Homometer II',
            date='1976',
            date_year_from=1976,
            date_year_to=1976,
            material='4 s/w Fotografien, Vintage prints, Unikate',
            dimensions='je 40,5 x 28,5 cm',
            published=True,
            checked=True,
            comments='Essen, Brot',
            credits='Mahlzeit - Essen in der Kunst, Ausstellungskatalog, Galerie im Traklhaus, Salzburg 2009. S.51',
            image_original=temporary_image(),
        ).artists.add(valie)
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
