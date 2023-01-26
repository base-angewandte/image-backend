from rest_framework import routers

from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from . import views

router = routers.DefaultRouter()


urlpatterns = [
    # ...
    # API Schema:
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
        # ...
    # already here
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$', views.no_ui_view, name='schema-json'
    ),
    path('swagger/', views.swagger_view, name='schema-swagger-ui'),
]
#
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
