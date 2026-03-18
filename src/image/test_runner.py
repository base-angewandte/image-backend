from django.conf import settings
from django.test.runner import DiscoverRunner


class Runner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        if kwargs.get('top_level') is None:
            kwargs['top_level'] = settings.BASE_DIR
        super().__init__(*args, **kwargs)
