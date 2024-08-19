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

# adding this, so MEDIA dir can be served during development
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

js_info_dict = {'packages': ('languages',)}

admin.site.login = login_required(admin.site.login)
admin.site.index_title = _('Image Admin')
admin.site.site_header = _('Image Admin')

urlpatterns = [
    path('api/', include('api.urls')),
    # django admin
    path('editing/', include('artworks.admin.urls')),
    path('editing/', admin.site.urls),
    path('editing/', include('massadmin.urls')),
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
    path('i18n/', include('django.conf.urls.i18n')),
]

# adding this, so MEDIA dir can be served during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
