from rest_framework.exceptions import NotFound, ParseError
from rest_framework.request import Request

from django.utils.translation import gettext_lazy as _

from artworks.models import Album, Artwork, PermissionsRelation


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
                        artwork.image_original.url,
                    )
                    if artwork.image_original
                    else None,
                    'title': artwork.title,
                    'discriminatory_terms': artwork.get_discriminatory_terms_list(),
                    'credits': artwork.credits,
                    'date': artwork.date,
                    'artists': [
                        {
                            'id': artist.id,
                            'value': artist.name,
                        }
                        for artist in artwork.artists.all()
                    ],
                },
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
                        artwork.image_original.url,
                    )
                    if artwork.image_original
                    else None,
                    'title': artwork.title,
                    'discriminatory_terms': artwork.get_discriminatory_terms_list(),
                },
            )

            if len(artworks) == num_artworks:
                return artworks

    return artworks


def album_object(
    album: Album,
    request: Request = None,
    details=False,
    include_slides=True,
    include_type=False,
    include_featured=False,
) -> dict:
    """Returns a dict representation of an album object.

    This will return a dictionary that can be used directly in API
    responses, representing an album. While this is not an actual
    serialization, it serves the purpose of contextually serializing an
    album object into a format containing potential extra information,
    like the slide details or featured artworks.

    :param album: the album to 'serialize'
    :param request: the request context with information about the
        logged-in user
    :param details: whether to include nested information in the slides
        list (default is False)
    :param include_slides: whether to include the slides list at all
        (default is True)
    :param include_type: whether to include the type information, e.g.
        when listed in folders (default is False)
    :param include_featured: whether to include the featured artworks
        (default is False)
    :returns: a dict representing the album with all requested features
    """
    permissions_qs = PermissionsRelation.objects.filter(album=album)

    # only album owners see all permissions. users who an album is shared with see
    # either only their own permission, or - if they have EDIT permissions themselves -
    # all other users with EDIT permissions
    if request is not None and album.user != request.user:
        if permissions_qs.filter(user=request.user, permissions='EDIT').exists():
            permissions_qs = permissions_qs.filter(permissions='EDIT')
        else:
            permissions_qs = permissions_qs.filter(user=request.user)

    ret = {
        'id': album.id,
        'title': album.title,
        'number_of_artworks': album.size(),
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
        'date_created': album.date_created,
        'date_changed': album.date_changed,
    }

    if album.last_changed_by:
        ret['last_changed_by'] = {
            'id': album.last_changed_by.username,
            'name': album.last_changed_by.get_full_name(),
        }
    else:
        ret['last_changed_by'] = ret['owner']

    if include_slides:
        ret['slides'] = slides_with_details(album, request) if details else album.slides
    if include_type:
        ret['type'] = album._meta.object_name
    if include_featured:
        ret['featured_artworks'] = featured_artworks(album, request)
    return ret
