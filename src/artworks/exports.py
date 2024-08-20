import logging
from io import BytesIO

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Pt
from rest_framework import status
from rest_framework.response import Response

from django.conf import settings
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from .models import Album, Artwork, DiscriminatoryTerm

logger = logging.getLogger(__name__)


def album_download_as_pptx(album_id, language='en'):
    """Return a downloadable powerpoint presentation of the album."""

    def get_discriminatory_terms():
        return list(DiscriminatoryTerm.objects.values_list('term', flat=True))

    def strike_through_term(word):
        strike = '\u0036'
        return word[0] + ''.join([char + strike for char in word[1:]])

    def process_text(text, terms):
        words = text.split()
        processed_words = []
        for word in words:
            for term in terms:
                if term.lower() in word.lower():
                    word = strike_through_term(word)
                    break
                processed_words.append(word)

        return ' '.join(processed_words)

    def get_new_slide():
        blank_slide_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_slide_layout)
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(217, 217, 217)
        return slide

    def add_description(slide, description, width, left):
        shapes = slide.shapes
        top = prs.slide_height - textbox_height - prs_padding
        shape = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, textbox_height)
        shape.fill.background()
        shape.line.fill.background()
        text_frame = shape.text_frame
        text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
        text_frame.word_wrap = True
        discriminatory_terms = get_discriminatory_terms()
        processed_description = process_text(description, discriminatory_terms)
        p = text_frame.paragraphs[0]
        run = p.add_run()
        run.text = processed_description
        font = run.font
        font.size = Pt(36)
        font.color.theme_color = MSO_THEME_COLOR.TEXT_1

    def add_slide_with_one_picture(artwork, padding):
        img_relative_path = artwork.image_original.thumbnail[
            '1880x933'  # 1920-20-20 = 1880
        ].name
        img_path = settings.MEDIA_ROOT_PATH / img_relative_path
        slide = get_new_slide()
        add_picture_to_slide(slide, img_path, padding, 'center')
        picture_width = prs.slide_width - (padding * 2)
        add_description(
            slide,
            artwork.get_short_description(language),
            picture_width,
            padding,
        )

    def add_slide_with_two_pictures(artwork_left, artwork_right, padding):
        img_relative_path_left = artwork_left.image_original.thumbnail[
            '920x933'  # (1920/2)-20-20 = 920
        ].name
        img_path_left = settings.MEDIA_ROOT_PATH / img_relative_path_left
        img_relative_path_right = artwork_right.image_original.thumbnail['920x933'].name
        img_path_right = settings.MEDIA_ROOT_PATH / img_relative_path_right
        slide = get_new_slide()
        add_picture_to_slide(slide, img_path_left, padding, 'left')
        add_picture_to_slide(slide, img_path_right, padding, 'right')
        text_width = int((prs.slide_width - (padding * 2) - distance_between) / 2)
        add_description(
            slide,
            artwork_left.get_short_description(language),
            text_width,
            padding,
        )
        left = padding + text_width + distance_between
        add_description(
            slide,
            artwork_right.get_short_description(language),
            text_width,
            left,
        )

    def add_picture_to_slide(slide, img_path, padding, position):
        pic = slide.shapes.add_picture(img_path, 0, padding)
        image_width = pic.image.size[0]
        image_height = pic.image.size[1]
        aspect_ratio = image_width / image_height

        # calculate width and height
        if position == 'center':
            picture_max_width = int(prs.slide_width - (padding * 2))
            space_aspect_ratio = picture_max_width / picture_max_height
            if aspect_ratio < space_aspect_ratio:
                pic.height = picture_max_height
                pic.width = int(picture_max_height * aspect_ratio)
            else:
                pic.width = picture_max_width
                pic.height = int(picture_max_width / aspect_ratio)
                pic.top = padding + int((picture_max_height - pic.height) / 2)
        else:
            picture_max_width = int(
                (prs.slide_width - (padding * 2) - distance_between) / 2,
            )
            space_aspect_ratio = picture_max_width / picture_max_height
            if aspect_ratio < space_aspect_ratio:
                pic.height = picture_max_height
                pic.width = int(picture_max_height * aspect_ratio)
            else:
                pic.width = picture_max_width
                pic.height = int(picture_max_width / aspect_ratio)
                pic.top = padding + int((picture_max_height - pic.height) / 2)

        # position the image left/right
        if position == 'center':
            pic.left = int((prs.slide_width - pic.width) / 2)
        if position == 'left':
            if image_height < image_width:
                pic.left = int(padding)
            else:
                pic.left = padding + int((picture_max_width - pic.width) / 2)
        if position == 'right':
            if image_height < image_width:
                pic.left = padding + picture_max_width + distance_between
            else:
                pic.left = (
                    padding
                    + picture_max_width
                    + distance_between
                    + int((picture_max_width - pic.width) / 2)
                )

    # define the presentation dimensions
    prs = Presentation()
    prs.slide_width = 24384000  # taken from Keynote 16:9 pptx
    prs.slide_height = 13716000  # taken from Keynote 16:9 pptx
    prs_padding = int(prs.slide_width / 96)  # full HD: 1920px/96 = 20px
    textbox_height = prs.slide_height / 10
    picture_max_height = int(prs.slide_height - (prs_padding * 2) - textbox_height)
    distance_between = prs_padding * 2

    try:
        col = Album.objects.get(id=album_id)
    except Album.DoesNotExist:
        logger.warning('Could not create powerpoint file. Collection missing.')
        return

    slides = col.slides
    if slides:
        for slide in slides:
            try:
                if len(slide) == 2:
                    add_slide_with_two_pictures(
                        Artwork.objects.get(id=slide[0].get('id')),
                        Artwork.objects.get(id=slide[1].get('id')),
                        prs_padding,
                    )

                elif len(slide) == 1:
                    for artwork_in_slide in slide:
                        artwork = Artwork.objects.get(id=artwork_in_slide.get('id'))
                        add_slide_with_one_picture(artwork, prs_padding)

                else:
                    return Response(
                        _(
                            'Too many artworks per slides. You can only have two artworks per slide. Please edit slides.',
                        ),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            except Artwork.DoesNotExist:
                return Response(
                    _(
                        f'There is no artwork associated with id {artwork_in_slide.get("id")}.',
                    ),
                    status=status.HTTP_404_NOT_FOUND,
                )

            except FileNotFoundError:
                return Response(
                    _(
                        f"There is no image associated with artwork with id {artwork_in_slide.get('id')}; it's a directory",
                    ),
                    status=status.HTTP_404_NOT_FOUND,
                )

    output = BytesIO()
    prs.save(output)
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    )
    response['Content-Disposition'] = (
        'attachment; filename="' + slugify(col.title) + '.pptx"'
    )
    output.close()

    return response
