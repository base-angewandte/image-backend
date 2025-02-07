from django.conf import settings


class LanguageHeaderMiddleware:
    """A custom middleware implementation that overwrites the language cookie.

    Overwriting takes place for requests made by the API and when the
    Language Header differs from the cookie set in the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        force_script_name = getattr(settings, 'FORCE_SCRIPT_NAME', '')
        api_prefix = getattr(settings, 'API_PREFIX', 'api/')

        self.api_prefix = f'{force_script_name}/{api_prefix}'

    def __call__(self, request):
        language_cookie = None

        if request.path.startswith(self.api_prefix) and (
            request_cookie := request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        ):
            accept_language_header = request.headers.get('accept-language')

            if (
                accept_language_header in settings.LANGUAGES_DICT
                and request_cookie != accept_language_header
            ):
                request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = accept_language_header
                language_cookie = accept_language_header

        response = self.get_response(request)

        if language_cookie:
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                language_cookie,
                max_age=settings.LANGUAGE_COOKIE_AGE,
            )

        return response
