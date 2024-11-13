from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from ..models import Artwork
from .forms import ImageFieldForm


class MultiArtworkCreationFormView(PermissionRequiredMixin, FormView):
    form_class = ImageFieldForm
    template_name = 'admin/artworks/upload.html'
    success_url = reverse_lazy('admin:artworks_artwork_changelist')
    permission_required = ['artworks.add_artwork']

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        files = form.cleaned_data['image_field']
        for f in files:
            Artwork(
                title=f.name,
                image_original=f,
                published=False,
                checked=False,
            ).save()
        messages.success(self.request, _('Images successfully uploaded'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add the title to the context data."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Upload multiple images')
        return context
