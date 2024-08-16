import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_gnd_id(gnd_id):
    if not re.match(
        settings.GND_ID_REGEX,
        gnd_id,
    ):
        raise ValidationError(_('Invalid GND ID format.'))


def validate_getty_id(getty_id):
    if not re.match(
        settings.GETTY_ID_REGEX,
        getty_id,
    ):
        raise ValidationError(_('Invalid Getty AAT ID format.'))
