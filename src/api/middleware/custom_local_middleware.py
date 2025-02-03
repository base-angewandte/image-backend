from django.conf import settings
from django.utils.translation import activate


class CustomLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_prefix = '/api/'

    def __call__(self, request):
        if request.path.startswith(self.api_prefix):
            accept_language = request.headers.get('accept-language')

            language_code = (
                accept_language.split(',')[0].split('-')[0].lower()
                if accept_language
                else settings.LANGUAGE_CODE
            )
            if language_code in settings.LANGUAGES_DICT:
                activate(language_code)
                request.LANGUAGE_CODE = language_code

        response = self.get_response(request)

        # Set the language cookie based on the chosen language
        if request.path.startswith(self.api_prefix):
            language_code = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
            response.set_cookie(
                'django_language',
                language_code,
                max_age=31536000,  # for one year
            )

        return response
