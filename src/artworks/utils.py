from django.conf import settings


def remove_non_printable_characters(value: str):
    if value and not value.isprintable():
        return ''.join(ch for ch in value if ch.isprintable())
    return value


def media_url_to_file_path(instance, url: str):
    """Derive local filesystem path from a response URL."""

    client_hostname = instance.client._base_environ()['SERVER_NAME']
    media_path = url.split(
        f'{client_hostname}{settings.MEDIA_URL}',
    )[1]
    return f'{settings.MEDIA_ROOT}/{media_path}'
