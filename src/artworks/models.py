import logging
import re
from pathlib import Path

import requests
from base_common.fields import ShortUUIDField
from base_common.models import AbstractBaseModel
from mptt.models import MPTTModel, TreeForeignKey
from versatileimagefield.fields import VersatileImageField

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import JSONField, Value
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from django.db.models.functions import Upper
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .managers import ArtworkManager
from .mixins import MetaDataMixin

logger = logging.getLogger(__name__)


def validate_gnd_id(gnd_id):
    if not re.match(
        settings.GND_ID_REGEX,
        gnd_id,
    ):
        raise ValidationError(_('Invalid GND ID format.'))


def validate_getty_id(getty_url):
    reg = r'^http:\/\/vocab\.getty\.edu\/aat\/[0-9]+$'
    if not re.match(
        reg,
        getty_url,
    ):
        raise ValidationError(_('Invalid getty ID format.'))


def fetch_getty_data(getty_link):
    if getty_link is None:
        return None
    try:
        response = requests.get(
            getty_link + '.json',
            timeout=settings.REQUESTS_TIMEOUT,
        )
    except requests.RequestException as e:
        raise ValidationError(
            _('Request error when retrieving getty data. Details: %(details)s'),
            params={'details': f'{repr(e)}'},
        ) from e
    if response.status_code != 200:
        if response.status_code == 404:
            raise ValidationError(
                _('No getty entry was found with ID %(id)s.'),
                params={'id': getty_link},
            )
        raise ValidationError(
            _('HTTP error %(status)s when retrieving getty data: %(details)s'),
            params={'status': response.status_code, 'details': response.text},
        )

    return response.json()


def fetch_gnd_data(gnd_id):
    try:
        response = requests.get(
            settings.GND_API_BASE_URL + gnd_id,
            timeout=settings.REQUESTS_TIMEOUT,
        )
    except requests.RequestException as e:
        raise ValidationError(
            _('Request error when retrieving GND data. Details: %(details)s'),
            params={'details': f'{repr(e)}'},
        ) from e

    if response.status_code != 200:
        if response.status_code == 404:
            raise ValidationError(
                _('No GND entry was found with ID %(id)s.'),
                params={'id': gnd_id},
            )
        raise ValidationError(
            _('HTTP error %(status)s when retrieving GND data: %(details)s'),
            params={'status': response.status_code, 'details': response.text},
        )
    gnd_data = response.json()

    return gnd_data


def process_external_metadata(instance):
    """Process external metadata for the given instance, to avoid code
    duplication.

    It is used by both clean functions of Artist and Location.
    """
    if not instance.name and not instance.gnd_id:
        raise ValidationError(_('Either a name or a valid GND ID need to be set'))

    if instance.gnd_id:
        # Validate the gnd_id and fetch the external metadata
        validate_gnd_id(instance.gnd_id)
        # Fetch the external metadata
        gnd_data = fetch_gnd_data(instance.gnd_id)
        instance.update_with_gnd_data(gnd_data)
    elif instance.external_metadata:
        instance.external_metadata = {}


class Artist(AbstractBaseModel, MetaDataMixin):
    """One Artist can be the maker of 0-n artworks."""

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
        null=False,
        blank=True,
    )
    synonyms = models.CharField(
        verbose_name=_('Synonyms'),
        null=False,
        blank=True,
        help_text=_('Comma-separated list of synonyms.'),
    )

    date_birth = models.DateField(null=True, blank=True)
    date_death = models.DateField(null=True, blank=True)
    date_display = models.CharField(  # noqa: DJ001
        null=True,
        blank=True,
        help_text=_('Overrides birth and death dates for display, if not empty.'),
    )
    gnd_id = models.CharField(max_length=16, null=True, blank=True, unique=True)
    gnd_overwrite = models.BooleanField(
        default=True,
        help_text=_('Overwrite entry with data from GND?'),
    )
    external_metadata = JSONField(null=True, blank=True, default=dict)

    class Meta:
        ordering = ['name']
        verbose_name = _('Artist')
        verbose_name_plural = _('Artists')

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        process_external_metadata(self)

    def set_birth_death_from_gnd_data(self, gnd_data):
        """Sets an Arist name, based on a GND result.

        :param dict gnd_data: GND response data for the Artist
        """
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

    def construct_individual_name(self, gnd_name_information):
        name = ''
        if 'nameAddition' in gnd_name_information:
            name += gnd_name_information['nameAddition'][0] + ' '
        if 'personalName' in gnd_name_information:
            if 'prefix' in gnd_name_information:
                name += gnd_name_information['prefix'][0] + ' '
            name += gnd_name_information['personalName'][0]
        else:
            if 'forename' in gnd_name_information:
                name += gnd_name_information['forename'][0] + ' '
            if 'prefix' in gnd_name_information:
                name += gnd_name_information['prefix'][0] + ' '
            if 'surname' in gnd_name_information:
                name += gnd_name_information['surname'][0]
        return name.strip()

    def set_name_from_gnd_data(self, gnd_data):
        """Sets an Arist's name, based on a GND result.

        To generate the name, the `preferredNameEntityForThePerson` property
        of the response is used. As a fallback the `preferredName` will be
        used.

        :param dict gnd_data: response data of the GND API for the Artist
        """
        if 'preferredNameEntityForThePerson' in gnd_data:
            self.name = self.construct_individual_name(
                gnd_data['preferredNameEntityForThePerson'],
            )
        elif 'preferredName' in gnd_data:
            self.name = gnd_data['preferredName'].strip()

    def set_synonyms_from_gnd_data(self, gnd_data):
        """Sets an Arist's synonyms, based on a GND result.

        To generate the name, the `variantNameEntityForThePerson` property
        of the response is used. As a fallback the `variantName` will be
        used.

        :param dict gnd_data: response data of the GND API for the Artist
        """
        if 'variantNameEntityForThePerson' in gnd_data:
            synonyms = []
            for n in gnd_data['variantNameEntityForThePerson']:
                synonym = self.construct_individual_name(n)
                synonyms.append(synonym)
            self.synonyms = ', '.join(synonyms)
        elif 'variantName' in gnd_data:
            self.synonyms = ', '.join(gnd_data['variantName'])

    def update_with_gnd_data(self, gnd_data):
        self.set_external_metadata('gnd', gnd_data)
        if self.gnd_overwrite:
            self.set_name_from_gnd_data(gnd_data)
            self.set_synonyms_from_gnd_data(gnd_data)
            self.set_birth_death_from_gnd_data(gnd_data)


def get_path_to_original_file(instance, filename):
    """The uploaded images of artworks are stored in a specifc directory
    structure based on the pk/id of the artwork.

    Example: artwork.pk==16320, filename=='example.jpg'
    filename = 'artworks/imageOriginal/16000/16320/example.jpg'
    """

    if instance.pk:
        directory = (instance.pk // 1000) * 1000
        return f'artworks/imageOriginal/{directory}/{instance.pk}/{filename}'
    return filename


class Keyword(MPTTModel, MetaDataMixin):
    """Keywords are nodes in a fixed hierarchical taxonomy."""

    name = models.CharField(verbose_name=_('Name'), max_length=255, unique=True)
    name_en = models.CharField(
        verbose_name=_('Name, English'),
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
    getty_url = models.URLField(
        verbose_name=_('Getty id'),
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    getty_overwrite = models.BooleanField(
        default=True,
        help_text=_('Overwrite entry with data from Getty?'),
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
        return self.name

    def clean(self):
        super().clean()
        if self.getty_url:
            # Validate getty url
            validate_getty_id(self.getty_url)
            # Fetch the external metadata
            getty_data = fetch_getty_data(self.getty_url)
            self.update_with_getty_data(getty_data)

    def set_name_en_from_getty_data(self, getty_data):
        # if fetch_getty_data(self.getty_url) is not None:
        if '_label' in getty_data:
            self.name_en = getty_data['_label']

    def update_with_getty_data(self, getty_data):
        self.set_external_metadata('getty', getty_data)
        if self.getty_overwrite:
            self.set_name_en_from_getty_data(getty_data)


class Location(MPTTModel, MetaDataMixin):
    """Locations are nodes in a fixed hierarchical taxonomy."""

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
        blank=True,
        null=False,
    )
    synonyms = models.CharField(
        verbose_name=_('Synonyms'),
        blank=True,
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    gnd_id = models.CharField(max_length=16, null=True, blank=True, unique=True)
    gnd_overwrite = models.BooleanField(
        default=True,
        help_text=_('Overwrite entry with data from GND?'),
    )

    external_metadata = JSONField(null=True, blank=True, default=dict)

    class Meta:
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        try:
            ancestors = self.get_ancestors(include_self=True)
            ancestors = [i.name for i in ancestors]
        except Exception:  # TODO: this should be more specific
            ancestors = [self.name]

        return ' > '.join(ancestors[: len(ancestors) + 1])

    def clean(self):
        super().clean()
        process_external_metadata(self)

    def set_name_from_gnd_data(self, gnd_data):
        if 'preferredName' in gnd_data:
            self.name = gnd_data['preferredName']
        else:
            raise ValidationError(_('No preferredName field was found.'))

    def set_synonyms_from_gnd_data(self, gnd_data):
        if 'variantName' in gnd_data:
            self.synonyms = ', '.join(gnd_data['variantName'])
        else:
            self.synonyms = ''

    def update_with_gnd_data(self, gnd_data):
        self.set_external_metadata('gnd', gnd_data)
        if self.gnd_overwrite:
            self.set_name_from_gnd_data(gnd_data)
            self.set_synonyms_from_gnd_data(gnd_data)


class Artwork(AbstractBaseModel):
    """Each Artwork has an metadata and image and various versions (renditions)
    of that image."""

    # VersatileImageField allows to create resized versions of the
    # image (renditions) on demand
    image_original = VersatileImageField(
        verbose_name=_('Original Image'),
        max_length=255,
        null=False,
        blank=True,
        upload_to=get_path_to_original_file,
    )
    title = models.CharField(verbose_name=_('Title'), max_length=255, blank=True)
    title_english = models.CharField(
        verbose_name=_('Title, English'),
        max_length=255,
        blank=True,
    )
    title_comment = models.TextField(verbose_name=_('Comment on title'), blank=True)
    artists = models.ManyToManyField(Artist, verbose_name=_('Artists'), blank=True)
    date = models.CharField(
        verbose_name=_('Date'),
        max_length=319,
        blank=True,
        help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende/Anfang 14. Jh., 5.3.1799, ca./um/vor/nach 1700',
    )
    date_year_from = models.IntegerField(
        verbose_name=_('Date From'),
        null=True,
        blank=True,
    )
    date_year_to = models.IntegerField(verbose_name=_('Date To'), null=True, blank=True)
    material = models.TextField(  # noqa: DJ001
        verbose_name=_('Material/Technique'),
        null=True,
        blank=True,
    )
    dimensions = models.CharField(
        verbose_name=_('Dimensions'),
        max_length=255,
        blank=True,
    )
    comments = models.TextField(verbose_name=_('Comments'), blank=True)
    credits = models.TextField(verbose_name=_('Credits'), blank=True)
    keywords = models.ManyToManyField(Keyword, verbose_name=_('Keywords'), blank=True)
    place_of_production = TreeForeignKey(
        Location,
        verbose_name=_('Place of Production'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
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

    def get_short_description(self, language):
        artists = ', '.join(artist.name for artist in self.artists.all())
        title_in_language = ''
        if language == 'en':
            if self.title_english:
                title_in_language = self.title_english
        else:
            title_in_language = self.title
        parts = [artists, title_in_language, self.date]
        description = ', '.join(x.strip() for x in parts if x.strip())
        return description

    def update_search_vector(self):
        search_vector = (
            SearchVector('title', weight='A')
            + SearchVector('title_english', weight='A')
            + SearchVector(Value('artists_names'), weight='A')
            + SearchVector(Value('artists_synonyms'), weight='A')
            + SearchVector('comments', weight='B')
            + SearchVector(Value('keywords_names'), weight='B')
            + SearchVector(Value('place_of_production_names'), weight='B')
            + SearchVector(Value('place_of_production_synonyms'), weight='B')
            + SearchVector(Value('location_names'), weight='B')
            + SearchVector(Value('location_synonyms'), weight='B')
            + SearchVector('credits', weight='C')
            + SearchVector('material', weight='C')
            + SearchVector('dimensions', weight='C')
            + SearchVector('date', weight='C')
        )

        Artwork.objects.filter(pk=self.pk).annotate(
            artists_names=StringAgg('artists__name', delimiter=' '),
        ).annotate(
            artists_synonyms=StringAgg('artists__synonyms', delimiter=' '),
        ).annotate(
            keywords_names=StringAgg('keywords__name', delimiter=' '),
        ).annotate(
            place_of_production_names=StringAgg(
                'place_of_production__name',
                delimiter=' ',
            ),
        ).annotate(
            place_of_production_synonyms=StringAgg(
                'place_of_production__synonyms',
                delimiter=' ',
            ),
        ).annotate(
            location_names=StringAgg('location__name', delimiter=' '),
        ).annotate(
            location_synonyms=StringAgg('location__synonyms', delimiter=' '),
        ).update(
            search_vector=search_vector,
        )


@receiver(models.signals.post_save, sender=Artwork)
def move_uploaded_image(sender, instance, created, **kwargs):
    """Move the uploaded image after an Artwork instance has been created."""
    if created:
        imagefile = instance.image_original
        old_name = imagefile.name
        relative_path = instance.image_original.storage.get_available_name(
            get_path_to_original_file(instance, old_name),
            max_length=sender._meta.get_field('image_original').max_length,
        )
        absolute_path = settings.MEDIA_ROOT_PATH / relative_path

        if not old_name:
            return

        if not absolute_path.exists():
            absolute_path.parent.mkdir(parents=True, exist_ok=True)

        # move the uploaded image
        Path(imagefile.path).rename(absolute_path)

        imagefile.name = relative_path
        instance.save()


@receiver(models.signals.post_delete, sender=Artwork)
def delete_artwork_images(sender, instance, **kwargs):
    """Delete Artwork's originalImage and all renditions on post_delete."""
    instance.image_original.delete_all_created_images()
    instance.image_original.delete(save=False)


@receiver(models.signals.pre_save, sender=Artwork)
def delete_renditions_on_change(sender, update_fields, instance, **kwargs):
    """When the image of an Artwork gets exchanged, the old renditions get
    deleted."""
    if instance._state.adding is False:
        old_artwork = Artwork.objects.get(pk=instance.id)
        old_artwork.image_original.delete_all_created_images()


class Album(AbstractBaseModel):
    """Specific users can create their own collections of artworks."""

    id = ShortUUIDField(primary_key=True)
    archive_id = models.BigIntegerField(null=True)
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.CASCADE)
    slides = JSONField(verbose_name=_('Slides'), default=list)
    permissions = models.ManyToManyField(
        User,
        verbose_name=_('Permissions'),
        through='PermissionsRelation',
        symmetrical=False,
        related_name='permissions',
    )
    last_changed_by = models.ForeignKey(
        User,
        verbose_name=_('Last changed by'),
        related_name='last_album_changes',
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return f'{self.title} by {self.user.get_full_name()}'

    def size(self):
        return sum([len(slide) for slide in self.slides])

    class Meta:
        permissions = (('can_download_pptx', 'Can download as PowerPoint file'),)
        verbose_name = _('Album')
        verbose_name_plural = _('Albums')


def get_default_permissions():
    return settings.DEFAULT_PERMISSIONS[0]


class PermissionsRelation(models.Model):
    PERMISSION_CHOICES = tuple((p, _(p)) for p in settings.PERMISSIONS)

    album = models.ForeignKey(Album, related_name='album', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='user', on_delete=models.CASCADE)
    permissions = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default=get_default_permissions,
    )

    class Meta:
        unique_together = ['album', 'user']

    def __str__(self):
        return f'{self.user.get_full_name()} <-- {self.get_permissions_display()} --> {self.album.title}'


# Monkey patch of String representation of User
def string_representation(self):
    return self.get_full_name() or self.username


User.add_to_class('__str__', string_representation)

# Monkey patch ManyToManyDescriptor
ManyToManyDescriptor.get_queryset = lambda self: self.rel.model.objects.get_queryset()


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
        User,
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
    user = models.ForeignKey(User, related_name='rel_to_user', on_delete=models.CASCADE)
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
