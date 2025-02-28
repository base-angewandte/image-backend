# Overview (reduced version)

[Image](https://imageplus.at/about-image) is a image database used as a platform for open art education.
Technically it is a web application developed with Django.

At the core of Image are artworks, which are image files with some additional metadata (title, material, etc.). An artwork can be associated with one or more persons (who can have the following roles: artists, photographers, authors, graphic designers), keywords and locations.
Users can create albums. Artworks can be added to one or more albums. Artworks can be added multiple times to albums. The user can provide `VIEW` and `EDIT` rights to other users, who then in turn can view or add/remove artworks to said album.
Users can sort the artworks inside their own albums to put them into a particular order. Users can export an album as a Powerpoint presentation (.pptx) or a PDF file (.pdf). If the user wants to show two artworks on one single slide, they can _connect_ two artworks inside the album.
A user can search for a specific artwork either with a full-text search or an advanced search. Within the advanced search the user can search by title, artist, place of production, location, keywords and date of creation.

## Historical Background

In spring 2018 it was decided that an alternative to the rather costly image database »EasyDB« was needed.

The following list of criteria and features was assembled:

- web-based photo organizing
- tags and/or metadata
- export as PowerPoint-presentation (pptx)
- basic authorisation/rights management capabilities
- collections per course
- view mode for students
- search with filters
- preview of PowerPoint-presentation with possibility to add multiple pictures to one slide migration

In summer 2018 an external developer-designer (Armin B. Wagner) was hired to plan out and implement a corresponding system together with the base Dev Team. Image 1.0 was launched in May 2019.

During the [image+ Platform for Open Art Education](https://imageplus.at) project running from September 2020 to December 2024, a major overhaul of the entire system was developed, and Image 2.0 was released in 2025 as a fully open source software project. The backend is still based on the old Image 1.X Django application. It is used by the editors to curate all artworks and additional data, and it provides a newly implemented REST API, which is used by the new Image frontend that was developed using Vue.js.
