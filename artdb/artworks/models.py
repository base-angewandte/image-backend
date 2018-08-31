from django.db import models
from django.contrib.auth.models import User
from versatileimagefield.fields import VersatileImageField
from django.dispatch import receiver
from django.conf import settings
import os

class Artist(models.Model):
    name = models.CharField(max_length=255, null=False)
    synonyms = models.CharField(max_length=255, null=False, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

def get_path_to_original_file(instance, filename):
    if instance.pk:
        dirA = (instance.pk // 1000) * 1000
        return 'artworks/imageOriginal/{0}/{1}/{2}'.format(dirA, instance.pk, filename)
    return filename

class Artwork(models.Model):
    # mandatory fields
    imageOriginal = VersatileImageField(max_length = 127, null=False, blank=True, upload_to=get_path_to_original_file)

    # hidden fields
    createdAt = models.DateTimeField(auto_now_add = True)
    updatedAt = models.DateTimeField(auto_now = True, null=True)

    # optional fields
    title = models.CharField(max_length=255, blank=True)
    artists = models.ManyToManyField(Artist, blank=True)
    date = models.CharField(max_length=255, blank=True)
    dateFrom = models.DateField(null=True, blank=True)
    dateTo = models.DateField(null=True, blank=True)
    material = models.CharField(max_length=255, blank=True)
    dimensions = models.CharField(max_length=255, blank=True)
    locationOfCreation = models.CharField(max_length=255, blank= True, null=True)
    credits = models.TextField(blank=True)
    # TODO: tags

    def delete_renditions(self):
        print("deleting renditions")
        storage = self.imageOriginal.storage
        storage.delete(self.big)
        self.big.cachefile_backend.set_state(self.big, 'does_not_exist')
        storage.delete(self.thumbnail)
        self.thumbnail.cachefile_backend.set_state(self.thumbnail, 'does_not_exist')

    def __str__(self):
        return self.title

@receiver(models.signals.post_save, sender=Artwork)
def move_uploaded_image(sender, instance, created, **kwargs):
    """
    Move Artwork uploaded image after the Artwork instance has been created.  
    """
    imagefile=instance.imageOriginal
    old_name=imagefile.name
    relative_path = get_path_to_original_file(instance, old_name)
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    if created:
        if not old_name:
            return
        if not os.path.exists(absolute_path):
            os.makedirs(os.path.dirname(absolute_path), exist_ok = True)
        # move the uploaded image
        os.rename(imagefile.path, absolute_path)
        imagefile.name=relative_path
        instance.save()

@receiver(models.signals.post_delete, sender=Artwork)
def delete_Artwork_images(sender, instance, **kwargs):
    """
    Deletes Artwork originalImage and all renditions on post_delete.
    """
    instance.imageOriginal.delete_all_created_images()
    instance.imageOriginal.delete(save=False)


@receiver(models.signals.pre_save, sender=Artwork)
def delete_renditions_on_change(sender, update_fields, instance, **kwargs):
    """
    When the image of an Artwork gets exchanged, the old 
    renditions get deleted.
    """
    print("CHANGED")
    if instance._state.adding is False:
        oldArtwork = Artwork.objects.get(pk=instance.id)
        oldArtwork.imageOriginal.delete_all_created_images()
        print("not created. instance is:")
        print(instance)
        print(instance.imageOriginal)
        print(sender.imageOriginal)


# Every users can create her own collections of artworks
class ArtworkCollection(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artworks = models.ManyToManyField(Artwork, through='ArtworkCollectionMembership')
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return '{0} by {1}'.format(self.title, self.user.get_username())


class ArtworkCollectionMembership(models.Model):
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)
    collection = models.ForeignKey(ArtworkCollection, on_delete=models.CASCADE)

    def __str__(self):
        return self.artwork.title + " is part of " + self.collection.title