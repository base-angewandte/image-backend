from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from dal import autocomplete
from rest_framework.response import Response
from artworks.models import *
from artworks.forms import *
from artworks.serializers import ArtworkSerializer

@login_required
def artworks_list(request):
    """
    Render the thumbnailbrowser.
    """
    querySearch = request.GET.get('search')
    querySearchType = request.GET.get('searchtype')
    queryArtworkTitle = request.GET.get('title')
    queryArtistName = request.GET.get('artist')
    queryKeyword = request.GET.get('keyword')
    queryDateFrom = request.GET.get('date_from')
    queryDateTo = request.GET.get('date_to')
    queryLocation = request.GET.get('location')
    qObjects = Q()
    context = {}
    expertSearch = False

    if querySearchType == 'expert':
        expertSearch = True
        if queryArtworkTitle:
            qObjects.add(Q(title__icontains=queryArtworkTitle), Q.AND)
        if queryLocation:
            qObjects.add(Q(locationOfCreation__name__icontains=queryLocation), Q.AND)
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
    else:
        if querySearch:
            terms = [term.strip() for term in querySearch.split()]
            for term in terms:
                qObjects.add(Q(title__icontains=term), Q.OR)
                artists = Artist.objects.filter(name__icontains=term)
                qObjects.add(Q(artists__in=artists), Q.OR)
                qObjects.add(Q(locationOfCreation__name__icontains=term), Q.OR)
                keywords = Keyword.objects.filter(name__icontains=term)
                qObjects.add(Q(keywords__in=keywords), Q.OR)

    querysetList = Artwork.objects.filter(qObjects).distinct().order_by('title')

    paginator = Paginator(querysetList, 40) # show 40 artworks per page
    pageNr = request.GET.get('page')
    try:
        artworks = paginator.get_page(pageNr)
    except PageNotAnInteger:
        artworks = paginator.page(1)
    except EmptyPage:
        artworks = paginator.page(paginator.num_pages)

    context['artworks'] = artworks
    context['query_search'] = querySearch
    context['query_title'] = queryArtworkTitle
    context['query_artist'] = queryArtistName
    context['query_keyword'] = queryKeyword
    context['query_date_from'] = queryDateFrom
    context['query_date_to'] = queryDateTo
    context['query_location'] = queryLocation
    context['expert_search'] = expertSearch
    return render(request, 'artwork/thumbnailbrowser.html', context)


@login_required
def details(request, id=None):
    """
    Return artwork details in json format.
    """
    artwork = Artwork.objects.get(id=id)
    serializer = ArtworkSerializer(artwork)
    return JsonResponse(serializer.data)


@login_required
def artwork_detail_overlay(request, id=None):
    """
    Render an overlay showing a large version of the image and the artwork's details.
    """
    artwork = Artwork.objects.get(id=id)
    context = {}
    context['artwork'] = artwork
    return render(request, 'artwork/artwork_detail_overlay.html', context)


@permission_required('artworks.change_artwork')
def artwork_edit(request, id):
    """
    Render an overlay showing the editable fields of an artwork.
    """
    artwork = Artwork.objects.get(id=id)
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
    Add or remove an artwork from/to a collection.
    """
    if request.method == 'GET':
        artwork = Artwork.objects.get(id=id)
        context = {}
        qs = ArtworkCollection.objects.all()
        collections = qs.filter(user=request.user).order_by('-createdAt')
        context['collections'] = collections
        context['artwork'] = artwork
        return render(request, 'artwork/artwork_collect_overlay.html', context)
    if request.method == 'POST':
        artwork = Artwork.objects.get(id=request.POST['artwork-id'])
        if (request.POST['action'] == 'addCollection'):
            colTitle = request.POST['collection-title']
            if (colTitle):
                u = User.objects.get(id=request.user.id)
                newcol = ArtworkCollection.objects.create(title=colTitle, user=u)
                ArtworkCollectionMembership.objects.create(collection=newcol, artwork=artwork)
                return JsonResponse({'action': 'reload'})
            else:
                return JsonResponse({'error': 'collection title missing'}, status=500)
        else:
            col = ArtworkCollection.objects.get(id=request.POST['collection-id'])
            # users can only manipulate their own collections via this view
            if (request.user == col.user):
                if (request.POST['action'] == 'add'):
                    ArtworkCollectionMembership.objects.create(collection=col, artwork=artwork)
                    return JsonResponse({'action': 'added'})
                if (request.POST['action'] == 'remove'):
                    ArtworkCollectionMembership.objects.filter(collection=col, artwork=artwork).delete()
                    return JsonResponse({'action': 'removed'})
        return JsonResponse({'action': 'collection error'})


@login_required
def collection(request, id=None):
    """
    Render all artwork thumbnails of a single collection.
    """
    if request.method == 'GET':
        col = get_object_or_404(ArtworkCollection, id=id)
        context = {}
        context['title']  = col.title
        context['id']  = col.id
        context['created_by_id'] = col.user.id
        context['created_by_username'] = col.user.get_username()
        context['created_by_fullname'] = col.user.get_full_name()
        context['created_by_userid'] = col.user.id
        context['memberships'] = col.artworkcollectionmembership_set.all()
        context['collections'] = ArtworkCollection.objects.filter(user__groups__in=[1,])
        return render(request, 'artwork/collection.html', context)
    if request.method == 'POST':
        # users can only manipulate their own collections via this view
        col = ArtworkCollection.objects.get(id=id)
        if (request.user.id == col.user.id):
            membership = ArtworkCollectionMembership.objects.get(id=request.POST['membership-id'])
            if not membership:
                return JsonResponse({'error': 'membership does not exist'})
            if (request.POST['action'] == 'left'):
                membership.up()
                return JsonResponse({'action': 'swapleft'})
            if (request.POST['action'] == 'right'):
                membership.down()
                return JsonResponse({'action': 'swapright'})
        else:
            return JsonResponse(status=550, data={'status': 'false', 'message': 'Permission denied'})


# TODO: user should be able to see own *and* all other collections
@login_required
def collections_list(request, id=None):
    """
    Render a list of all collections.
    """
    context = {}
    context['collections'] = ArtworkCollection.objects.filter(user__groups__name='editor').exclude(user=request.user)
    context['my_collections'] = ArtworkCollection.objects.filter(user=request.user)
    return render(request, 'artwork/collections_list.html', context)


@method_decorator(login_required, name='dispatch')
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


@method_decorator(login_required, name='dispatch')
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


@method_decorator(login_required, name='dispatch')
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
