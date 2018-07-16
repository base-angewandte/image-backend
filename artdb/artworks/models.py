from django.db import models
from django.contrib.auth.models import User
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


class Artist(models.Model):
    firstname = models.CharField(max_length=255)
    surname = models.CharField(max_length=255)
    def __str__(self):
        return '{0} by {1}'.format(self.firstname, self.surname)


class Artwork(models.Model):
    # mandatory fields
    title = models.CharField(max_length=255)
    original = models.ImageField(max_length = 127, upload_to='artworks/original/', null=False, blank=True)

    # hidden fields
    createdAt = models.DateTimeField(auto_now_add = True)
    updatedAt = models.DateTimeField(auto_now = True)

    # optional fields
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.CharField(max_length=255, blank=True)
    dateFrom = models.DateField(null=True, blank=True)
    dateTo = models.DateField(null=True, blank=True)
    material = models.CharField(max_length=255, blank=True)
    dimensions = models.CharField(max_length=255,blank=True)
    locationOfCreation = models.CharField(max_length=255, blank=True)
    credits = models.TextField(blank=True)
    # TODO: tags

    # shrinked versions of the original image are crated using django-imagekit
    # imagekit uses Pillow
    thumbnail = ImageSpecField(source='original',
                processors=[ResizeToFit(180, 180)],
                format='JPEG',
                options={'quality': 80})
    big = ImageSpecField(source='original',
                processors=[ResizeToFit(930, 768)],
                format='JPEG',
                options={'quality': 92})
                            
    def __str__(self):
        return self.title


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