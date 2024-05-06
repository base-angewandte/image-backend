from artworks.models import Artwork, PermissionsRelation
from rest_framework.exceptions import NotFound, ParseError

from django.utils.translation import gettext_lazy as _


def check_limit(limit):
    try:
        limit = int(limit)
        if limit <= 0:
            raise ValueError
    except ValueError as e:
        raise ParseError(_('limit must be a positive integer')) from e

    return limit


def check_offset(offset):
    try:
        offset = int(offset)
        if offset < 0:
            raise ParseError(_('negative offset is not allowed'))
    except ValueError as e:
        raise ParseError(_('offset must be an integer')) from e

    return offset


def check_sorting(sorting, ordering_fields):
    try:
        sorting = str(sorting)
        if sorting not in ordering_fields + [f'-{i}' for i in ordering_fields]:
            raise ParseError(_(f'sorting should be {ordering_fields}'))
    except ValueError as e:
        raise ParseError(_('sorting must be a string')) from e

    return sorting


def slides_with_details(album, request):
    ret = []
    for slide in album.slides:
        slide_info = []
        for artwork in slide:
            try:
                artwork = Artwork.objects.get(id=artwork.get('id'))
            except Artwork.DoesNotExist as dne:
                raise NotFound(_('Artwork does not exist')) from dne

            slide_info.append(
                {
                    'id': artwork.id,
                    'image_original': request.build_absolute_uri(
                        artwork.image_original.url
                    )
                    if artwork.image_original
                    else None,
                    'title': artwork.title,
                    'credits': artwork.credits,
                    'date': artwork.date,
                    'artists': [
                        {
                            'id': artist.id,
                            'value': artist.name,
                        }
                        for artist in artwork.artists.all()
                    ],
                }
            )
        ret.append(slide_info)

    return ret


def featured_artworks(album, request, num_artworks=4):
    artworks = []

    for slide in album.slides:
        for item in slide:
            try:
                artwork = Artwork.objects.get(id=item['id'])
            except Artwork.DoesNotExist as dne:
                raise NotFound(_('Artwork does not exist')) from dne

            artworks.append(
                {
                    'id': artwork.pk,
                    'image_original': request.build_absolute_uri(
                        artwork.image_original.url
                    )
                    if artwork.image_original
                    else None,
                    'title': artwork.title,
                }
            )

            if len(artworks) == num_artworks:
                return artworks

    return artworks


def album_object(album, request=None, details=False):
    permissions_qs = PermissionsRelation.objects.filter(album=album)

    if request is not None and album.user != request.user:
        permissions_qs = permissions_qs.filter(user=request.user)

    return {
        'id': album.id,
        'title': album.title,
        'number_of_artworks': album.size(),
        'slides': slides_with_details(album, request) if details else album.slides,
        'owner': {
            'id': album.user.username,
            'name': album.user.get_full_name(),
        },
        'permissions': [
            {
                'user': {
                    'id': p.user.username,
                    'name': p.user.get_full_name(),
                },
                'permissions': [{'id': p.permissions}],
            }
            for p in permissions_qs
        ],
    }
