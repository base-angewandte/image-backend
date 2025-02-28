# Management Commands

## Available Commands

### `check_image_files`

This command aims to repair incorrect file extensions.

In certain error cases a warning will be issued:

- image file not found.
- image cannot be verified by [Pillow](https://pypi.org/project/pillow/).

### `clean_empty_media_folders`

This command deletes empty media folders in the folder configured in `MEDIA_DIR` (the media directory that gets mounted into Django, set in the `.env` file).

### `clear_artwork_fields`

This command checks the fields `title` & `title_en` of the `Artwork` model and if present removes [non-printable characters](<https://docs.python.org/3/library/stdtypes.html#:~:text=str.isprintable()>) by replacing them with spaces.

### `create_image_fullsize`

This command generates an `image_fullsize` for every artwork, by converting the `image_original` to an image of the same size and in a (standardized) JPEG format with [Pillow](https://pypi.org/project/pillow/).

### `import_external_metadata`

This command maps identifiers from external sources (e.g., GND, Getty, Wikidata) for `Persons`, `Locations` and `Keywords` via CSV files, and updates corresponding entries in the database with external data. For more information, please refer to [Affected fields](external_metadata.md#affected-fields) section in the "External Metadata" chapter.

- It's important to note that the [`gnd_overwrite`-flag](external_metadata.md#overwrite-mechanism) is set a bit differently:
  - By default the flag will be turned on.
  - In case of a name mismatch between the database entry and the fetched GND data, all data will be overwritten, except for the `name` field and the overwrite flag will be turned off.
  - The differing name retrieved from the GND response is added to the first index of the `synonyms` field instead.
  - Editors can review these synonyms to decide whether to update the primary name manually (or by activating the overwrite flag again).

#### Arguments

##### Optional

- `-s, --skip-header`
  Skips the first row of the CSV file if it contains headers.
- `-p, --progress`
  Displays progress updates while processing the file.

##### Positional

- `type`

  The type of data to be imported. Must be one of:

  - `artist`
  - `location`
  - `keyword`

- `file`
  The full path to the CSV file containing the mapping of labels to external source IDs. The file should have the format:

  `name;source_id`

#### Usage examples

A common usage might look like:

`python manage.py import_external_metadata --progress artist artist_data.csv`

This assumes `artist_data.csv` contains a list of person names and their corresponding GND IDs (without any header line in the CSV). For a local development setup, you might want to use a relative path, such as `./data/artist_data.csv`.

For a containerized setup, (temporarily) copy your CSV file (e.g. `artist_data.csv`) into the `src/` directory of the repo and execute the command

`docker compose exec image-django python manage.py import_external_metadata artist artist_data.csv`

### `repair_image_paths`

This command checks all images, if the filenames conform to the latest naming schema. If the filename does not conform, the file (and its references in the database) will be updated to the current schema.

```{note}
In a 2.x install this command should not be needed. But if you are migrating an older Image instance (e.g. from version 1.x), you might need this.
```

### `update_search_vector`

This command updates the search vector for all artworks, which is used for a performant full-text search on artworks. This is useful when a new version with an updated search logic is deployed, as well as in local development.
