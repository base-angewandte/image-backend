import hashlib
import logging
import re
from io import BytesIO
from pathlib import Path

from base_common.fields import ShortUUIDField
from base_common.models import AbstractBaseModel
from django_jsonform.models.fields import ArrayField
from mptt.models import MPTTModel, TreeForeignKey
from PIL import Image
from versatileimagefield.fields import VersatileImageField

from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.db.models import JSONField
from django.db.models.functions import Length, Upper
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from .fetch import fetch_getty_data, fetch_wikidata
from .fetch.exceptions import DataNotFoundError, HTTPError, RequestError
from .gnd import (
    add_preferred_name_to_synonyms,
    construct_individual_name,
    process_external_metadata,
)
from .managers import ArtworkManager
from .mixins import LocalizationMixin, MetaDataMixin
from .utils import remove_non_printable_characters
from .validators import validate_getty_id, validate_image_original

logger = logging.getLogger(__name__)


class Person(AbstractBaseModel, MetaDataMixin):
    """A Person can fulfill several roles for 0-n artworks."""

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
        null=False,
        blank=True,
    )
    synonyms = ArrayField(
        models.CharField(),
        verbose_name=_('Synonyms'),
        default=list,
        blank=True,
    )
    synonyms_old = models.CharField(
        verbose_name=_('Synonyms (old)'),
        null=False,
        blank=True,
    )

    date_birth = models.DateField(null=True, blank=True)
    date_death = models.DateField(null=True, blank=True)
    date_display = models.CharField(
        blank=True,
        help_text=_('Overrides birth and death dates for display, if not empty.'),
    )
    gnd_id = models.CharField(
        verbose_name=f'{settings.GND_LABEL} ID',
        max_length=16,
        null=True,
        blank=True,
        unique=True,
    )
    gnd_overwrite = models.BooleanField(
        default=True,
        help_text=_('Overwrite entry with data from %(label)s?')
        % {'label': settings.GND_LABEL},
    )
    external_metadata = JSONField(null=True, blank=True, default=dict)

    class Meta:
        ordering = ['name']
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        process_external_metadata(self)

    def set_birth_death_from_gnd_data(self):
        """Sets a Person's birth and death dates, based on a GND result."""

        if gnd_data := self.get_external_metadata_response_data('gnd'):
            # while theoretically there could be more than one date, it was
            # decided to just use the first listed date if there is one
            date_display = ''
            if 'dateOfBirth' in gnd_data:
                if re.match(settings.GND_DATE_REGEX, gnd_data.get('dateOfBirth')[0]):
                    self.date_birth = gnd_data.get('dateOfBirth')[0]

                date_display += gnd_data.get('dateOfBirth')[0] + ' - '

            if 'dateOfDeath' in gnd_data:
                if re.match(settings.GND_DATE_REGEX, gnd_data.get('dateOfDeath')[0]):
                    self.date_death = gnd_data.get('dateOfDeath')[0]

                if not date_display:
                    date_display += ' - '

                date_display += gnd_data.get('dateOfDeath')[0]

            if date_display:
                self.date_display = date_display

    def set_name_from_gnd_data(self):
        """Sets a Person's name, based on a GND result.

        To generate the name, the `preferredNameEntityForThePerson` property
        of the response is used. As a fallback the `preferredName` will be
        used.
        """

        if gnd_data := self.get_external_metadata_response_data('gnd'):
            if 'preferredNameEntityForThePerson' in gnd_data:
                self.name = construct_individual_name(
                    gnd_data['preferredNameEntityForThePerson'],
                )
            elif 'preferredName' in gnd_data:
                self.name = gnd_data['preferredName'].strip()

    def set_synonyms_from_gnd_data(self):
        """Sets a Person's synonyms, based on a GND result.

        To generate the name, the `variantNameEntityForThePerson` property
        of the response is used. As a fallback the `variantName` will be
        used.
        """
        if gnd_data := self.get_external_metadata_response_data('gnd'):
            if 'variantNameEntityForThePerson' in gnd_data:
                synonyms = []
                for n in gnd_data['variantNameEntityForThePerson']:
                    synonym = construct_individual_name(n)
                    synonyms.append(synonym)
                self.synonyms = synonyms
            elif 'variantName' in gnd_data:
                self.synonyms = gnd_data['variantName']

    def update_with_gnd_data(self, gnd_data):
        self.set_external_metadata('gnd', gnd_data)
        if self.gnd_overwrite:
            self.set_name_from_gnd_data()
            self.set_synonyms_from_gnd_data()
            self.set_birth_death_from_gnd_data()


class Keyword(MPTTModel, MetaDataMixin, LocalizationMixin):
    """Keywords are nodes in a fixed hierarchical taxonomy."""

    name = models.CharField(
        verbose_name=_('Name (DE)'),
        max_length=255,
        unique=True,
    )
    name_en = models.CharField(
        verbose_name=_('Name (EN)'),
        max_length=255,
        blank=True,
        default='',
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    getty_id = models.URLField(
        verbose_name=f'{settings.GETTY_LABEL} ID',
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    getty_overwrite = models.BooleanField(
        default=True,
        help_text=_('Overwrite Name, English with data from %(label)s?')
        % {'label': settings.GETTY_LABEL},
    )
    external_metadata = JSONField(
        null=True,
        blank=True,
        default=dict,
    )

    class Meta:
        verbose_name = _('Keyword')
        verbose_name_plural = _('Keywords')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name_localized

    @property
    def name_localized(self):
        return self.get_localized_property('name')

    def clean(self):
        super().clean()

        if self.getty_id:
            # Validate getty url
            validate_getty_id(self.getty_id)

            # Fetch the external metadata
            try:
                getty_data = fetch_getty_data(self.getty_id)
                self.update_with_getty_data(getty_data)
            except DataNotFoundError as err:
                raise ValidationError(
                    {
                        'getty_id': _(
                            'No %(label)s entry was found for %(label)s ID %(id)s.',
                        )
                        % {
                            'label': settings.GETTY_LABEL,
                            'id': self.getty_id,
                        },
                    },
                ) from err
            except HTTPError as err:
                logger.warning(
                    f'HTTP error {err.status_code} when retrieving {settings.GETTY_LABEL} data: {err.details}',
                )
                raise ValidationError(
                    {
                        'getty_id': _(
                            'HTTP error %(status_code)s when retrieving %(label)s data: %(details)s',
                        )
                        % {
                            'status_code': err.status_code,
                            'label': settings.GETTY_LABEL,
                            'details': err.details,
                        },
                    },
                ) from err
            except RequestError as err:
                logger.warning(
                    f'Request error when retrieving {settings.GETTY_LABEL} data. Details: {repr(err)}',
                )
                raise ValidationError(
                    {
                        'getty_id': _(
                            'Request error when retrieving %(label)s data: %(error)s',
                        )
                        % {
                            'label': settings.GETTY_LABEL,
                            'error': repr(err),
                        },
                    },
                ) from err
        elif self.external_metadata:
            self.external_metadata = {}

    def set_name_en_from_getty_data(self):
        if getty_data := self.get_external_metadata_response_data('getty'):  # noqa: SIM102
            if '_label' in getty_data:
                self.name_en = getty_data['_label']

    def update_with_getty_data(self, getty_data, save=False):
        self.set_external_metadata('getty', getty_data)
        if self.getty_overwrite:
            self.set_name_en_from_getty_data()
        if save:
            self.save()


class Location(MPTTModel, MetaDataMixin, LocalizationMixin):
    """Locations are nodes in a fixed hierarchical taxonomy."""

    name = models.CharField(
        verbose_name=_('Name (DE)'),
        max_length=255,
        blank=True,
        null=False,
    )
    name_en = models.CharField(
        verbose_name=_('Name (EN)'),
        max_length=255,
        blank=True,
        default='',
    )
    synonyms = ArrayField(
        models.CharField(),
        verbose_name=_('Synonyms'),
        default=list,
        blank=True,
    )
    synonyms_old = models.CharField(
        verbose_name=_('Synonyms (old)'),
        blank=True,
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    gnd_id = models.CharField(
        verbose_name=f'{settings.GND_LABEL} ID',
        max_length=16,
        null=True,
        blank=True,
        unique=True,
    )
    gnd_overwrite = models.BooleanField(
        default=True,
        help_text=_('Overwrite entry with data from %(label)s?')
        % {'label': settings.GND_LABEL},
    )

    external_metadata = JSONField(null=True, blank=True, default=dict)

    class Meta:
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return ' > '.join(
            ancestor.name_localized
            for ancestor in self.get_ancestors(include_self=True)
        )

    @property
    def name_localized(self):
        return self.get_localized_property('name')

    def clean(self):
        super().clean()
        process_external_metadata(self)

    def set_name_from_gnd_data(self):
        if gnd_data := self.get_external_metadata_response_data('gnd'):
            if 'preferredName' in gnd_data:
                self.name = gnd_data['preferredName']
            else:
                raise ValidationError(
                    _(
                        'The %(label)s database does not provide a preferred name for this %(label)s ID.',
                    )
                    % {'label': settings.GND_LABEL},
                )

    def set_synonyms_from_gnd_data(self):
        if gnd_data := self.get_external_metadata_response_data('gnd'):
            self.synonyms = gnd_data.get('variantName', [])

    def update_with_gnd_data(self, gnd_data, save=False):
        self.set_external_metadata('gnd', gnd_data)

        if wikidata_link := self.get_wikidata_link():
            try:
                wikidata_data = fetch_wikidata(wikidata_link)
                entity_id = next(iter(wikidata_data['entities'].keys()))
                entity_data = wikidata_data['entities'].get(entity_id, {})
                simplified_wikidata_data = {
                    'modified': entity_data.get('modified', None),
                    'id': entity_data.get('id', None),
                    'labels': entity_data.get('labels', None),
                }
                self.set_external_metadata(
                    'wikidata',
                    simplified_wikidata_data,
                )
            except DataNotFoundError:
                # 404 on Wikidata just means we have no translation, but we
                # continue processing the rest of the GND data as usual
                pass
            except HTTPError as err:
                logger.warning(
                    f'HTTP error {err.status_code} when retrieving {settings.WIKIDATA_LABEL} data: {err.details}',
                )
            except RequestError as err:
                logger.warning(
                    f'Request error when retrieving {settings.WIKIDATA_LABEL} data. Details: {repr(err)}',
                )
        else:
            self.delete_external_metadata('wikidata')

        if self.gnd_overwrite:
            self.set_name_from_gnd_data()
            self.set_synonyms_from_gnd_data()
            self.name_en = ''
            self.set_name_en_from_wikidata()
        else:
            add_preferred_name_to_synonyms(self, gnd_data)

        if save:
            self.save()

    def get_wikidata_link(self):
        if gnd_data := self.get_external_metadata_response_data('gnd'):  # noqa: SIM102
            if 'sameAs' in gnd_data:
                for concept in gnd_data['sameAs']:
                    if 'wikidata' in concept['id']:
                        return concept['id']

    def set_name_en_from_wikidata(self):
        if wikidata := self.get_external_metadata_response_data('wikidata'):
            labels = wikidata.get('labels', {})
            if 'en-gb' in labels:
                self.name_en = labels['en-gb']['value']
            elif 'en' in labels:
                self.name_en = labels['en']['value']


class Material(AbstractBaseModel, LocalizationMixin):
    """Material types for artworks."""

    name = models.TextField(
        verbose_name=_('Material/Technique (DE)'),
    )
    name_en = models.TextField(
        verbose_name=_('Material/Technique (EN)'),
        blank=True,
        default='',
    )

    def __str__(self):
        return self.name_localized

    @property
    def name_localized(self):
        return self.get_localized_property('name')


def get_path_to_file(instance, filename, folder):
    """The uploaded images of artworks are stored in a specific directory
    structure based on the pk/id of the artwork.

    Example:
        artwork.pk==16320, filename=='example.jpg', folder=='image_original'

        path = 'artworks/image_original/16320/example.jpg'
    """

    prefix = f'artworks/{folder}'
    if instance.pk:
        return f'{prefix}/{instance.pk}/{filename}'
    return filename


def get_path_to_original_file(instance, filename):
    return get_path_to_file(instance, filename, 'image_original')


def get_path_to_image_fullsize(instance, filename):
    return get_path_to_file(instance, filename, 'image_fullsize')


class Artwork(AbstractBaseModel, LocalizationMixin):
    """Each Artwork has an metadata and image and various versions (renditions)
    of that image."""

    id = ShortUUIDField(primary_key=True)
    archive_id = models.BigIntegerField(null=True)

    # VersatileImageField allows to create resized versions of the
    # image (renditions) on demand
    image_original = VersatileImageField(
        verbose_name=_('Original Image'),
        max_length=255,
        null=False,
        blank=False,
        upload_to=get_path_to_original_file,
        validators=[validate_image_original],
    )

    image_fullsize = VersatileImageField(
        verbose_name=_('Fullsize Image'),
        max_length=255,
        null=False,
        blank=True,
        upload_to=get_path_to_image_fullsize,
    )

    title = models.CharField(verbose_name=_('Title'), max_length=255)
    title_english = models.CharField(
        verbose_name=_('Title, English'),
        max_length=255,
        blank=True,
    )
    title_comment_de = models.TextField(
        verbose_name=_('Comment on title (DE)'),
        blank=True,
    )
    title_comment_en = models.TextField(
        verbose_name=_('Comment on title (EN)'),
        blank=True,
    )
    discriminatory_terms = models.ManyToManyField(
        'DiscriminatoryTerm',
        verbose_name=_('Discriminatory terms'),
    )
    artists = models.ManyToManyField(
        Person,
        verbose_name=_('Artists'),
        related_name='artworks_artists',
    )
    photographers = models.ManyToManyField(
        Person,
        verbose_name=_('Photographers'),
        related_name='artworks_photographers',
    )
    authors = models.ManyToManyField(
        Person,
        verbose_name=_('Authors'),
        related_name='artworks_authors',
    )
    graphic_designers = models.ManyToManyField(
        Person,
        verbose_name=_('Graphic designers'),
        related_name='artworks_graphic_designers',
    )
    date = models.CharField(
        verbose_name=_('Date'),
        max_length=319,
        blank=True,
        help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende/Anfang 14. Jh., 5.3.1799, ca./um/vor/nach 1700, 4000 BC/v.Chr.',
    )
    date_year_from = models.IntegerField(
        verbose_name=_('Date From'),
        null=True,
        blank=True,
    )
    date_year_to = models.IntegerField(verbose_name=_('Date To'), null=True, blank=True)
    materials = models.ManyToManyField(
        Material,
        verbose_name=_('Material/Technique'),
        related_name='artworks',
    )
    material_description_de = models.TextField(
        verbose_name=_('Material/Technique description (DE)'),
        help_text=_('Description of artwork materials and composition.'),
        blank=True,
    )
    material_description_en = models.TextField(
        verbose_name=_('Material/Technique description (EN)'),
        help_text=_('Description of artwork materials and composition.'),
        blank=True,
    )
    width = models.FloatField(
        verbose_name=_('Width'),
        help_text='in cm',
        null=True,
        blank=True,
    )
    height = models.FloatField(
        verbose_name=_('Height'),
        help_text='in cm',
        null=True,
        blank=True,
    )
    depth = models.FloatField(
        verbose_name=_('Depth'),
        help_text='in cm',
        null=True,
        blank=True,
    )
    dimensions_display = models.CharField(
        verbose_name=_('Dimensions'),
        max_length=255,
        blank=True,
        help_text=_(
            'Generated from width, height, and depth, but can also be set manually.',
        ),
    )
    comments_de = models.TextField(verbose_name=_('Comments (DE)'), blank=True)
    comments_en = models.TextField(verbose_name=_('Comments (EN)'), blank=True)
    credits = models.TextField(verbose_name=_('Credits'), blank=True)
    credits_link = models.URLField(verbose_name=_('Credits URL'), blank=True)
    keywords = models.ManyToManyField(
        Keyword,
        verbose_name=_('Keywords'),
        related_name='artworks',
    )
    link = models.URLField(verbose_name=_('Further information'), blank=True)
    place_of_production = models.ManyToManyField(
        Location,
        verbose_name=_('Place of Production'),
        blank=True,
        related_name='artworks_created_here',
    )
    location = TreeForeignKey(
        Location,
        verbose_name=_('Location'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='artworks_currently_located_here',
    )
    checked = models.BooleanField(verbose_name=_('Checked'), default=False)
    published = models.BooleanField(verbose_name=_('Published'), default=False)

    # search fields
    search_persons = models.CharField(blank=True, default='')
    search_locations = models.CharField(blank=True, default='')
    search_keywords = models.CharField(blank=True, default='')
    search_materials = models.CharField(blank=True, default='')
    search_vector = SearchVectorField(null=True, editable=False)

    objects = ArtworkManager()

    class Meta:
        ordering = [
            Upper('title'),
        ]
        verbose_name = _('Artwork')
        verbose_name_plural = _('Artworks')

    def __str__(self):
        return self.title

    @property
    def comments_localized(self):
        return self.get_localized_property('comments')

    @property
    def material_description_localized(self):
        return self.get_localized_property('material_description')

    @property
    def title_comment_localized(self):
        return self.get_localized_property('title_comment')

    @property
    def editing_link(self):
        return reverse('admin:artworks_artwork_change', kwargs={'object_id': self.pk})

    @staticmethod
    def get_license_label():
        return _('Rights of use')

    @staticmethod
    def get_title_comment_label():
        return _('Comment on title')

    @staticmethod
    def get_material_description_label():
        return _('Material/Technique description')

    @staticmethod
    def get_comments_label():
        return _('Comments')

    def get_short_description(self, language):
        artists = ', '.join(artist.name for artist in self.artists.all())
        title_in_language = (
            self.title_english
            if language == 'en' and self.title_english
            else self.title
        )
        parts = [artists, title_in_language, self.date]
        description = ', '.join(x.strip() for x in parts if x.strip())
        description = remove_non_printable_characters(description)
        return description

    def get_discriminatory_terms_list(self, order_by_length=False):
        qs = self.discriminatory_terms.all()

        if order_by_length:
            qs = qs.order_by(Length('term').desc())

        return qs.values_list('term', flat=True)

    def get_place_of_production_list(self):
        return [
            {
                'id': location.id,
                'value': location.name_localized,
            }
            for location in self.place_of_production.all()
        ]

    def update_search_vector(self):
        # Update search fields
        # persons
        persons_ids = []
        persons = []

        persons_ids.extend(self.artists.values_list('pk', flat=True))
        persons_ids.extend(self.photographers.values_list('pk', flat=True))
        persons_ids.extend(self.authors.values_list('pk', flat=True))
        persons_ids.extend(self.graphic_designers.values_list('pk', flat=True))

        for person in Person.objects.filter(pk__in=set(persons_ids)):
            persons.append(person.name)
            persons.extend(person.synonyms)

        # locations
        locations_ids = []
        locations = []

        locations_ids.extend(
            Location.objects.get_queryset_descendants(
                self.place_of_production,
                include_self=True,
            ).values_list('pk', flat=True),
        )
        if self.location:
            locations_ids.extend(
                Location.objects.filter(pk=self.location.pk)
                .get_descendants(include_self=True)
                .values_list('pk', flat=True),
            )

        for location in Location.objects.filter(id__in=set(locations_ids)):
            locations.append(location.name)
            if location.name_en:
                locations.append(location.name_en)
            locations.extend(location.synonyms)

        # keywords
        keywords = []

        for keyword in Keyword.objects.get_queryset_descendants(
            self.keywords,
            include_self=True,
        ):
            keywords.append(keyword.name)
            if keyword.name_en:
                keywords.append(keyword.name_en)

        # materials
        materials = []

        for material in self.materials.all():
            materials.append(material.name)
            if material.name_en:
                materials.append(material.name_en)

        if self.material_description_de:
            materials.append(self.material_description_de)
        if self.material_description_en:
            materials.append(self.material_description_en)

        search_vector = (
            SearchVector('title', weight='A')
            + SearchVector('title_english', weight='A')
            + SearchVector('search_persons', weight='A')
            + SearchVector('comments_de', weight='B', config='german')
            + SearchVector('comments_en', weight='B', config='english')
            + SearchVector('search_keywords', weight='B')
            + SearchVector('search_locations', weight='B')
            + SearchVector('credits', weight='C')
            + SearchVector('credits_link', weight='C')
            + SearchVector('search_materials', weight='C')
            + SearchVector('dimensions_display', weight='C')
            + SearchVector('link', weight='C')
            + SearchVector('date', weight='C')
        )

        Artwork.objects.filter(pk=self.pk).update(
            search_persons=' '.join(persons),
            search_locations=' '.join(locations),
            search_keywords=' '.join(keywords),
            search_materials=' '.join(materials),
            search_vector=search_vector,
        )

    def create_image_fullsize(self, save=True):
        # cleanup before creation
        if self.image_fullsize:
            self.image_fullsize.delete_all_created_images()
            self.image_fullsize.delete(save=False)

        img_io = BytesIO()
        with Image.open(self.image_original) as img:
            # check if image contains transparency:
            if img.mode in ['LA', 'RGBA', 'RGBa']:
                bg_color = (255, 255, 255)
                img_new = Image.new('RGB', img.size, bg_color)
                img_new.paste(img, (0, 0), img)
            else:
                img_new = img.convert('RGB')
            img_new.save(img_io, format='JPEG', subsampling=0, quality=95)

        original_name = Path(self.image_original.name).stem
        fullsize_name = urlsafe_base64_encode(
            hashlib.blake2s(
                original_name.encode(),
                digest_size=8,
            ).digest(),
        )

        # Save the image to the image_fullsize field
        self.image_fullsize.save(f'{fullsize_name}.jpg', File(img_io), save=False)
        if save:
            self.save(update_fields=['image_fullsize'])


class Album(AbstractBaseModel):
    """Specific users can create their own collections of artworks."""

    id = ShortUUIDField(primary_key=True)
    archive_id = models.BigIntegerField(null=True)
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
    )
    slides = JSONField(verbose_name=_('Slides'), default=list)
    permissions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Permissions'),
        through='PermissionsRelation',
        symmetrical=False,
        related_name='permissions',
    )
    last_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Last changed by'),
        related_name='last_album_changes',
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return f'{self.title} by {self.user.get_full_name()}'

    def size(self):
        return sum([len(slide['items']) for slide in self.slides])

    class Meta:
        verbose_name = _('Album')
        verbose_name_plural = _('Albums')


def get_default_permissions():
    return settings.DEFAULT_PERMISSIONS[0]


class PermissionsRelation(models.Model):
    PERMISSION_CHOICES = tuple((p, _(p)) for p in settings.PERMISSIONS)

    album = models.ForeignKey(Album, related_name='album', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='user',
        on_delete=models.CASCADE,
    )
    permissions = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=get_default_permissions,
    )

    class Meta:
        unique_together = ['album', 'user']

    def __str__(self):
        return f'{self.user.get_full_name()} <-- {self.get_permissions_display()} --> {self.album.title}'


class Folder(AbstractBaseModel):
    # unique id
    id = ShortUUIDField(
        primary_key=True,
    )
    title = models.CharField(
        verbose_name=_('Title'),
        max_length=255,
        blank=False,
        null=False,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='folder_owner',
    )
    albums = models.ManyToManyField(
        Album,
        verbose_name=_('Albums'),
        through='FolderAlbumRelation',
        related_name='folder_to_albums',
    )
    parent = models.ForeignKey(
        'Folder',
        on_delete=models.CASCADE,
        related_name='folder_to_parent',
        null=True,
    )

    def __str__(self):
        return self.title

    @property
    def is_root(self):
        return self.parent is None

    @staticmethod
    def root_folder_for_user(user):
        # All albums should be related to it. If no album exists, then folder is empty
        folder, created = Folder.objects.get_or_create(owner=user, parent=None)
        if created:
            user_albums = user.album_set.all()
            folder.title = f'{user.username}-root'
            folder.save()
            for a in user_albums:
                # Add relation to albums
                FolderAlbumRelation(album=a, user=user, folder=folder).save()
        return folder


class FolderAlbumRelation(models.Model):
    album = models.ForeignKey(
        Album,
        related_name='rel_to_album',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='rel_to_user',
        on_delete=models.CASCADE,
    )
    folder = models.ForeignKey(
        Folder,
        related_name='rel_to_folder',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.folder.title} <-- {self.user.get_full_name()} --> {self.album.title}'


class DiscriminatoryTerm(models.Model):
    """Defined and extensible set of discriminatory terms that should be
    contextualised by frontend."""

    term = models.CharField(max_length=255)

    class Meta:
        ordering = [Upper('term')]

    def __str__(self):
        return self.term
