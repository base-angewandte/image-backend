from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        from base_common_drf.openapi.authentication import SessionScheme  # noqa: F401
