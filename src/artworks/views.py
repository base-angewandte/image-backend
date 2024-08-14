import logging
import operator
from datetime import datetime
from functools import reduce

from dal import autocomplete

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
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
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from .forms import AlbumForm, ArtworkForm, ImageFieldForm
from .models import Album, Artwork, Keyword, Location, Person
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
    query_location = request.GET.get('location')
    q_objects = Q()
    context = {}
    expert_search = False

    def get_expert_queryset_list():
        expert_list = Artwork.objects.filter(published=True)
        if query_place_of_production:
            locations = Location.objects.filter(
                name__istartswith=query_place_of_production,
            )
            locations_plus_descendants = Location.objects.get_queryset_descendants(
                locations,
                include_self=True,
            )
            q_objects.add(Q(place_of_production__in=locations_plus_descendants), Q.AND)
        if query_location:
            locations = Location.objects.filter(name__istartswith=query_location)
            locations_plus_descendants = Location.objects.get_queryset_descendants(
                locations,
                include_self=True,
            )
            q_objects.add(Q(location__in=locations_plus_descendants), Q.AND)
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
                title_english__icontains=query_artwork_title,
            )
            title_starts_with = Q(title__istartswith=query_artwork_title) | Q(
                title_english__istartswith=query_artwork_title,
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

            def get_persons(term):
                return Person.objects.filter(
                    Q(name__unaccent__istartswith=term)
                    | Q(name__unaccent__icontains=' ' + term),
                )

            def get_keywords(term):
                return Keyword.objects.filter(
                    Q(name__istartswith=term) | Q(name__istartswith=' ' + term),
                )

            terms = [term.strip() for term in query_search.split()]
            basic_list = (
                Artwork.objects.annotate(
                    rank=Case(
                        When(Q(title__iexact=query_search), then=Value(1)),
                        When(Q(title_english__iexact=query_search), then=Value(1)),
                        When(Q(artists__in=get_persons(query_search)), then=Value(2)),
                        When(Q(title__istartswith=query_search), then=Value(3)),
                        When(Q(title_english__istartswith=query_search), then=Value(3)),
                        When(
                            reduce(
                                operator.or_,
                                (Q(artists__in=get_persons(term)) for term in terms),
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
                    ),
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
                '-date_changed',
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
    context['query_location'] = query_location
    context['expert_search'] = expert_search
    return render(request, 'artwork/thumbnailbrowser.html', context)


@login_required
def details(request, pk=None):
    """Return artwork details in json format."""
    try:
        artwork = Artwork.objects.get(id=pk)
    except Artwork.DoesNotExist:
        logger.warning('Could not find artwork: %s', pk)
        return JsonResponse(
            status=404,
            data={'status': 'false', 'message': 'Could not get artwork details'},
        )
    serializer = ArtworkSerializer(artwork)
    return JsonResponse(serializer.data)


@login_required
def artwork_detail_overlay(request, pk=None):
    """Render an overlay showing a large version of the image and the artwork's
    details."""
    artwork = get_object_or_404(Artwork, id=pk)
    context = {
        'artwork': artwork,
        'is_staff': request.user.is_staff,
    }
    return render(request, 'artwork/artwork_detail_overlay.html', context)


@permission_required('artworks.change_artwork')
def artwork_edit(request, pk):
    """Render an overlay showing the editable fields of an artwork."""
    artwork = get_object_or_404(Artwork, id=pk)
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
def collection_edit(request, pk):
    """Render an overlay showing the editable fields of a collection."""
    artwork_collection = get_object_or_404(Album, id=pk)
    if request.user.id is not artwork_collection.user.id:
        # users can only manipulate their own collections via this view
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=artwork_collection)
        if form.is_valid():
            form.save()
            return redirect('collection', pk=pk)
    context = {
        'form': AlbumForm(instance=artwork_collection),
        'collection': artwork_collection,
    }
    return render(request, 'artwork/collection_edit_overlay.html', context)


@login_required
def collection_delete(request, pk):
    """Delete a collection."""
    if request.method == 'POST':
        try:
            artwork_collection = Album.objects.get(id=pk)
            if request.user.id is artwork_collection.user.id:
                # users can only manipulate their own collections via this view
                artwork_collection.delete()
                return redirect('collections-list')
            else:
                logger.warning('Could not get artwork collection: %s', pk)
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
        return redirect('collection', pk=pk)


@login_required
def collection_json(request, pk=None):
    """Return collection data in json format."""
    try:
        col = Album.objects.get(id=pk)
    except Album.DoesNotExist:
        logger.warning('Could not get artwork collection: %s', pk)
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


@method_decorator(login_required, name='dispatch')
class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    """Return dal suggestions for the artist input field."""

    def get_queryset(self):
        qs = Person.objects.all().order_by('name')
        if self.q:
            return qs.filter(
                Q(name__unaccent__istartswith=self.q)
                | Q(name__unaccent__icontains=' ' + self.q)
                | Q(synonyms__unaccent__istartswith=self.q)
                | Q(synonyms__unaccent__icontains=' ' + self.q),
            )
        else:
            return Person.objects.none()


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


class MultiArtworkCreationFormView(PermissionRequiredMixin, FormView):
    form_class = ImageFieldForm
    template_name = 'admin/artwork/upload.html'
    success_url = reverse_lazy('admin:artworks_artwork_changelist')
    permission_required = ['artworks.add_artwork']

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        files = form.cleaned_data['image_field']
        for f in files:
            Artwork(
                title=f.name,
                image_original=f,
                published=False,
                checked=False,
            ).save()
        messages.success(self.request, _('Images successfully uploaded'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add the title to the context data."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Upload multiple images')
        return context
