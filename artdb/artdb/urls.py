"""artdb URL Configuration

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
from django.contrib import admin
from django.urls import path, include

# adding this, so MEDIA dir can be served during development 
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('artworks.urls')),
    path('admin/', include("massadmin.urls")),

    path(r'accounts/login/', django_cas_ng.views.login, name='cas_ng_login'),
    path(r'accounts/logout/', django_cas_ng.views.logout, name='cas_ng_logout'),
    path(r'accounts/callback/', django_cas_ng.views.callback, name='cas_ng_proxy_callback'),

    path('i18n/', include('django.conf.urls.i18n')),
]

# adding this, so MEDIA dir can be served during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # django debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
