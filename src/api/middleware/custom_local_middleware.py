from django.conf import settings
from django.utils.translation import activate


class CustomLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_prefix = settings.PREFIX

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith(self.api_prefix):
            accept_language = request.headers.get('accept-language')

            language_code = (
                accept_language.split(',')[0].split('-')[0].lower()
                if accept_language
                else settings.LANGUAGE_CODE
            )
            if language_code in settings.LANGUAGES_DICT:
                activate(language_code)

                response.set_cookie(
                    settings.LANGUAGE_COOKIE_NAME,
                    language_code,
                    max_age=settings.LANGUAGE_COOKIE_AGE,
                )

        return response
