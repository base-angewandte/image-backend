"""Artdb URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import django_cas_ng.views

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

admin.site.login = login_required(admin.site.login)
admin.site.index_title = settings.DJANGO_ADMIN_TITLE
admin.site.site_header = settings.DJANGO_ADMIN_TITLE
admin.site.site_title = settings.DJANGO_ADMIN_TITLE
admin.site.site_url = None

urlpatterns = [
    # index
    path(
        '',
        RedirectView.as_view(url=reverse_lazy('schema-docs', kwargs={'version': 'v1'})),
        name='index',
    ),
    # api
    path('api/', include('api.urls')),
    # django admin
    path(f'{settings.DJANGO_ADMIN_PATH}/', include('artworks.admin.urls')),
    path(f'{settings.DJANGO_ADMIN_PATH}/', admin.site.urls),
    path(f'{settings.DJANGO_ADMIN_PATH}/', include('massadmin.urls')),
    # django cas ng
    path(
        r'accounts/login/',
        django_cas_ng.views.LoginView.as_view(),
        name='cas_ng_login',
    ),
    path(
        r'accounts/logout/',
        django_cas_ng.views.LogoutView.as_view(),
        name='cas_ng_logout',
    ),
    path(
        r'accounts/callback/',
        django_cas_ng.views.CallbackView.as_view(),
        name='cas_ng_proxy_callback',
    ),
    # i18n
    path('i18n/', include('django.conf.urls.i18n')),
    # tinymce
    path('tinymce/', include('tinymce.urls')),
]

# adding this, so static and media files can be served during development
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
