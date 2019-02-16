from datetime import datetime
from io import BytesIO
from functools import reduce
import operator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, ExpressionWrapper, BooleanField, Case, Value, IntegerField, When
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.db.models.functions import Upper
from dal import autocomplete
from rest_framework.response import Response
from pptx import Presentation
from pptx.dml.color import RGBColor 
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Pt
from artworks.models import *
from artworks.forms import *
from artworks.serializers import ArtworkSerializer, CollectionSerializer


@login_required
def artworks_list(request):
    """
    Render the thumbnailbrowser.
    """
    query_search = request.GET.get('search')
    query_search_type = request.GET.get('searchtype')
    query_artwork_title = request.GET.get('title')
    query_artist_name = request.GET.get('artist')
    query_keyword = request.GET.get('keyword')
    query_date_from = request.GET.get('date_from')
    query_date_to = request.GET.get('date_to')
    query_location_of_creation = request.GET.get('location_of_creation')
    query_location_current = request.GET.get('location_current')
    q_objects = Q()
    context = {}
    expertSearch = False

    if query_search_type == 'expert':
        expertSearch = True
        querysetList = Artwork.objects.filter(published=True)
        if query_location_of_creation:
            q_objects.add(Q(location_of_creation__name__icontains=query_location_of_creation), Q.AND)
        if query_location_current:
            q_objects.add(Q(location_current__name__icontains=query_location_current), Q.AND)
        if query_date_from:
            q_objects.add(Q(dateYearFrom__gte=int(query_date_from)), Q.AND)
        if query_date_to:
            q_objects.add(Q(dateYearTo__lte=int(query_date_to)), Q.AND)
        if query_artist_name:
            artists = Artist.objects.filter(name__icontains=query_artist_name)
            synonyms = Artist.objects.filter(synonyms__icontains=query_artist_name)
            q_objects.add((Q(artists__in=artists) | Q(artists__in=synonyms)), Q.AND)
        if query_keyword:
            keywords = Keyword.objects.filter(name__icontains=query_keyword)
            q_objects.add(Q(keywords__in=keywords), Q.AND)

        if query_artwork_title:
            # order results by startswith match. see: https://stackoverflow.com/a/48409962
            querysetList = querysetList.filter(title__icontains=query_artwork_title)
            expression = Q(title__startswith=query_artwork_title)
            is_match = ExpressionWrapper(expression, output_field=BooleanField())
            querysetList = querysetList.annotate(myfield=is_match)

        querysetList = (querysetList.filter(q_objects)
                .order_by('title', 'location_of_creation')
                .distinct())
    else:
        if query_search:
            terms = [term.strip() for term in query_search.split()]

            def get_artists(term):
                return Artist.objects.filter(Q(name__istartswith=term) | Q(name__icontains=' ' + term))

            def get_keywords(term):
                return Keyword.objects.filter(Q(name__istartswith=term) | Q(name__istartswith=' ' + term))

            querysetList = (Artwork.objects.annotate(
                rank=Case(
                    When(reduce(operator.or_, (Q(title__istartswith=term) for term in terms)), then=Value(2)),
                    When(reduce(operator.or_, (Q(title__icontains=' ' + term) for term in terms)), then=Value(3)),
                    When(reduce(operator.or_, (Q(title__icontains=term) for term in terms)), then=Value(6)),
                    When(reduce(operator.or_, (Q(artists__in=get_artists(term)) for term in terms)), then=Value(1)),
                    When(reduce(operator.or_, (Q(location_of_creation__name__istartswith=term) for term in terms)), then=Value(4)),
                    When(reduce(operator.or_, (Q(keywords__in=get_keywords(term)) for term in terms)), then=Value(5)),
                    default=Value(99),
                    output_field=IntegerField(),
                ))
                .filter(published=True)
                .exclude(rank=99)
                .distinct('id', 'rank', 'title',)
                .order_by('rank', 'title',))
        else:
            # what the user gets, when she isn't using the search at all
            querysetList = (Artwork.objects
                .filter(published=True)
                .order_by('-updated_at'))

    paginator = Paginator(querysetList, 40) # show 40 artworks per page
    pageNr = request.GET.get('page')
    try:
        artworks = paginator.get_page(pageNr)
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
    context['query_location_of_creation'] = query_location_of_creation
    context['query_location_current'] = query_location_current
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
    context['is_staff'] = request.user.is_staff
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
    context['image_original'] = artwork.image_original
    if request.method == "POST":
        form = ArtworkForm(request.POST, request.FILES, instance=artwork)
        if form.is_valid():
            updated_artwork = form.save(commit=False)
            # TODO: artwork.user = request.user
            updated_artwork.updated_at = datetime.now()
            updated_artwork.save()
            # TODO: redirectURL = "%i.json" % artwork.id
            # TODO: reload/close? scroll to thumbnail
            # TODO!!!
            # return redirect('image', id=artwork.id)
            return HttpResponse("<script>window.location=document.referrer;</script>")
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
        collections = qs.filter(user=request.user).order_by('-created_at')
        context['collections'] = collections
        context['artwork'] = artwork
        return render(request, 'artwork/artwork_collect_overlay.html', context)
    if request.method == 'POST':
        artwork = Artwork.objects.get(id=request.POST['artwork-id'])
        if (request.POST['action'] == 'addCollection'):
            col_title = request.POST['collection-title']
            if (col_title):
                u = User.objects.get(id=request.user.id)
                newcol = ArtworkCollection.objects.create(title=col_title, user=u)
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
        col = ArtworkCollection.objects.get(id=id)
        context = {}
        context['title']  = col.title
        context['id']  = col.id
        context['created_by_id'] = col.user.id
        context['created_by_username'] = col.user.get_username()
        context['created_by_fullname'] = col.user.get_full_name()
        context['created_by_userid'] = col.user.id
        context['memberships'] = col.artworkcollectionmembership_set.all()
        context['collections'] = ArtworkCollection.objects.filter(user__groups__name='editor').exclude(user=request.user)
        context['my_collections'] = ArtworkCollection.objects.filter(user=request.user)
        return render(request, 'artwork/collection.html', context)
    if request.method == 'POST':
        # users can only manipulate their own collections via this view
        col = ArtworkCollection.objects.get(id=id)
        if (request.user.id == col.user.id):
            if 'membership-id' in request.POST:
                membership = ArtworkCollectionMembership.objects.get(id=request.POST['membership-id'])
                if not membership:
                    return JsonResponse(status=404, data={'status': 'false', 'message': 'Could not find artwork membership'})
                    # move artwork left
                if (request.POST['action'] == 'left'):
                    membership.move_left()
                    return JsonResponse({'message': 'moved left'})
                    # move artwork right
                if (request.POST['action'] == 'right'):
                    membership.move_right()
                    return JsonResponse({'message': 'moved right'})
                return JsonResponse(status=500, data={'status': 'false', 'message': 'Could not manipulate artwork membership'})
            else:
                leftMember = ArtworkCollectionMembership.objects.get(id=request.POST['member-left'])
                rightMember = ArtworkCollectionMembership.objects.get(id=request.POST['member-right'])
                if (request.POST['action'] == 'connect'):
                    if leftMember.connect(rightMember):
                        return JsonResponse({'message': 'connected'})
                if (request.POST['action'] == 'disconnect'):
                    if leftMember.disconnect(rightMember):
                        return JsonResponse({'message': 'disconnected'})
        else:
            return JsonResponse(status=403, data={'status': 'false', 'message': 'Permission needed'})


@login_required
def collection_json(request, id=None):
    """
    Return collection data in json format.
    """
    col = ArtworkCollection.objects.get(id=id)
    serializer = CollectionSerializer(col)
    return JsonResponse(serializer.data)


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
            # order results by startswith match. see: https://stackoverflow.com/a/48409962
            expression = Q(title__istartswith=self.q) | Q(title__icontains=' ' + self.q)
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


def collection_download_as_pptx_en(request, id=None):
    return collection_download_as_pptx(request, id, 'en')


def collection_download_as_pptx_de(request, id=None):
    return collection_download_as_pptx(request, id, 'de')


def collection_download_as_pptx(request, id=None, language='de'):
    """
    Return a downloadable powerpoint presentation of the collection
    """
    def get_new_slide():
        blank_slide_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_slide_layout)
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(0, 0, 0)
        return slide

    def add_description(slide, description, width, left):
        shapes = slide.shapes
        top = prs.slide_height - textbox_height - padding
        shape = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, textbox_height)
        shape.fill.background()
        shape.line.fill.background()
        text_frame = shape.text_frame
        text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
        text_frame.word_wrap = True
        p = text_frame.paragraphs[0]
        run = p.add_run()
        run.text = description
        font = run.font
        font.size = Pt(30)

    def add_slide_with_one_picture(artwork, padding):
        img_path = artwork.image_original.path
        slide = get_new_slide()
        add_picture_to_slide(slide, img_path, padding, 'center')
        width = prs.slide_width - (padding * 2)
        add_description(slide, artwork.get_description(language), width, padding)

    def add_slide_with_two_pictures(artwork_left, artwork_right, padding):
        img_path_left = artwork_left.image_original.path        
        img_path_right = artwork_right.image_original.path
        slide = get_new_slide()
        add_picture_to_slide(slide, img_path_left, padding, 'left')
        add_picture_to_slide(slide, img_path_right, padding, 'right')
        text_width = int((prs.slide_width - (padding * 2) - distance_between)/2)
        add_description(slide, artwork_left.get_description(language), text_width, padding)
        left = padding + text_width + distance_between
        add_description(slide, artwork_right.get_description(language), text_width, left)

    def add_picture_to_slide(slide, img_path, padding, position):
        pic = slide.shapes.add_picture(img_path, 0, padding)
        image_width = pic.image.size[0]
        image_height = pic.image.size[1]
        aspect_ratio = image_width / image_height

        # calculate width and height
        if (position == 'center'):
            picture_max_width = int(prs.slide_width - (padding * 2))
            if (image_height > image_width):
                pic.height = picture_max_height
                pic.width = int(picture_max_height * aspect_ratio)
            else:
                pic.height = picture_max_height
                pic.width = int(picture_max_height * aspect_ratio)
        else:
            picture_max_width = int((prs.slide_width - (padding * 2) - distance_between)/2)
            if (image_height > image_width):
                pic.height = picture_max_height
                pic.width = int(picture_max_height * aspect_ratio)
            else:
                pic.width = picture_max_width
                pic.height = int(picture_max_width / aspect_ratio)
                pic.top = padding + int((picture_max_height - pic.height) / 2)

        # position the image left/right
        if (position == 'center'):
            pic.left = int((prs.slide_width - pic.width) / 2)
        if (position == 'left'):
            if (image_height < image_width):
                pic.left = int(padding)
            else:
                pic.left = padding + int((picture_max_width - pic.width)/2)
            # pic.left = int(padding + (pic.width / 2))
        if (position == 'right'):
            if (image_height < image_width):
                pic.left = padding + picture_max_width + distance_between
            else:
                pic.left = padding + picture_max_width + distance_between + int((picture_max_width - pic.width)/2)


    # define the presentation dimensions
    prs = Presentation()
    prs.slide_width = 24384000  # taken from Keynote 16:9 pptx
    prs.slide_height = 13716000 # taken from Keynote 16:9 pptx
    padding = int(prs.slide_width / 100)
    textbox_height = prs.slide_height / 10
    picture_max_height = int(prs.slide_height - (padding * 2) - textbox_height)
    distance_between = padding * 2

    col = ArtworkCollection.objects.get(id=id)
    memberships = col.artworkcollectionmembership_set.all()
    connected_member = None
    for membership in memberships:
        if membership.connected_with:
            if not (connected_member):
                connected_member = membership
            else:
                add_slide_with_two_pictures(connected_member.artwork, membership.artwork, padding)
                connected_member = None
        else:
            add_slide_with_one_picture(membership.artwork, padding)

    output = BytesIO()
    prs.save(output)
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    response['Content-Disposition'] = 'attachment; filename="' + slugify(col.title) + '.pptx"'
    output.close()

    return response