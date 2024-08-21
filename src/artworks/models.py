import logging
import re
from pathlib import Path

from base_common.fields import ShortUUIDField
from base_common.models import AbstractBaseModel
from mptt.models import MPTTModel, TreeForeignKey
from versatileimagefield.fields import VersatileImageField

from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import JSONField, Value
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from django.db.models.functions import Upper
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .fetch import fetch_getty_data, fetch_gnd_data, fetch_wikidata
from .fetch.exceptions import DataNotFoundError, HTTPError, RequestError
from .managers import ArtworkManager
from .mixins import MetaDataMixin
from .validators import validate_getty_id, validate_gnd_id

logger = logging.getLogger(__name__)


def process_external_metadata(instance):
    """Process external metadata for the given instance, to avoid code
    duplication.

    It is used by both clean functions of Person and Location.
    """
    if not instance.name and not instance.gnd_id:
        raise ValidationError(
            _('Either a name or a valid %(label)s ID need to be set')
            % {'label': settings.GND_LABEL},
        )

    if instance.gnd_id:
        # Validate the gnd_id and fetch the external metadata
        validate_gnd_id(instance.gnd_id)

        # Fetch the external metadata
        try:
            gnd_data = fetch_gnd_data(instance.gnd_id)
            instance.update_with_gnd_data(gnd_data)
        except DataNotFoundError as err:
            raise ValidationError(
                {
                    'gnd_id': _('No %(label)s entry was found for %(label)s ID %(id)s.')
                    % {
                        'label': settings.GND_LABEL,
                        'id': instance.gnd_id,
                    },
                },
            ) from err
        except HTTPError as err:
            logger.warning(
                f'HTTP error {err.status_code} when retrieving {settings.GND_LABEL} data: {err.details}',
            )
            raise ValidationError(
                {
                    'gnd_id': _(
                        'HTTP error %(status_code)s when retrieving %(label)s data: %(details)s',
                    )
                    % {
                        'status_code': err.status_code,
                        'label': settings.GND_LABEL,
                        'details': err.details,
                    },
                },
            ) from err
        except RequestError as err:
            logger.warning(
                f'Request error when retrieving {settings.GND_LABEL} data. Details: {repr(err)}',
            )
            raise ValidationError(
                {
                    'gnd_id': _(
                        'Request error when retrieving %(label)s data. Details: %(error)s',
                    )
                    % {
                        'label': settings.GND_LABEL,
                        'error': repr(err),
                    },
                },
            ) from err
    elif instance.external_metadata:
        instance.delete_external_metadata('gnd')


class Person(AbstractBaseModel, MetaDataMixin):
    """A Person can fulfill several roles for 0-n artworks."""

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

    def set_birth_death_from_gnd_data(self, gnd_data):
        """Sets an Arist name, based on a GND result.

        :param dict gnd_data: GND response data for the Person
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

        :param dict gnd_data: response data of the GND API for the Person
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

        :param dict gnd_data: response data of the GND API for the Person
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
        return self.name

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

    def set_name_en_from_getty_data(self, getty_data):
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
    name_en = models.CharField(
        verbose_name=_('Name, English'),
        max_length=255,
        blank=True,
        default='',
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
            raise ValidationError(
                _(
                    'The %(label)s database does not provide a preferred name for this %(label)s ID.',
                )
                % {'label': settings.GND_LABEL},
            )

    def set_synonyms_from_gnd_data(self, gnd_data):
        if 'variantName' in gnd_data:
            self.synonyms = ', '.join(gnd_data['variantName'])
        else:
            self.synonyms = ''

    def update_with_gnd_data(self, gnd_data):
        self.set_external_metadata('gnd', gnd_data)
        simplified_wikidata_data = None
        if wikidata_link := self.get_wikidata_link(gnd_data):
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
            self.set_name_from_gnd_data(gnd_data)
            self.set_synonyms_from_gnd_data(gnd_data)
            self.name_en = ''
            if simplified_wikidata_data:
                self.set_name_en_from_wikidata(simplified_wikidata_data)

    def get_wikidata_link(self, gnd_data):
        if 'sameAs' in gnd_data:
            for concept in gnd_data['sameAs']:
                if 'wikidata' in concept['id']:
                    return concept['id']

    def set_name_en_from_wikidata(self, wikidata):
        labels = wikidata.get('labels', {})
        if 'en-gb' in labels:
            self.name_en = labels['en-gb']['value']
        elif 'en' in labels:
            self.name_en = labels['en']['value']


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
    discriminatory_terms = models.ManyToManyField(
        'DiscriminatoryTerm',
        verbose_name=_('Discriminatory terms'),
    )
    artists = models.ManyToManyField(Person, verbose_name=_('Artists'))
    photographers = models.ManyToManyField(
        Person,
        verbose_name=_('Photographers'),
        related_name='photographers',
    )
    authors = models.ManyToManyField(
        Person,
        verbose_name=_('Authors'),
        related_name='authors',
    )
    graphic_designers = models.ManyToManyField(
        Person,
        verbose_name=_('Graphic designers'),
        related_name='graphic_designers',
    )
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
    keywords = models.ManyToManyField(Keyword, verbose_name=_('Keywords'))
    link = models.URLField(verbose_name=_('Link'), blank=True)
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

    def get_discriminatory_terms_list(self):
        return [term.term for term in self.discriminatory_terms.all()]

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
