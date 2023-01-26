import json
from collections import OrderedDict

import jsonschema
from drf_yasg import openapi
from jsonschema import validate
from rest_framework import serializers

from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from core.utils import placeholder_lazy
from user_preferences.models import UserPreferencesData, UserSettingsValue

from . import CleanModelSerializer, SwaggerMetaModelSerializer


def validate_json_field(value, schema):
    try:
        if not isinstance(value, list):
            value = [value]

        for v in value:
            validate(v, schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValidationError(_(f'Well-formed but invalid JSON: {e}')) from e
    except json.decoder.JSONDecodeError as e:
        raise ValidationError(_(f'Poorly-formed text, not JSON: {e}')) from e
    except TypeError as e:
        raise ValidationError(f'Invalid characters: {e}') from e

    if len(value) > len({json.dumps(d, sort_keys=True) for d in value}):
        raise ValidationError(_('Data contains duplicate entries'))

    return value


class SkillsField(serializers.JSONField):
    class Meta:
        swagger_schema_fields = {
            'type': openapi.TYPE_ARRAY,
            'properties': {},
            'items': openapi.Items(
                type=openapi.TYPE_OBJECT,
                properties={
                    'label': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'fr': openapi.Schema(
                                type=openapi.TYPE_STRING,
                            ),
                            'en': openapi.Schema(
                                type=openapi.TYPE_STRING,
                            ),
                            'de': openapi.Schema(
                                type=openapi.TYPE_STRING,
                            ),
                        },
                        additionalProperties=False,
                    ),
                    'source': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        }


class UserPreferencesDataSerializer(CleanModelSerializer, SwaggerMetaModelSerializer):
    date_created = serializers.DateField(read_only=True)
    date_changed = serializers.DateField(read_only=True)
    complementary_email = serializers.CharField(
        label=_('E-Mail (complementary)'),
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    website = serializers.URLField(
        label=_('Website'),
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    expertise = SkillsField(
        label=_('Skills and Expertise'),
        required=False,
        allow_null=True,
        default=None,
    )

    def validate_skills(self, value):
        schema = {
            'additionalProperties': False,
            'type': 'object',
            'properties': {
                'label': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'fr': {'type': 'string'},
                        'en': {'type': 'string'},
                        'de': {'type': 'string'},
                        'additionalProperties': False,
                    },
                },
                'source': {'type': 'string'},
                'source_name': {'type': 'string'},
                'additionalProperties': False,
            },
        }

        return validate_json_field(value, schema)

    class Meta:
        model = UserPreferencesData
        fields = (
            'expertise',
            'complementary_email',
            'website',
            'date_created',
            'date_changed',
        )

        swagger_meta_attrs = {
            'date_created': OrderedDict([('hidden', True)]),
            'date_changed': OrderedDict([('hidden', True)]),
            'expertise': OrderedDict(
                [
                    ('field_type', 'chips'),
                    (
                        'operationId',
                        'autosuggest_v1_lookup',
                    ),
                    (
                        'source',
                        reverse_lazy(
                            'lookup_all',
                            kwargs={'version': 'v1', 'fieldname': 'expertise'},
                        ),
                    ),
                    ('prefetch', ['source']),
                    ('order', 1),
                    ('allow_unknown_entries', False),
                    (
                        'dynamic_autosuggest',
                        True,
                    ),
                    (
                        'set_label_language',
                        True,
                    ),
                    (
                        'sortable',
                        True,
                    ),
                    ('placeholder', placeholder_lazy(_('Skills and Expertise'))),
                ]
            ),
            'complementary_email': OrderedDict(
                [
                    ('order', 2),
                    ('placeholder', placeholder_lazy(_('E-Mail (complementary)'))),
                ]
            ),
            'website': OrderedDict(
                [('order', 3), ('placeholder', placeholder_lazy(_('Website')))]
            ),
        }


class DataField(serializers.JSONField):
    pass


class UserSettingsSerializer(CleanModelSerializer, SwaggerMetaModelSerializer):
    data = DataField(required=False)

    def validate_data(self, value):
        schema = {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'id': {'type': 'string'},
                'value': {'type': 'string'},
                'title': {'type': 'string'},
                'type': {'type': 'string'},
                'x-attrs': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'field_type': {'type': 'string'},
                    },
                },
            },
        }

        return validate_json_field(value, schema)

    class Meta:
        model = UserSettingsValue
        fields = ('data',)


class ProfileField(serializers.JSONField):
    class Meta:
        swagger_schema_fields = {
            'type': openapi.TYPE_ARRAY,
            'items': openapi.Items(
                type=openapi.TYPE_OBJECT,
                properties={
                    'label': openapi.Schema(type=openapi.TYPE_STRING),
                    'value': openapi.Schema(type=openapi.TYPE_STRING),
                    'url': openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        }


class UserSerializer(CleanModelSerializer, SwaggerMetaModelSerializer):
    id = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    permissions = serializers.ListField(child=serializers.CharField(), required=False)
    space = serializers.IntegerField(required=False)
    profile = ProfileField()

    class Meta:
        model = UserPreferencesData
        fields = ('id', 'name', 'email', 'permissions', 'space', 'profile')

    swagger_meta_attrs = {
        'id': OrderedDict([('hidden', True)]),
        'name': OrderedDict([('hidden', True)]),
        'email': OrderedDict([('hidden', True)]),
        'permissions': OrderedDict([('hidden', True)]),
        'space': OrderedDict([('hidden', True)]),
    }


class UserImageSerializer(CleanModelSerializer, SwaggerMetaModelSerializer):
    user_image = serializers.ImageField()

    class Meta:
        model = UserPreferencesData
        fields = ('user_image',)
