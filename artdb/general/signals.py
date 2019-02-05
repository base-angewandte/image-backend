from django.conf import settings
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.dispatch import receiver

from django_cas_ng.signals import cas_user_authenticated


@receiver(cas_user_authenticated, dispatch_uid="process_user_attributes")
def process_user_attributes(sender, user, created, attributes, *args, **kwargs):
    if not user or not attributes:
        return

    if user.username in settings.SUPERUSERS:
        user.is_staff = True
        user.is_superuser = True
    else:
        user.is_superuser = False

        permissions = attributes.get('permissions')

        # TODO
        if permissions and 'edit_image' in permissions.split(','):
            user.is_staff = True
            # p = Permission.objects.filter().exclude()
            # user.user_permissions.set(p)
        else:
            user.is_staff = False
            # user.user_permissions.clear()

    user.save()
