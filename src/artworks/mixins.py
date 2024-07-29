from datetime import datetime


class MetaDataMixin:
    external_metadata = None

    def set_external_metadata(self, key, data):
        if self.external_metadata is not None:
            self.external_metadata[key] = {
                'date_requested': datetime.now().isoformat(),
                'response_data': data,
            }

    def delete_external_metadata(self, key):
        if self.external_metadata is not None and key in self.external_metadata:
            del self.external_metadata[key]
