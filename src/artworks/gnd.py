import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .fetch import fetch_gnd_data
from .fetch.exceptions import DataNotFoundError, HTTPError, RequestError
from .validators import validate_gnd_id

logger = logging.getLogger(__name__)


def construct_individual_name(gnd_name_information):
    """Helper function to construct name from GND name information.

    :param gnd_name_information: GND name information
    :return: Constructed name
    """
    name_parts = []

    if 'nameAddition' in gnd_name_information:
        name_parts.append(gnd_name_information['nameAddition'][0])

    if 'personalName' in gnd_name_information:
        if 'prefix' in gnd_name_information:
            name_parts.append(gnd_name_information['prefix'][0])
        name_parts.append(gnd_name_information['personalName'][0])
    else:
        if 'forename' in gnd_name_information:
            name_parts.append(gnd_name_information['forename'][0])
        if 'prefix' in gnd_name_information:
            name_parts.append(gnd_name_information['prefix'][0])
        if 'surname' in gnd_name_information:
            name_parts.append(gnd_name_information['surname'][0])

    return ' '.join(name_parts).strip()


def add_preferred_name_to_synonyms(instance, gnd_data):
    if (
        'preferredName' in gnd_data
        and gnd_data['preferredName'] not in instance.synonyms
    ):
        instance.synonyms.insert(0, gnd_data['preferredName'])


def process_external_metadata(instance):
    """Process external metadata for the given instance, to avoid code
    duplication.

    It is used by both clean functions of Person and Location.
    """
    if not instance.name and not instance.gnd_id:
        raise ValidationError(
            _('Either a name or a valid %(label)s ID need to be set')
            % {'label': settings.GND_LABEL},
        )

    if instance.gnd_id:
        # Validate the gnd_id and fetch the external metadata
        validate_gnd_id(instance.gnd_id)

        # Fetch the external metadata
        try:
            gnd_data = fetch_gnd_data(instance.gnd_id)
            instance.update_with_gnd_data(gnd_data)
        except DataNotFoundError as err:
            raise ValidationError(
                {
                    'gnd_id': _('No %(label)s entry was found for %(label)s ID %(id)s.')
                    % {
                        'label': settings.GND_LABEL,
                        'id': instance.gnd_id,
                    },
                },
            ) from err
        except HTTPError as err:
            logger.warning(
                f'HTTP error {err.status_code} when retrieving {settings.GND_LABEL} data: {err.details}',
            )
            raise ValidationError(
                {
                    'gnd_id': _(
                        'HTTP error %(status_code)s when retrieving %(label)s data: %(details)s',
                    )
                    % {
                        'status_code': err.status_code,
                        'label': settings.GND_LABEL,
                        'details': err.details,
                    },
                },
            ) from err
        except RequestError as err:
            logger.warning(
                f'Request error when retrieving {settings.GND_LABEL} data. Details: {repr(err)}',
            )
            raise ValidationError(
                {
                    'gnd_id': _(
                        'Request error when retrieving %(label)s data. Details: %(error)s',
                    )
                    % {
                        'label': settings.GND_LABEL,
                        'error': repr(err),
                    },
                },
            ) from err
    elif instance.external_metadata:
        instance.delete_external_metadata('gnd')
