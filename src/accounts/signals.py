from django_cas_ng.signals import cas_user_authenticated

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.dispatch import receiver


@receiver(cas_user_authenticated, dispatch_uid='process_user_attributes')
def process_user_attributes(sender, user, created, attributes, *args, **kwargs):
    if not user or not attributes:
        return

    permissions = attributes.get('permissions')
    permissions = permissions if permissions else []

    user.is_staff = False
    user.is_superuser = False

    if user.username in settings.SUPERUSERS:
        user.is_staff = True
        user.is_superuser = True

    if 'administer_image' in permissions or 'edit_image' in permissions:
        user.is_staff = True

        editor_group, created = Group.objects.get_or_create(name=settings.EDITOR_GROUP)

        if created:
            app_labels = [
                'artworks',
                'texts',
            ]
            codenames = [
                p
                for m in (
                    'artwork',
                    'discriminatoryterm',
                    'keyword',
                    'location',
                    'material',
                    'person',
                )
                for p in (f'view_{m}', f'add_{m}', f'change_{m}', f'delete_{m}')
            ] + ['change_text']

            group_permissions = Permission.objects.filter(
                content_type__app_label__in=app_labels,
                codename__in=codenames,
            )

            editor_group.permissions.set(group_permissions)

        user.groups.add(editor_group)
    else:
        user.groups.clear()

    user.save()
