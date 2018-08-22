from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime
from artworks.models import *
from artworks.forms import *
from artworks.serializers import ArtworkSerializer
from rest_framework.response import Response
from dal import autocomplete

def index(request):
    query = request.GET.get('artist')
    context = {}
    if not query:
        # per default, the artworks are shown that were modified most recently
        queryset = Artwork.objects.all().order_by('title').order_by('-updatedAt')
    if query:
        # TODO: add date filter
        queryset = Artwork.objects.filter(artists__id=str(query)).order_by('title')
    paginator = Paginator(queryset, 3)
    page = request.GET.get('page')
    artworks = paginator.get_page(page)
    context['title'] = 'artworks'
    context['artworks'] = artworks
    return render(request, 'artwork/index.html', context)

# return the artwork details in json format
def details(request, id=None):
    artwork = get_object_or_404(Artwork, id=id)
    serializer = ArtworkSerializer(artwork)
    return JsonResponse(serializer.data)

# return the artwork page
# to be placed into the overlay via js
def getArtworkContext(artwork):
    context = {}
    context['big_url'] = artwork.big.url
    return context

def artwork_detail_overlay(request, id=None):
    artwork = get_object_or_404(Artwork, id=id)
    return render(request, 'artwork/artwork_detail_overlay.html', getArtworkContext(artwork))


def artwork(request, id=None):
    artwork = get_object_or_404(Artwork, id=id)
    context = getArtworkContext(artwork)
    context['id'] = artwork.id
    return render(request, 'artwork/artwork.html', context)


def artwork_new(request):
    if request.method == "POST":
        form = ArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # TODO: artwork.user = request.user
            # https://www.youtube.com/watch?v=qwE9TFNub84
            # TODO: redirectURL = "%i.json" % artwork.id
            redirectURL = './'
            return redirect(redirectURL)
    else:
        form = ArtworkForm()
        return render(request, 'artwork/artwork_new.html', {'form': form})


def artwork_edit(request, id):
    artwork = get_object_or_404(Artwork, id=id)
    if request.method == "POST":
        form = ArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            artwork = form.save(commit=False)
            # TODO: artwork.user = request.user
            artwork.updatedAt = datetime.now()
            artwork.save()
            # TODO: redirectURL = "%i.json" % artwork.id
            return redirect('/artwork', id=artwork.id)
    else:
        context = {}
        context['form'] = ArtworkForm(instance=artwork)
        context['id'] = artwork.id
        context['big_url'] = artwork.big.url
        return render(request, 'artwork/artwork_edit.html', context)


def artwork_delete(request, id):
    artwork = get_object_or_404(Artwork, id=id)
    if request.method == "POST":
        artwork.delete()
        return redirect('/artwork', id=artwork.id)
    else:
        context = {}
        context['id'] = artwork.id
        return render(request, 'artwork/artwork_delete.html', context)


def collection(request, id=None):
    artworkCollection = get_object_or_404(ArtworkCollection, id=id)
    context = {}
    context['title']  = artworkCollection.title
    context['created_by_id'] = artworkCollection.user.id
    context['created_by_username'] = artworkCollection.user.get_username()
    context['created_by_fullname'] = artworkCollection.user.get_full_name()
    # TODO: figure out/use .order_by of the m2m manager
    context['artworks'] = artworkCollection.artworks.all()
    return render(request, 'artwork/collection.html', context)


class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        # if not self.request.user.is_authenticated():
            # return Artist.objects.none()

        qs = Artist.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs

def artist_artworks(request, id=None):
    # artist = get_object_or_404(Artist, id=id)
    # artworks = Artwork.objects.get(pk=artist.id)
    # context = {}
    # context['title'] = artworks.title
    return index(request, artist=id)
    #return render(request, 'artists/artworks.html', context)