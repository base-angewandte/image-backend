# External Metadata

One of the main models of Image are `Person`, `Keyword` and `Location`.
To avoid manual administrative effort, metadata is added automatically from the [GND Database](https://www.dnb.de/EN/Professionell/Standardisierung/GND/gnd_node.html) (aka. the Integrated Authority File of the German National Library), the [Art & Architecture Thesaurus](https://vocab.getty.edu/aat/) of the [Getty Research Institute](https://www.getty.edu) or [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page), if a valid external source ID is provided.

## Affected fields

The following fields of the `Person` model are automatically filled in from the GND Database:

- `name`
- `synonyms`
- `date_birth`
- `date_death`

The following fields of the `Location` model are automatically filled in from the GND Database & Wikidata:

- `name`
- `name_en` (extracted from Wikidata if a valid Wikidata ID is provided via GND)
- `synonyms`

The following fields of the `Keyword` model are automatically filled in from the Getty Database:

- `name_en`

All responses from external APIs are saved in the `external_metadata` field belonging to the respective model.

### Overwrite mechanism

Depending on the used overwrite flag by the model, their respective fields are updated automatically.
Both the fields of `Location` and `Person` are updated depending on the status of `gnd_overwrite`.
`Keyword`'s fields are updated according to the status of the `getty_overwrite` flag.

- If `gnd_overwrite` flag is turned on:
  - The system automatically updates relevant fields with metadata from the GND Database.
  - Any existing values in these fields will be replaced with the imported GND metadata.
  - This is the default state for entries.
- If `gnd_overwrite` flag is turned off:
  - The system preserves the existing data and prevents updates from the GND import process. But it stores the full API response in the `external_metadata` field.

The `getty_overwrite` flag functions similarly to `gnd_overwrite`:

- Only the `name_en` field is updated, if available, allowing for the inclusion of translated keywords from the Getty Vocabulary Database.
