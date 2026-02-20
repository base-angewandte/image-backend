import mimetypes
import re
from contextlib import suppress
from pathlib import Path

import magic
from wand.exceptions import WandException
from wand.image import Image

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_id(id_, regex, label):
    if not re.match(regex, id_):
        raise ValidationError(_('Invalid %(label)s ID format.') % {'label': label})


def validate_gnd_id(gnd_id):
    validate_id(gnd_id, settings.GND_ID_REGEX, settings.GND_LABEL)


def validate_getty_id(getty_id):
    validate_id(getty_id, settings.GETTY_ID_REGEX, settings.GETTY_LABEL)


def validate_image_original(value):
    try:
        value.seek(0)
        mime_type = magic.from_buffer(value.read(2048), mime=True)
        value.seek(0)

        if mime_type not in settings.IM_ALLOWED_MIME_TYPES:
            raise ValidationError(
                _('Unsupported image type: {mime}.').format(mime=mime_type),
            )

        with Image(file=value) as img:
            img.size  # noqa: B018

        valid_extensions = mimetypes.guess_all_extensions(mime_type, strict=True)
        file_extension = Path(value.name).suffix.lower()

        if valid_extensions and file_extension not in valid_extensions:
            raise ValidationError(
                _(
                    "The file extension {file_extension} does not match the detected MIME type '{mime_type}'. "
                    'Valid extensions are: {valid_extensions}.',
                ).format(
                    file_extension=file_extension,
                    mime_type=mime_type,
                    valid_extensions=', '.join(valid_extensions),
                ),
            )

    except WandException as e:
        raise ValidationError('Uploaded file is not a valid image.') from e
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f'Error processing image: {e}') from e
    finally:
        with suppress(Exception):
            value.seek(0)
