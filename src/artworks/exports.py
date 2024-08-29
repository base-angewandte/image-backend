import logging
import re
from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Pt
from rest_framework import status
from rest_framework.response import Response

from django.conf import settings
from django.db.models.functions import Length
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from .models import Album, Artwork

logger = logging.getLogger(__name__)


def album_download_as_pptx(album_id, language='en'):
    """Return a downloadable powerpoint presentation of the album."""

    def apply_strike_through_and_formatting(p, matched_term, discriminatory_term):
        leading_punct = ''
        trailing_punct = ''
        # Check for leading punctuation
        if matched_term[0] in ['"', "'", '(', '[', '{']:
            leading_punct = matched_term[0]
            matched_term = matched_term[1:]

        # Check for trailing punctuation
        if matched_term[-1] in ['"', "'", ')', ']', '}', ',']:
            trailing_punct = matched_term[-1]
            matched_term = matched_term[:-1]

        # Add leading punctuation if it exists
        if leading_punct:
            run_leading_punct = p.add_run()
            run_leading_punct.text = leading_punct
            font = run_leading_punct.font
            font.size = Pt(36)
            font.color.theme_color = MSO_THEME_COLOR.TEXT_1

        # Add first letter to run with normal formatting
        first_letter_run = p.add_run()
        first_letter_run.text = matched_term[:1]
        font = first_letter_run.font
        font.size = Pt(36)
        font.color.theme_color = MSO_THEME_COLOR.TEXT_1

        # Find the position of the discriminatory term in the term
        start_index = matched_term.lower().find(discriminatory_term.lower())
        end_index = start_index + len(discriminatory_term)

        # Strike through the discriminatory part of the term
        run_rest_of_term = p.add_run()
        run_rest_of_term.text = matched_term[start_index + 1 : end_index]
        font = run_rest_of_term.font
        font.size = Pt(36)
        font.color.theme_color = MSO_THEME_COLOR.TEXT_1
        run_rest_of_term.font._element.attrib['strike'] = 'sngStrike'
        run_rest_of_term.font._element.attrib['baseline'] = '-25000'

        # Handle any remaining text (after the discriminatory term)
        remaining_text = matched_term[end_index:]
        if remaining_text:
            run_remaining = p.add_run()
            run_remaining.text = remaining_text
            font = run_remaining.font
            font.size = Pt(36)
            font.color.theme_color = MSO_THEME_COLOR.TEXT_1

        # Add trailing punctuation if it exists
        if trailing_punct:
            run_trailing_punct = p.add_run()
            run_trailing_punct.text = trailing_punct + ' '
            font = run_trailing_punct.font
            font.size = Pt(36)
            font.color.theme_color = MSO_THEME_COLOR.TEXT_1

    def get_new_slide():
        blank_slide_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_slide_layout)
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(217, 217, 217)
        return slide

    def add_description(slide, artwork, width, left):
        shapes = slide.shapes
        top = prs.slide_height - textbox_height - prs_padding
        shape = shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, textbox_height)
        shape.fill.background()
        shape.line.fill.background()
        text_frame = shape.text_frame
        text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
        text_frame.word_wrap = True
        description = artwork.get_short_description(language)
        discriminatory_terms = artwork.discriminatory_terms.order_by(
            Length('term').asc(),
        )
        p = text_frame.paragraphs[0]
        description_words = description.split()
        for word in description_words:
            matched = False
            for term in discriminatory_terms:
                if re.search(term.term, word, flags=re.IGNORECASE):
                    apply_strike_through_and_formatting(p, word, term.term)
                    matched = True
                    break
            if not matched:
                run = p.add_run()
                run.text = word + ' '
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
            artwork,
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
            artwork_left,
            text_width,
            padding,
        )
        left = padding + text_width + distance_between
        add_description(
            slide,
            artwork_right,
            text_width,
            left,
        )

    def add_picture_to_slide(slide, img_path: Path, padding, position):
        pic = slide.shapes.add_picture(img_path.as_posix(), 0, padding)
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
