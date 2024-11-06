from django.contrib import admin

from .models import Text


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'date_created',
        'date_changed',
    )
    search_fields = ('title', 'de', 'en')
    readonly_fields = ('date_created', 'date_changed')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
