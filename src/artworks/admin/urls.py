from django.urls import path

from .views import MultiArtworkCreationFormView

urlpatterns = [
    path(
        'multi-artwork-creation/',
        MultiArtworkCreationFormView.as_view(),
        name='multi-artwork-creation',
    ),
]
