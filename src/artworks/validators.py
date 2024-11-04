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
    file_extension = Path(value.name).suffix.lower()
    valid_extensions = {}
    for extension, img_format in Image.registered_extensions().items():
        if img_format not in valid_extensions:
            valid_extensions[img_format] = []
        valid_extensions[img_format].append(extension.lower())
    try:
        img = Image.open(value)
        img.verify()
        img_format = img.format
    except UnidentifiedImageError as e:
        raise ValidationError('Uploaded file is not a valid image.') from e
    except Exception as e:
        raise ValidationError(f'Error processing image: {e}') from e
    valid_exts = valid_extensions.get(img_format, [])
    if file_extension not in valid_exts:
        valid_exts_display = ', '.join(valid_exts)
        raise ValidationError(
            f"The file extension '{file_extension}' does not match the image format '{img_format}'. "
            f'Valid extensions for this format are: {valid_exts_display}.',
        )
