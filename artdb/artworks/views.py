from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from dal import autocomplete
from rest_framework.response import Response
from artworks.models import *
from artworks.forms import *
from artworks.serializers import ArtworkSerializer

def artworks_list(request):
    """
    Render the thumbnailbrowser.
    """
    queryArtworkTitle = request.GET.get('title')
    queryArtistName = request.GET.get('artist')
    queryKeyword = request.GET.get('keyword')
    queryDateFrom = request.GET.get('date_from')
    queryDateTo = request.GET.get('date_to')
    queryLocation = request.GET.get('location')
    qObjects = Q()
    context = {}

    if queryArtworkTitle:
        qObjects.add(Q(title__icontains=queryArtworkTitle), Q.AND)
    if queryLocation:
        qObjects.add(Q(locationOfCreation__icontains=queryLocation), Q.AND)
    if queryDateFrom:
        qObjects.add(Q(dateYearFrom__gte=int(queryDateFrom)), Q.AND)
    if queryDateTo:
        qObjects.add(Q(dateYearTo__lte=int(queryDateTo)), Q.AND)
    if queryArtistName:
        artists = Artist.objects.filter(name__icontains=queryArtistName)
        qObjects.add(Q(artists__in=artists), Q.AND)
    if queryKeyword:
        keywords = Keyword.objects.filter(name__icontains=queryKeyword)
        qObjects.add(Q(keywords__in=keywords), Q.AND)

    querysetList = Artwork.objects.filter(qObjects).distinct().order_by('title')

    paginator = Paginator(querysetList, 40) # show 40 artworks per page
    pageNr = request.GET.get('page')
    try:
        artworks = paginator.get_page(pageNr)
    except PageNotAnInteger:
        artworks = paginator.page(1)
    except EmptyPage:
        artworks = paginator.page(paginator.num_pages)

    context['BASE_HEADER'] = settings.BASE_HEADER
    context['title'] = 'artworks'
    context['artworks'] = artworks
    context['query_title'] = queryArtworkTitle
    context['query_artist'] = queryArtistName
    context['query_keyword'] = queryKeyword
    context['query_date_from'] = queryDateFrom
    context['query_date_to'] = queryDateTo
    context['query_location'] = queryLocation
    return render(request, 'artwork/thumbnailbrowser.html', context)


def details(request, id=None):
    """
    Return artwork details in json format.
    """
    artwork = get_object_or_404(Artwork, id=id)
    serializer = ArtworkSerializer(artwork)
    return JsonResponse(serializer.data)


def artwork_detail_overlay(request, id=None):
    """
    Render an overlay showing a large version of the image and the artwork's details.
    """
    artwork = get_object_or_404(Artwork, id=id)
    context = {}
    context['artwork'] = artwork
    return render(request, 'artwork/artwork_detail_overlay.html', context)


def artwork_edit(request, id):
    """
    Render an overlay showing the editable fields of an artwork.
    """
    artwork = get_object_or_404(Artwork, id=id)
    context = {}
    context['form'] = ArtworkForm(instance=artwork)
    context['id'] = artwork.id
    context['imageOriginal'] = artwork.imageOriginal
    if request.method == "POST":
        form = ArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            updated_artwork = form.save(commit=False)
            # TODO: artwork.user = request.user
            updated_artwork.updatedAt = datetime.now()
            updated_artwork.save()
            # TODO: redirectURL = "%i.json" % artwork.id
            # TODO: reload/close? scroll to thumbnail
            return redirect('/', id=artwork.id)
    return render(request, 'artwork/artwork_edit_overlay.html', context)


@login_required
def artwork_collect(request, id):
    """
    Add or remove an artwork to a collection.
    """
    # TODO: user should only be able to manipulate her own collections
    # if request.user.is_authenticated():
        # Do something for authenticated users.
        # collections = request.user.collections.get(user = userID).order_by('name')
        # userID = request.user.id
    #else:
        # Do something for anonymous users.
    if request.method == 'GET':
        artwork = get_object_or_404(Artwork, id=id)
        context = {}
        qs = ArtworkCollection.objects.all()
        collections = qs.filter(user=request.user).order_by('-createdAt')
        context['collections'] = collections
        context['artwork'] = artwork
        return render(request, 'artwork/artwork_collect_overlay.html', context)
    if request.method == 'POST':
        artwork = get_object_or_404(Artwork, id=request.POST['artwork-id'])
        if (request.POST['action'] == 'add'):
            col = get_object_or_404(ArtworkCollection, id=request.POST['collection-id'])
            # col.artworks.add(artwork)
            ArtworkCollectionMembership.objects.create(collection=col, artwork=artwork)
            return JsonResponse({'action': 'added'})
        if (request.POST['action'] == 'remove'):
            col = get_object_or_404(ArtworkCollection, id=request.POST['collection-id'])
            # col.artworks.remove(artwork)
            ArtworkCollectionMembership.objects.filter(collection=col, artwork=artwork).delete()
            return JsonResponse({'action': 'removed'})
        if (request.POST['action'] == 'addCollection'):
            colTitle = request.POST['collection-title']
            if (colTitle):
                u = User.objects.get(id=request.user.id)
                col = ArtworkCollection.objects.create(title=colTitle, user=u)
                # col.artworks.add(artwork)
                ArtworkCollectionMembership.objects.create(collection=col, artwork=artwork)
                return JsonResponse({'action': 'reload'})
            else:
                return JsonResponse({'error': 'title missing'},  status=500)
        return JsonResponse({'action': 'none'})


def collection(request, id=None):
    """
    Render all artwork thumbnails of a single collection.
    """
    col = get_object_or_404(ArtworkCollection, id=id)
    context = {}
    context['BASE_HEADER'] = settings.BASE_HEADER
    context['title']  = col.title
    context['id']  = col.id
    context['created_by_id'] = col.user.id
    context['created_by_username'] = col.user.get_username()
    context['created_by_fullname'] = col.user.get_full_name()
    context['artworks'] = col.artworks.all()
    context['collections'] = ArtworkCollection.objects.all()
    return render(request, 'artwork/collection.html', context)


def collections_list(request, id=None):
    """
    Render a list of all collections.
    """
    context = {}
    context['BASE_HEADER'] = settings.BASE_HEADER
    context['collections'] = ArtworkCollection.objects.filter(user=request.user)
    return render(request, 'artwork/collections_list.html', context)


class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    """
    Return dal suggestions for the artist input field.
    """
    def get_queryset(self):
        # TODO: Don't forget to filter out results depending on the visitor
        # if not self.request.user.is_authenticated():
        # return Artist.objects.none()
        qs = Artist.objects.all().order_by('name')
        if self.q:
            return qs.filter(name__icontains=self.q)
        else:
            return Artist.objects.none()


class ArtworkAutocomplete(autocomplete.Select2QuerySetView):
    """
    Return dal suggestions for the basic search.
    Suggest the first 4 artworks with matching titles.
    """
    def get_queryset(self):
        qs = Artwork.objects.all()
        if self.q:
            qs = qs.filter(title__icontains=self.q).order_by('title')
            # order results by startswith match
            # see: https://stackoverflow.com/questions/11622501
            expression = Q(title__startswith=self.q)
            is_match = ExpressionWrapper(expression, output_field=BooleanField())
            qs = qs.annotate(myfield=is_match)
            qs = qs.order_by('-myfield')[:4]
            return qs
        else:
            return Artwork.objects.none()
            
    def get_result_value(self, result):
        """Return the value of a result."""
        return result.title


class KeywordAutocomplete(autocomplete.Select2QuerySetView):
    """
    Return dal suggestions for the artwork's keywords input field.
    """
    def get_queryset(self):
        qs = Keyword.objects.all().order_by('name')
        if self.q:
            return qs.filter(name__icontains=self.q)
        else:
            return Keyword.objects.none()