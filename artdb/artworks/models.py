from django.db import models
from django.contrib.auth.models import User
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


class Artist(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name


class Artwork(models.Model):
    # mandatory fields
    imageOriginal = models.ImageField(max_length = 127, null=False, blank=True)

    # hidden fields
    createdAt = models.DateTimeField(auto_now_add = True)
    updatedAt = models.DateTimeField(auto_now = True, null=True)

    # hidden, auto-filled fields
    # fileID = models.IntegerField(null=False, blank=False, default=0)

    # optional fields
    title = models.CharField(max_length=255, blank=True)
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.CharField(max_length=255, blank=True)
    dateFrom = models.DateField(null=True, blank=True)
    dateTo = models.DateField(null=True, blank=True)
    material = models.CharField(max_length=255, blank=True)
    dimensions = models.CharField(max_length=255, blank=True)
    locationOfCreation = models.CharField(max_length=255, null=True)
    credits = models.TextField(blank=True)
    # TODO: tags

    # shrinked versions of the original image are created using django-imagekit
    # imagekit uses Pillow
    thumbnail = ImageSpecField(source='imageOriginal',
                processors=[ResizeToFit(180, 180)],
                format='JPEG',
                options={'quality': 80})
    big = ImageSpecField(source='imageOriginal',
                processors=[ResizeToFit(930, 768)],
                format='JPEG',
                options={'quality': 92})

    def get_path_to_original_file(self):
        print("getpath ")
        return 'artworks/imageOriginal/{0}/{1}'.format(self.pk, self.imageOriginal.name)

    def save(self, *args, **kwargs):
        # call save to create a primary key. See: https://stackoverflow.com/questions/651949
        super(Artwork, self).save( *args, **kwargs )
        imageOriginal = self.imageOriginal
        if imageOriginal:
            oldPath = self.imageOriginal.name
            print(oldPath)
            newPath = self.get_path_to_original_file()
            print(newPath)
            self.imageOriginal.storage.save(newPath, imageOriginal)
            self.imageOriginal.name = newPath
            #self.imageOriginal.close()
            self.imageOriginal.storage.delete(oldPath)
            print("saving")
        super( Artwork, self ).save( *args, **kwargs )

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