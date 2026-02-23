import mimetypes
import re
from pathlib import Path

import magic
from sorl.thumbnail import default

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
    # don't catch exception, this should never happen, and if it does, it
    # should be logged
    seek = value.seek
    # make sure the FP is pointing to the start of the file
    seek(0)
    mime_type = magic.from_buffer(value.read(2048), mime=True)
    # reset FP after read for mime_type
    seek(0)
    if mime_type not in settings.IM_ALLOWED_MIME_TYPES:
        raise ValidationError(
            _('Unsupported image type: %(mime).') % {'mime': mime_type},
        )
    # we aren't using sorl-thumbnail's ImageField, but Django's built-in one.
    # so we need to perform this step manually
    ivi = default.engine.is_valid_image(value.read())
    # reset FP after getting image data for validation
    seek(0)
    if not ivi:
        raise ValidationError('Uploaded file is not a valid image.')

    valid_extensions = mimetypes.guess_all_extensions(mime_type, strict=True)
    file_extension = Path(value.name).suffix.lower()

    if valid_extensions and file_extension not in valid_extensions:
        raise ValidationError(
            _(
                "The file extension %(file_extension) does not match the detected MIME type '%(mime_type)'. "
                'Valid extensions are: %(valid_extensions).',
            )
            % {
                'file_extension': file_extension,
                'mime_type': mime_type,
                'valid_extensions': ', '.join(valid_extensions),
            },
        )
