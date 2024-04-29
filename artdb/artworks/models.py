import logging
import os

from base_common.fields import ShortUUIDField
from base_common.models import AbstractBaseModel
from mptt.models import MPTTModel, TreeForeignKey
from versatileimagefield.fields import VersatileImageField

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import JSONField, Value
from django.db.models.fields.related_descriptors import ManyToManyDescriptor
from django.db.models.functions import Upper
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .managers import ArtworkManager

logger = logging.getLogger(__name__)


class Artist(models.Model):
    """One Artist can be the maker of 0-n artworks."""

    name = models.CharField(verbose_name=_('Name'), max_length=255, null=False)
    synonyms = models.CharField(
        verbose_name=_('Synonyms'), max_length=255, null=False, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Artist')
        verbose_name_plural = _('Artists')

    def __str__(self):
        return self.name


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


class Keyword(MPTTModel):
    """Keywords are nodes in a fixed hierarchical taxonomy."""

    name = models.CharField(verbose_name=_('Name'), max_length=255, unique=True)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )

    class Meta:
        verbose_name = _('Keyword')
        verbose_name_plural = _('Keywords')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class Location(MPTTModel):
    """Locations are nodes in a fixed hierarchical taxonomy."""

    name = models.CharField(verbose_name=_('Name'), max_length=255)
    synonyms = models.CharField(verbose_name=_('Synonyms'), max_length=255, blank=True)
    parent = TreeForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )

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


class Artwork(models.Model):
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
        verbose_name=_('Title, English'), max_length=255, blank=True
    )
    artists = models.ManyToManyField(Artist, verbose_name=_('Artists'), blank=True)
    date = models.CharField(
        verbose_name=_('Date'),
        max_length=319,
        blank=True,
        help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende/Anfang 14. Jh., 5.3.1799, ca./um/vor/nach 1700',
    )
    date_year_from = models.IntegerField(
        verbose_name=_('Date From'), null=True, blank=True
    )
    date_year_to = models.IntegerField(verbose_name=_('Date To'), null=True, blank=True)
    material = models.TextField(
        verbose_name=_('Material/Technique'), null=True, blank=True
    )
    dimensions = models.CharField(
        verbose_name=_('Dimensions'), max_length=255, blank=True
    )
    description = models.TextField(verbose_name=_('Descriptions'), blank=True)
    credits = models.TextField(verbose_name=_('Credits'), blank=True)
    created_at = models.DateTimeField(verbose_name=_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name=_('Updated at'), auto_now=True, null=True
    )
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
        indexes = [GinIndex(fields=['search_vector'])]

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
            + SearchVector('description', weight='B')
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
            artists_names=StringAgg('artists__name', delimiter=' ')
        ).annotate(
            artists_synonyms=StringAgg('artists__synonyms', delimiter=' ')
        ).annotate(
            keywords_names=StringAgg('keywords__name', delimiter=' ')
        ).annotate(
            place_of_production_names=StringAgg(
                'place_of_production__name',
                delimiter=' ',
            )
        ).annotate(
            place_of_production_synonyms=StringAgg(
                'place_of_production__synonyms',
                delimiter=' ',
            )
        ).annotate(
            location_names=StringAgg('location__name', delimiter=' ')
        ).annotate(
            location_synonyms=StringAgg('location__synonyms', delimiter=' ')
        ).update(
            search_vector=search_vector
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
        absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        if not old_name:
            return

        if not os.path.exists(absolute_path):
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

        # move the uploaded image
        os.rename(imagefile.path, absolute_path)

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


class Album(models.Model):
    """Specific users can create their own collections of artworks."""

    id = ShortUUIDField(primary_key=True)
    archive_id = models.BigIntegerField(null=True)
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name=_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('Updated at'), auto_now=True)
    slides = JSONField(verbose_name=_('Slides'), default=list)
    permissions = models.ManyToManyField(
        User,
        verbose_name=_('Permissions'),
        through='PermissionsRelation',
        symmetrical=False,
        related_name='permissions',
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
        verbose_name=_('Title'), max_length=255, blank=False, null=False
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
        Album, related_name='rel_to_album', on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, related_name='rel_to_user', on_delete=models.CASCADE)
    folder = models.ForeignKey(
        Folder, related_name='rel_to_folder', on_delete=models.CASCADE
    )


class DiscriminatoryTerm(models.Model):
    """Defined and extensible set of discriminatory terms that should be
    contextualised by frontend."""

    term = models.CharField(max_length=255)
