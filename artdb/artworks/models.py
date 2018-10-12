import os
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.conf import settings
from versatileimagefield.fields import VersatileImageField


class Artist(models.Model):
    """
    One Artist can be the maker of 0-n artworks.
    """
    name = models.CharField(max_length=255, null=False)
    synonyms = models.CharField(max_length=255, null=False, blank=True)

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


class Artwork(models.Model):
    """
    Each Artwork has an metadata and image and various versions (renditions) of that image.
    """
    # VersatileImageField allows to create resized versions of the
    # image (renditions) on demand
    imageOriginal = VersatileImageField(max_length = 127, null=False, blank=True, upload_to=get_path_to_original_file)
    title = models.CharField(max_length=255, blank=True)
    titleEnglish = models.CharField(max_length=255, blank=True)
    artists = models.ManyToManyField(Artist, blank=True)
    date = models.CharField(max_length=255, blank=True, help_text='1921-1923, 1917/1964, -20000, 2.Jh. - 4.Jh., Ende 14. Jh., 5.3.1799, um 1700')
    dateYearFrom = models.IntegerField(null=True, blank=True)
    dateYearTo = models.IntegerField(null=True, blank=True)
    material = models.CharField(max_length=255, blank=True)
    dimensions = models.CharField(max_length=255, blank=True)
    locationOfCreation = models.CharField(max_length=255, blank= True, null=True)
    credits = models.TextField(blank=True)
    # TODO: tags
    createdAt = models.DateTimeField(auto_now_add = True)
    updatedAt = models.DateTimeField(auto_now = True, null=True)

    def __str__(self):
        return self.title


@receiver(models.signals.post_save, sender=Artwork)
def move_uploaded_image(sender, instance, created, **kwargs):
    """
    Move the uploaded image after an Artwork instance has been created.  
    """
    imagefile = instance.imageOriginal
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
    instance.imageOriginal.delete_all_created_images()
    instance.imageOriginal.delete(save=False)


@receiver(models.signals.pre_save, sender=Artwork)
def delete_renditions_on_change(sender, update_fields, instance, **kwargs):
    """
    When the image of an Artwork gets exchanged, the old renditions get deleted.
    """
    if instance._state.adding is False:
        old_artwork = Artwork.objects.get(pk=instance.id)
        old_artwork.imageOriginal.delete_all_created_images()


class ArtworkCollection(models.Model):
    """
    Specific users can create collections of artworks.
    """
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artworks = models.ManyToManyField(Artwork, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0} by {1}'.format(self.title, self.user.get_username())
        
    def size(self):
        return self.artworks.count()