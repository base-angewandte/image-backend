from datetime import datetime


class MetaDataMixin:
    external_metadata = None

    def set_external_metadata(self, key, data):
        if self.external_metadata is not None:
            self.external_metadata[key] = {
                'date_requested': datetime.now().isoformat(),
                'response_data': data,
            }
