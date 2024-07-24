from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        *UserAdmin.fieldsets,
        (_('Additional info'), {'fields': ('tos_accepted',)}),
    )
    list_display = (
        *UserAdmin.list_display,
        'tos_accepted',
    )
