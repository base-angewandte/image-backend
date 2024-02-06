from django_cas_ng.signals import cas_user_authenticated

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

    # everyone gets the user permission to download pptx files
    permission_to_download = Permission.objects.get(codename='can_download_pptx')
    user.user_permissions.add(permission_to_download)

    if 'administer_image' in permissions:
        user.is_staff = True
        user.is_superuser = True

    if 'edit_image' in permissions:
        user.is_staff = True

        editor_group = Group.objects.get(name='editor')
        user.groups.add(editor_group)
    else:
        user.groups.clear()

    user.save()
