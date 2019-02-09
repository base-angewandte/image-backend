import os
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.conf import settings
from versatileimagefield.fields import VersatileImageField
from mptt.models import MPTTModel, TreeForeignKey
from ordered_model.models import OrderedModel

class Artist(models.Model):
    """
    One Artist can be the maker of 0-n artworks.
    """
    name = models.CharField(max_length=255, null=False)
    synonyms = models.CharField(max_length=255, null=False, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


def get_path_to_original_file(instance, filename):
    """
    The uploaded images of artworks are stored in a specifc directory structure
    based on the pk/id of the artwork.
    Example: artwork.pk==16320, filename=='example.jpg'
    filename = 'artworks/imageOriginal/16000/16320/example.jpg'
    """
    if instance.pk:
        directory = (instance.pk // 1000) * 1000
        return 'artworks/imageOriginal/{0}/{1}/{2}'.format(directory, instance.pk, filename)
    return filename


class Keyword(MPTTModel):
    """
    Keywords are nodes in a fixed hierarchical taxonomy.
    """
    name = models.CharField(max_length=255, unique=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']


class Location(MPTTModel):
    """
    Locations are nodes in a fixed hierarchical taxonomy.
    """
    name = models.CharField(max_length=255)
    synonyms = models.CharField(max_length=255, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']


class Artwork(models.Model):
    """
    Each Artwork has an metadata and image and various versions (renditions) of that image.
    """
    # VersatileImageField allows to create resized versions of the
    # image (renditions) on demand
    image_original = VersatileImageField(max_length = 127, null=False, blank=True, upload_to=get_path_to_original_file)
    title = models.CharField(max_length=255, blank=True)
    title_english = models.CharField(max_length=255, blank=True)
    artists = models.ManyToManyField(Artist, blank=True)
    date = models.CharField(max_length=319, blank=True, help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende/Anfang 14. Jh., 5.3.1799, ca./um/vor/nach 1700')
    date_year_from = models.IntegerField(null=True, blank=True)
    date_year_to = models.IntegerField(null=True, blank=True)
    material = models.TextField(null=True, blank=True)
    dimensions = models.CharField(max_length=255, blank=True)
    credits = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True, null=True)
    keywords = models.ManyToManyField(Keyword, blank=True)
    location_of_creation = TreeForeignKey(Location, blank=True, null=True, on_delete=models.SET_NULL, related_name='artworks_created_here')
    location_current = TreeForeignKey(Location, blank=True, null=True, on_delete=models.SET_NULL, related_name='artworks_currently_located_here')
    checked = models.BooleanField(default=False)
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_description(self, language):
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


@receiver(models.signals.post_save, sender=Artwork)
def move_uploaded_image(sender, instance, created, **kwargs):
    """
    Move the uploaded image after an Artwork instance has been created.  
    """
    imagefile = instance.image_original
    old_name = imagefile.name
    relative_path = get_path_to_original_file(instance, old_name)
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    if created:
        if not old_name:
            return
        if not os.path.exists(absolute_path):
            os.makedirs(os.path.dirname(absolute_path), exist_ok = True)
        # move the uploaded image
        os.rename(imagefile.path, absolute_path)
        imagefile.name = relative_path
        instance.save()


@receiver(models.signals.post_delete, sender=Artwork)
def delete_artwork_images(sender, instance, **kwargs):
    """
    Delete Artwork's originalImage and all renditions on post_delete.
    """
    instance.image_original.delete_all_created_images()
    instance.image_original.delete(save=False)


@receiver(models.signals.pre_save, sender=Artwork)
def delete_renditions_on_change(sender, update_fields, instance, **kwargs):
    """
    When the image of an Artwork gets exchanged, the old renditions get deleted.
    """
    if instance._state.adding is False:
        old_artwork = Artwork.objects.get(pk=instance.id)
        old_artwork.image_original.delete_all_created_images()


class ArtworkCollection(models.Model):
    """
    Specific users can create collections of artworks.
    """
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artworks = models.ManyToManyField(Artwork, through='ArtworkCollectionMembership')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0} by {1}'.format(self.title, self.user.get_username())
        
    def size(self):
        return self.artworks.count()
    
    class Meta:
        permissions = (('can_download_pptx', 'Can download as PowerPoint file'),)


class ArtworkCollectionMembership(OrderedModel):
    collection = models.ForeignKey(ArtworkCollection, on_delete=models.CASCADE)
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)
    order_with_respect_to = 'collection'
    connected_with = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def move_left(self):
        # did the user click a single one or a connected one?
        if self.connected_with:
            if (self.connected_with == self.previous()):
                # right side
                left_side = self.previous()
                right_side = self
            else:
                # left side
                left_side = self
                right_side = self.next()
        else:
            left_side = self
            right_side = None
           
        if left_side.previous():
            if left_side.previous().connected_with:
                # the left_side is connected. let's move twice
                left_side.up()
                if right_side:
                    right_side.up()
            left_side.up()
            if right_side:
                right_side.up()


    def move_right(self):
        # did the user click a single one or a connected one?
        if self.connected_with:
            if (self.connected_with == self.previous()):
                # right side
                left_side = self.previous()
                right_side = self
            else:
                # left side
                left_side = self
                right_side = self.next()
        else:
            left_side = None
            right_side = self
           
        if right_side.next():
            if right_side.next().connected_with:
                # the rightSide is connected. let's move twice
                right_side.down()
                if left_side:
                    left_side.down()
            right_side.down()
            if left_side:
                left_side.down()


    def disconnect(self, partner):
        if (self.connected_with == partner) and (self == partner.connected_with):
            self.connected_with = None
            partner.connected_with = None
            self.save()
            partner.save()
            return True
        return False


    def connect(self, partner):
        if (self.connected_with == None) and (partner.connected_with == None):
            self.connected_with = partner
            partner.connected_with = self
            self.save()
            partner.save()
            return True
        return False
        

    class Meta:
        ordering = ('collection', 'order')