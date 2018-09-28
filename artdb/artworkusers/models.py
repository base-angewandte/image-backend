from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete="models.CASCADE")

    def __str__(self):
        # TODO: only a stub
        return 'profile'


@receiver(post_save, sender=User)
def user_is_created(sender, instance, created, **kwargs):
    """
    Automatically create a Profile when a User is created.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        # user object gets saved/update after the profile has been changed
        instance.profile.save()