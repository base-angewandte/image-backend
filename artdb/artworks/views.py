import logging
import operator
from datetime import datetime
from functools import reduce

from dal import autocomplete

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import (
    BooleanField,
    Case,
    ExpressionWrapper,
    IntegerField,
    Q,
    Value,
    When,
)
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator

from .forms import AlbumForm, ArtworkForm
from .models import Album, AlbumMembership, Artist, Artwork, Keyword, Location
from .serializers import ArtworkSerializer, CollectionSerializer

logger = logging.getLogger(__name__)


@login_required
def artworks_list(request):
    """Render the thumbnailbrowser."""
    query_search = request.GET.get('search')
    query_search_type = request.GET.get('searchtype')
    query_artwork_title = request.GET.get('title')
    query_artist_name = request.GET.get('artist')
    query_keyword = request.GET.get('keyword')
    query_date_from = request.GET.get('date_from')
    query_date_to = request.GET.get('date_to')
    query_place_of_production = request.GET.get('place_of_production')
    query_location_current = request.GET.get('location_current')
    q_objects = Q()
    context = {}
    expert_search = False

    def get_expert_queryset_list():
        expert_list = Artwork.objects.filter(published=True)
        if query_place_of_production:
            locations = Location.objects.filter(
                name__istartswith=query_place_of_production
            )
            locations_plus_descendants = Location.objects.get_queryset_descendants(
                locations,
                include_self=True,
            )
            q_objects.add(Q(place_of_production__in=locations_plus_descendants), Q.AND)
        if query_location_current:
            locations = Location.objects.filter(
                name__istartswith=query_location_current
            )
            locations_plus_descendants = Location.objects.get_queryset_descendants(
                locations,
                include_self=True,
            )
            q_objects.add(Q(location_current__in=locations_plus_descendants), Q.AND)
        if query_artist_name:
            terms = [term.strip() for term in query_artist_name.split()]
            for term in terms:
                q_objects.add(
                    (
                        Q(artists__name__unaccent__icontains=term)
                        | Q(artists__synonyms__unaccent__icontains=term)
                    ),
                    Q.AND,
                )
        if query_keyword:
            keywords = Keyword.objects.filter(name__icontains=query_keyword)
            q_objects.add(Q(keywords__in=keywords), Q.AND)
        if query_date_from:
            try:
                year = int(query_date_from)
                q_objects.add(Q(date_year_from__gte=year), Q.AND)
            except ValueError as err:
                logger.error(err)
                return []
        if query_date_to:
            try:
                year = int(query_date_to)
                q_objects.add(Q(date_year_to__lte=year), Q.AND)
            except ValueError as err:
                logger.error(err)
                return []
        if query_artwork_title:
            title_contains = Q(title__icontains=query_artwork_title) | Q(
                title_english__icontains=query_artwork_title
            )
            title_starts_with = Q(title__istartswith=query_artwork_title) | Q(
                title_english__istartswith=query_artwork_title
            )
            # order results by startswith match. see: https://stackoverflow.com/a/48409962
            expert_list = expert_list.filter(title_contains)
            is_match = ExpressionWrapper(title_starts_with, output_field=BooleanField())
            expert_list = expert_list.annotate(starts_with_title=is_match)
            expert_list = expert_list.filter(q_objects).order_by(
                '-starts_with_title',
                'place_of_production',
            )
        else:
            expert_list = expert_list.filter(q_objects).order_by(
                'title',
                'place_of_production',
            )
        return expert_list.distinct()

    def get_basic_queryset_list():
        if query_search:

            def get_artists(term):
                return Artist.objects.filter(
                    Q(name__unaccent__istartswith=term)
                    | Q(name__unaccent__icontains=' ' + term)
                )

            def get_keywords(term):
                return Keyword.objects.filter(
                    Q(name__istartswith=term) | Q(name__istartswith=' ' + term)
                )

            terms = [term.strip() for term in query_search.split()]
            basic_list = (
                Artwork.objects.annotate(
                    rank=Case(
                        When(Q(title__iexact=query_search), then=Value(1)),
                        When(Q(title_english__iexact=query_search), then=Value(1)),
                        When(Q(artists__in=get_artists(query_search)), then=Value(2)),
                        When(Q(title__istartswith=query_search), then=Value(3)),
                        When(Q(title_english__istartswith=query_search), then=Value(3)),
                        When(
                            reduce(
                                operator.or_,
                                (Q(artists__in=get_artists(term)) for term in terms),
                            ),
                            then=Value(4),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (Q(title__istartswith=term) for term in terms),
                            ),
                            then=Value(5),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (Q(title_english__istartswith=term) for term in terms),
                            ),
                            then=Value(5),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (Q(title__icontains=' ' + term) for term in terms),
                            ),
                            then=Value(6),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (
                                    Q(title_english__icontains=' ' + term)
                                    for term in terms
                                ),
                            ),
                            then=Value(6),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (Q(title__icontains=term) for term in terms),
                            ),
                            then=Value(7),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (Q(title_english__icontains=term) for term in terms),
                            ),
                            then=Value(7),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (
                                    Q(place_of_production__name__istartswith=term)
                                    for term in terms
                                ),
                            ),
                            then=Value(10),
                        ),
                        When(
                            reduce(
                                operator.or_,
                                (Q(keywords__in=get_keywords(term)) for term in terms),
                            ),
                            then=Value(11),
                        ),
                        default=Value(99),
                        output_field=IntegerField(),
                    )
                )
                .filter(published=True)
                .exclude(rank=99)
                .distinct(
                    'id',
                    'rank',
                    'title',
                )
                .order_by(
                    'rank',
                    'title',
                )
            )
        else:
            # what the user gets, when she isn't using the search at all
            basic_list = Artwork.objects.filter(published=True).order_by(
                '-updated_at',
                'title',
            )
        return basic_list

    if query_search_type == 'expert':
        queryset_list = get_expert_queryset_list()
        expert_search = True
    else:
        queryset_list = get_basic_queryset_list()

    paginator = Paginator(queryset_list, 40)  # show 40 artworks per page
    page_nr = request.GET.get('page')
    try:
        artworks = paginator.get_page(page_nr)
    except PageNotAnInteger:
        artworks = paginator.page(1)
    except EmptyPage:
        artworks = paginator.page(paginator.num_pages)

    context['artworks'] = artworks
    context['query_search'] = query_search
    context['query_title'] = query_artwork_title
    context['query_artist'] = query_artist_name
    context['query_keyword'] = query_keyword
    context['query_date_from'] = query_date_from
    context['query_date_to'] = query_date_to
    context['query_place_of_production'] = query_place_of_production
    context['query_location_current'] = query_location_current
    context['expert_search'] = expert_search
    return render(request, 'artwork/thumbnailbrowser.html', context)


@login_required
def details(request, id=None):
    """Return artwork details in json format."""
    try:
        artwork = Artwork.objects.get(id=id)
    except Artwork.DoesNotExist:
        logger.warning('Could not find artwork: %s', id)
        return JsonResponse(
            status=404,
            data={'status': 'false', 'message': 'Could not get artwork details'},
        )
    serializer = ArtworkSerializer(artwork)
    return JsonResponse(serializer.data)


@login_required
def artwork_detail_overlay(request, id=None):
    """Render an overlay showing a large version of the image and the artwork's
    details."""
    artwork = get_object_or_404(Artwork, id=id)
    context = {
        'artwork': artwork,
        'is_staff': request.user.is_staff,
    }
    return render(request, 'artwork/artwork_detail_overlay.html', context)


@permission_required('artworks.change_artwork')
def artwork_edit(request, id):
    """Render an overlay showing the editable fields of an artwork."""
    artwork = get_object_or_404(Artwork, id=id)
    if request.method == 'POST':
        form = ArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            updated_artwork = form.save(commit=False)
            updated_artwork.updated_at = datetime.now()
            updated_artwork.save()
            form.save_m2m()
            return HttpResponse('<script>window.location=document.referrer;</script>')
    context = {
        'form': ArtworkForm(instance=artwork),
        'id': artwork.id,
        'image_original': artwork.image_original,
    }
    return render(request, 'artwork/artwork_edit_overlay.html', context)


@login_required
def artwork_collect(request, id):
    """Add or remove an artwork from/to a collection."""
    if request.method == 'GET':
        artwork = get_object_or_404(Artwork, id=id)
        context = {}
        qs = Album.objects.all()
        collections = qs.filter(user=request.user).order_by('-created_at')
        context['collections'] = collections
        context['artwork'] = artwork
        return render(request, 'artwork/artwork_collect_overlay.html', context)
    if request.method == 'POST':
        try:
            artwork = Artwork.objects.get(id=request.POST['artwork-id'])
        except Artwork.DoesNotExist:
            logger.warning(
                'Could not find artwork membership: %s', request.POST['artwork-id']
            )
            return JsonResponse(
                status=404,
                data={'status': 'false', 'message': 'Artwork does not exist'},
            )
        if request.POST['action'] == 'addCollection':
            col_title = request.POST['collection-title']
            if col_title:
                try:
                    u = User.objects.get(id=request.user.id)
                    newcol = Album.objects.create(title=col_title, user=u)
                    AlbumMembership.objects.create(collection=newcol, artwork=artwork)
                    return JsonResponse({'action': 'reload'})
                except User.DoesNotExist:
                    logger.warning('Could not find user: %s', request.user.id)
                    return JsonResponse(
                        status=404,
                        data={'status': 'false', 'message': 'User does not exist'},
                    )
            else:
                return JsonResponse({'error': 'collection title missing'}, status=500)
        else:
            try:
                col = Album.objects.get(id=request.POST['collection-id'])
            except Album.DoesNotExist:
                logger.warning(
                    'Could not find artwork collection: %s',
                    request.POST['collection-id'],
                )
                return JsonResponse(
                    status=404,
                    data={'status': 'false', 'message': 'Collection does not exist'},
                )
            # users can only manipulate their own collections via this view
            if request.user == col.user:
                if request.POST['action'] == 'add':
                    AlbumMembership.objects.get_or_create(
                        collection=col,
                        artwork=artwork,
                    )
                    return JsonResponse({'action': 'added'})
                if request.POST['action'] == 'remove':
                    try:
                        artwork_col_mem = AlbumMembership.objects.get(
                            collection=col,
                            artwork=artwork,
                        )
                        artwork_col_mem.remove()
                        return JsonResponse({'action': 'removed'})
                    except AlbumMembership.DoesNotExist:
                        logger.warning('Could not remove artwork from collection')
                        return JsonResponse(
                            status=500,
                            data={
                                'status': 'false',
                                'message': 'Could not remove artwork from collection',
                            },
                        )
                    except MultipleObjectsReturned:
                        logger.warning('Duplicate AlbumMemberships. Removing them all.')
                        artwork_col_mem = AlbumMembership.objects.filter(
                            collection=col,
                            artwork=artwork,
                        )
                        artwork_col_mem.remove()
                        return JsonResponse({'action': 'removed'})
        return JsonResponse(
            status=500,
            data={'status': 'false', 'message': 'Could not manipulate collection'},
        )


@login_required
def collection(request, id=None):
    """
    GET: Render all artwork thumbnails of a single collection.
    POST: move artworks within collection; connect or disconnect them
    """
    if request.method == 'GET':
        col = get_object_or_404(Album, id=id)
        context = {
            'title': col.title,
            'id': col.id,
            'created_by_username': col.user.get_username(),
            'created_by_fullname': col.user.get_full_name(),
            'created_by_userid': col.user.id,
            'memberships': col.albummembership_set.all(),
            # 'collections': Album.objects.filter(user__groups__name='editor').exclude(user=request.user),
            'my_collections': Album.objects.filter(user=request.user),
        }
        return render(request, 'artwork/collection.html', context)
    if request.method == 'POST':
        # users can only manipulate their own collections via this view
        try:
            col = Album.objects.get(id=id)
        except Album.DoesNotExist:
            logger.warning('Could not find artwork collection: %s', id)
            return JsonResponse(
                status=404,
                data={
                    'status': 'false',
                    'message': 'Could not find artwork collection',
                },
            )
        if request.user.id != col.user.id:
            return JsonResponse(
                status=403,
                data={'status': 'false', 'message': 'Permission needed'},
            )
        if request.POST['action'] == 'left' or request.POST['action'] == 'right':
            if 'membership-id' in request.POST:
                try:
                    membership = AlbumMembership.objects.get(
                        id=request.POST['membership-id'],
                        collection=col,
                    )
                    # move artwork left
                    if request.POST['action'] == 'left':
                        membership.move_left()
                        return JsonResponse({'message': 'moved left'})
                    # move artwork right
                    if request.POST['action'] == 'right':
                        membership.move_right()
                        return JsonResponse({'message': 'moved right'})
                except AlbumMembership.DoesNotExist:
                    logger.warning(
                        'Could not get artwork membership: %s',
                        request.POST['membership-id'],
                    )
            return JsonResponse(
                status=500,
                data={
                    'status': 'false',
                    'message': 'Could not move artwork membership',
                },
            )
        elif (
            request.POST['action'] == 'connect'
            or request.POST['action'] == 'disconnect'
        ):
            # user wants to connect or disconnect the artwork
            try:
                left_member = AlbumMembership.objects.get(
                    id=request.POST['member-left'], collection=col
                )
                right_member = AlbumMembership.objects.get(
                    id=request.POST['member-right'], collection=col
                )
                if request.POST['action'] == 'connect':
                    if left_member.connect(right_member):
                        return JsonResponse({'message': 'connected'})
                if request.POST['action'] == 'disconnect':
                    if left_member.disconnect(right_member):
                        return JsonResponse({'message': 'disconnected'})
            except AlbumMembership.DoesNotExist:
                logger.warning(
                    "Could not do action '%s' on artwork membership '%s'",
                    request.POST['action'],
                    request.POST['membership-id'],
                )
            return JsonResponse(
                status=500,
                data={
                    'status': 'false',
                    'message': 'Could not connect/disconnect artwork membership',
                },
            )
        return JsonResponse(
            status=404,
            data={'status': 'false', 'message': 'Invalid post action'},
        )


@login_required
def collection_edit(request, id):
    """Render an overlay showing the editable fields of a collection."""
    artwork_collection = get_object_or_404(Album, id=id)
    if request.user.id is not artwork_collection.user.id:
        # users can only manipulate their own collections via this view
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=artwork_collection)
        if form.is_valid():
            form.save()
            return redirect('collection', id=id)
    context = {
        'form': AlbumForm(instance=artwork_collection),
        'collection': artwork_collection,
    }
    return render(request, 'artwork/collection_edit_overlay.html', context)


@login_required
def collection_delete(request, id):
    """Delete a collection."""
    if request.method == 'POST':
        try:
            artwork_collection = Album.objects.get(id=id)
            if request.user.id is artwork_collection.user.id:
                # users can only manipulate their own collections via this view
                artwork_collection.delete()
                return redirect('collections-list')
            else:
                logger.warning('Could not get artwork collection: %s', id)
                return JsonResponse(
                    status=403,
                    data={'status': 'false', 'message': 'Permission needed'},
                )
        except Album.DoesNotExist:
            return JsonResponse(
                status=500,
                data={'status': 'false', 'message': 'Could not delete collection'},
            )
    else:
        return redirect('collection', id=id)


@login_required
def collection_json(request, id=None):
    """Return collection data in json format."""
    try:
        col = Album.objects.get(id=id)
    except Album.DoesNotExist:
        logger.warning('Could not get artwork collection: %s', id)
        return JsonResponse(
            status=404,
            data={'status': 'false', 'message': 'Could not get collection'},
        )
    serializer = CollectionSerializer(col)
    return JsonResponse(serializer.data)


@login_required
def collections_list(request):
    """Render a list of all collections."""
    context = {
        # 'collections': Album.objects.filter(user__groups__name='editor').exclude(user=request.user),
        'my_collections': Album.objects.filter(user=request.user),
    }
    return render(request, 'artwork/collections_list.html', context)


class ArtworkArtistAutocomplete(autocomplete.Select2QuerySetView):
    """Return dal suggestions for the artist filter."""

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Artist.objects.none()

        qs = Artist.objects.all().order_by('name')

        if self.q:
            return qs.filter(
                Q(name__unaccent__icontains=self.q)
                | Q(synonyms__unaccent__icontains=self.q)
            )

        return qs


@method_decorator(login_required, name='dispatch')
class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    """Return dal suggestions for the artist input field."""

    def get_queryset(self):
        qs = Artist.objects.all().order_by('name')
        if self.q:
            return qs.filter(
                Q(name__unaccent__istartswith=self.q)
                | Q(name__unaccent__icontains=' ' + self.q)
                | Q(synonyms__unaccent__istartswith=self.q)
                | Q(synonyms__unaccent__icontains=' ' + self.q)
            )
        else:
            return Artist.objects.none()


@method_decorator(login_required, name='dispatch')
class ArtworkAutocomplete(autocomplete.Select2QuerySetView):
    """Return dal suggestions for the basic search.

    Suggest the first 4 artworks with matching titles.
    """

    def get_queryset(self):
        qs = Artwork.objects.all()
        if self.q:
            qs = qs.filter(title__icontains=self.q).order_by('title')
            # order results by startswith match. see: https://stackoverflow.com/a/48409962
            expression = Q(title__istartswith=self.q) | Q(title__icontains=' ' + self.q)
            is_match = ExpressionWrapper(expression, output_field=BooleanField())
            qs = qs.annotate(title_starts_with=is_match)
            qs = qs.distinct('title', 'title_starts_with')
            qs = qs.order_by('-title_starts_with', 'title')[:4]
            return qs
        else:
            return Artwork.objects.none()

    def get_result_value(self, result):
        """Return the value of a result."""
        return result.title


@method_decorator(login_required, name='dispatch')
class KeywordAutocomplete(autocomplete.Select2QuerySetView):
    """Return dal suggestions for the artwork's keywords input field."""

    def get_queryset(self):
        qs = Keyword.objects.all().order_by('name')
        if self.q:
            return qs.filter(name__icontains=self.q)
        else:
            return Keyword.objects.none()
