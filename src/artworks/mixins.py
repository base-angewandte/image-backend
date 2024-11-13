from datetime import datetime

from django.conf import settings
from django.utils.translation import get_language


class MetaDataMixin:
    external_metadata = None

    def get_external_metadata_response_data(self, key):
        if self.external_metadata is not None:
            return self.external_metadata.get(key, {}).get('response_data')

    def set_external_metadata(self, key, data):
        if self.external_metadata is not None:
            self.external_metadata[key] = {
                'date_requested': datetime.now().isoformat(),
                'response_data': data,
            }

    def delete_external_metadata(self, key):
        if self.external_metadata is not None and key in self.external_metadata:
            del self.external_metadata[key]


class LocalizationMixin:
    def get_localized_property(self, property_name):
        """Get localized property.

        It returns the localized property if a property with _language
        appendix exists, and it is set. As a fallback it tries every
        other configured language in the order defined in the
        settings.LANGUAGES variable.
        """

        current_language = get_language() or settings.LANGUAGE_CODE

        available_languages = list(settings.LANGUAGES_DICT.keys())
        available_languages.remove(current_language)

        languages = [current_language, *available_languages]

        for lang in languages:
            properties = [f'{property_name}_{lang}']
            if lang == 'de':
                properties.append(f'{property_name}')

            for prop in properties:
                if hasattr(self, prop) and getattr(self, prop):
                    return getattr(self, prop)

        return ''
