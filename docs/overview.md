# Overview

## Historical Background
In spring 2018 it was decided that an alternative to the rather costly image database »EasyDB« was needed.
The following list of criteria and features was assembled:
* web-based photo organizing
* tags and/or metadata
* export as PowerPoint-presentation (pptx)
* basic authorisation/rights management capabilities
* collections per course
* view mode for students
* search with filters
* preview of PowerPoint-presentation with possibility to add multiple pictures to one slide migration

In summer 2018 and external developer-designer (the author) was hired to plan out and implement a corresponding system.

## System Components
The implemented system is based on **django** ([version 2.0.6](https://docs.djangoproject.com/en/2.0/) at the time of writing) - an open source Python web framework. Django already found use by the internal development team of the Angewandte when they build the **Base Recherche**. Using the same framework -- so the idea -- should make the post-launch handover and later maintenance easier.

The django web app is internally called *artdb*. It is **dockerized** and it connects to a **PostgreSQL** database.

## Django Models
An **artwork** is basically just an image with some addtional data (title, material, etc.). An artwork can be associated with one or more **artists**, **keywords** and **locations**.
Users can **collect** artworks. They can create **collections**. They can add artworks to multiple collections. Users can put the artworks inside their own collections into a particular order.
Users can export a collection in the form of a pptx file. If the user wants to show two artworks on one single powerpoint slide, she can *connect* two artworks inside the collection.

## Static and dynamic pages
The django web app is mainly serving relatively static pages, which are defined by the following templates (and a few smaller supporting ones):
* `/artdb/templates/base.html` - the basic page skeleton
* `/artdb/templates/artwork/thumbnailbrowser.html` - the main page showing thumbnails
* `/artdb/templates/artwork/collections_list.html` - a listing of collections

Apart from those pages, there are several **overlays**. These overlays are not served as stand-alone pages. Instead they are loaded via javascript and put inside empty divs defined in the `base.html` template. When an overlay gets shown, the content *beneath* is removed via css (`display: none`). When the user closes the overlay, the content beneath appears again. No reload necessary.

**A webframework/library such as Angular or React was not used.** The empty divs are filled by simply loading static overlay templates via **jQuery**.
* `artwork_detail_overlay.html` gets loaded when the user clicks twice on an artwork’s thumbnail.
* `artwork_collect_overlay.html` gets loaded when the user wants to add an artwork to a collection.
* `artwork_edit_overlay.html` gets loaded when the user wants to edit an artwork.
* `collection_edit_overlay.html` gets loaded when the user wants to edit a collection.

Most javascript functions are defined in the following file: `/artdb/static_dev/js/artworks.js`. This file defines, among other things, a relatively complex function called *updateInspector()*. The inspector -- the dark sidebar on the right -- gets updated whenever the user selects an artwork by clicking on it once. Instead of reloading the whole static page, only the inspector gets updated via javascript. The necessary data is provided via JSON (see: <https://base.uni-ak.ac.at/image/artwork/17014.json>)

Some templates also bring their own javascript to provide additional template specific functionalities. `collection.html` uses a rather large function called `updateSlides()`. The user is able to move and connect artworks. Instead of reloading the whole static page whenever a change happens, only the data of the collection gets reloaded (see: <https://base.uni-ak.ac.at/image/collection/1.json>). Then all the thumbnails get constructed anew.

## Notable Third Party Django Packages
### django-versatileimagefield
<https://github.com/respondcreate/django-versatileimagefield> - Replacement of Django's ImageField that allows to create new image versions (renditions) from the one assigned to the field.
Thumbnails and images shown in the detail view are created on demand. Please note: all images, the original uploaded ones as well as the renditions, are stored in a specific file structure. This file structure was adopted from EasyDB and is defined in `/artdb/artworks/models.py` (see: `get_path_to_original_file()` and `move_uploaded_image()`).

### django-mptt
<https://github.com/django-mptt/django-mptt> - Utilities for implementing a modified pre-order traversal tree in django. This one is used to implement the hierarchical structure needed for **locations** (Holland->Amsterdam->Galerie Monet). It is also used to preserve the hierarchical structure of the **keywords** (potentially useful later on).

### django-ordered-model
<https://github.com/bfirsh/django-ordered-model> - This one makes **collections** orderable.

### django-mass-edit
<https://github.com/burke-software/django-mass-edit> - Allows to edit multiple records at once via the admin interface.

### django-autocomplete-light
<https://github.com/yourlabs/django-autocomplete-light> - Provides autocomplete functionality for various input and selection fields.