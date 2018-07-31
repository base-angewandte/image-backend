from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime
from artworks.models import *
from artworks.forms import *
from dal import autocomplete

def index(request):
    context = {}
    # TODO: do not get *all* objects here! (just the latest?)
    artworks = Artwork.objects.all()
    paginator = Paginator(artworks, 3)
    page = request.GET.get('page')
    artworks = paginator.get_page(page)
    context['title'] = 'artworks'
    context['artworks'] = artworks
    return render(request, 'artworks/index.html', context)

# return the artwork details in json format
def details(request, id=None):
    artwork = get_object_or_404(Artwork, id=id)
    artistName = ''
    if artwork.artist:
        artistName = artwork.artist.name
    data = {
        'Title' : artwork.title,
        'Artist' : artistName,
        'Location of creation': artwork.locationOfCreation,
        'Date of creation' : artwork.date,
        'Material' : artwork.material,
        'Dimensions' : artwork.dimensions,
        'Credits' : artwork.credits
    }
    jsonData = {key:value for key, value in data.items() 
        if ((value is not '') and (value is not None))}
    return JsonResponse(jsonData)


# return the artwork page
# to be placed into the overlay via js
def getArtworkContext(artwork):
    context = {}
    context['big_url'] = artwork.big.url
    return context

def artwork_overlay_only(request, id=None):
    artwork = get_object_or_404(Artwork, id=id)
    return render(request, 'artworks/artwork_overlay_only.html', getArtworkContext(artwork))


def artwork(request, id=None):
    artwork = get_object_or_404(Artwork, id=id)
    context = getArtworkContext(artwork)
    context['id'] = artwork.id
    return render(request, 'artworks/artwork.html', context)


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
        return render(request, 'artworks/artwork_new.html', {'form': form})


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
            return redirect('/artworks', id=artwork.id)
    else:
        context = {}
        context['form'] = ArtworkForm(instance=artwork)
        context['id'] = artwork.id
        context['big_url'] = artwork.big.url
        return render(request, 'artworks/artwork_edit.html', context)


def artwork_delete(request, id):
    artwork = get_object_or_404(Artwork, id=id)
    if request.method == "POST":
        artwork.delete()
        return redirect('/artworks', id=artwork.id)
    else:
        context = {}
        context['id'] = artwork.id
        return render(request, 'artworks/artwork_delete.html', context)


def collection(request, id=None):
    artworkCollection = get_object_or_404(ArtworkCollection, id=id)
    context = {}
    context['title']  = artworkCollection.title
    context['created_by_id'] = artworkCollection.user.id
    context['created_by_username'] = artworkCollection.user.get_username()
    context['created_by_fullname'] = artworkCollection.user.get_full_name()
    # TODO: figure out/use .order_by of the m2m manager
    context['artworks'] = artworkCollection.artworks.all()
    return render(request, 'artworks/collection.html', context)


class ArtistAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        # if not self.request.user.is_authenticated():
            # return Artist.objects.none()

        qs = Artist.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
