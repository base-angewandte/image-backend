from django.conf import settings


class LocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        if settings.FORCE_SCRIPT_NAME:
            self.api_prefix = f'{settings.FORCE_SCRIPT_NAME}/{settings.API_PREFIX}'
        else:
            self.api_prefix = f'/{settings.API_PREFIX}'

    def __call__(self, request):
        cookie_change = None

        if request.path.startswith(self.api_prefix):
            current_set_cookie = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

            if current_set_cookie:
                accept_language_header = request.headers.get('accept-language')
                language_code = (
                    accept_language_header
                    if accept_language_header
                    else settings.LANGUAGE_CODE
                )

                if (
                    accept_language_header in settings.LANGUAGES_DICT
                    and current_set_cookie != accept_language_header
                ):
                    request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = language_code
                    cookie_change = language_code

        response = self.get_response(request)

        if cookie_change:
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                cookie_change,
                max_age=settings.LANGUAGE_COOKIE_AGE,
            )

        return response
