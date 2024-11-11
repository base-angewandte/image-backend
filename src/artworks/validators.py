import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError

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
        img = Image.open(value)
        img.verify()
        img_format = img.format
    except UnidentifiedImageError as e:
        raise ValidationError('Uploaded file is not a valid image.') from e
    except Exception as e:
        raise ValidationError(f'Error processing image: {e}') from e

    valid_extensions = settings.PIL_VALID_EXTENSIONS.get(img_format, [])
    file_extension = Path(value.name).suffix.lower()

    if file_extension not in valid_extensions:
        raise ValidationError(
            _(
                "The file extension %(file_extension)s does not match the image format '%(img_format)'. "
                'Valid extensions are: %(valid_extensions)s.',
            )
            % {
                'file_extension': file_extension,
                'img_format': img_format,
                'valid_extensions': ', '.join(valid_extensions),
            },
        )
