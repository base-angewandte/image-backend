from base_common_drf import openapi


class AutoSchema(openapi.AutoSchema):
    def _process_override_parameters(self, direction='request'):
        # TODO: this should be refactored to base_common_drf.openapi.AutoSchema
        #   once we tested and adapted it to our general needs.
        #   we also need to adapt the docs accordingly for the exclude_language_header in ViewSets
        result = super()._process_override_parameters(direction)
        if hasattr(self.view, 'exclude_language_header'):
            for exclude in self.view.exclude_language_header:
                if (
                    exclude[0] in self.view.action_map
                    and self.view.action_map[exclude[0]] == exclude[1]
                ):
                    result.pop(('Accept-Language', 'header'))
        return result
