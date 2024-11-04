import shortuuid

from django.db import connection, migrations

artwork_relationship_tables = [
    'artworks_artwork_artists',
    'artworks_artwork_authors',
    'artworks_artwork_discriminatory_terms',
    'artworks_artwork_graphic_designers',
    'artworks_artwork_keywords',
    'artworks_artwork_material',
    'artworks_artwork_photographers',
    'artworks_artwork_place_of_production',
]


def artwork_id_to_shortuuid(apps, schema_editor):
    cursor = connection.cursor()

    # Add new uuid column to artwork and fetch all ids
    cursor.execute(
        'ALTER TABLE artworks_artwork ADD COLUMN uuid VARCHAR(22) DEFAULT NULL;'
    )
    cursor.execute('SELECT id FROM artworks_artwork;')
    results = cursor.fetchall()
    # Add new uuid colum to tables with foreign keys on artwork
    for table in artwork_relationship_tables:
        cursor.execute(
            f'ALTER TABLE {table} ADD COLUMN artwork_uuid VARCHAR(22) DEFAULT NULL;'
        )

    # Generate new ShortUUIDs and update all album rows
    uuids = []
    while len(uuids) < len(results):
        new_uuid = shortuuid.uuid()
        # theoretically there could be a uuid collision, so make sure every one is unique
        while new_uuid in uuids:
            new_uuid = shortuuid.uuid()
        uuids.append(new_uuid)
    for i, result in enumerate(results):
        params = [uuids[i], result[0]]
        cursor.execute('UPDATE artworks_artwork SET uuid = %s WHERE id = %s;', params)
        # Also update the related tables with the new uuids
        for table in artwork_relationship_tables:
            cursor.execute(
                f'UPDATE {table} SET artwork_uuid = %s WHERE artwork_id = %s;',
                params,
            )

    # Drop foreign key constraints on related tables
    query = """
        SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_name = '{}'
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%%artwork_id%%';
    """
    for table in artwork_relationship_tables:
        cursor.execute(query.format(table))
        fk_constraint = cursor.fetchone()
        cursor.execute(
            f'ALTER TABLE {table} DROP CONSTRAINT {fk_constraint[0]};'
        )

    # Archive old pk on artwork and adopt new uuid for it
    cursor.execute('ALTER TABLE artworks_artwork RENAME COLUMN id TO archive_id;')
    cursor.execute('ALTER TABLE artworks_artwork ALTER COLUMN archive_id DROP IDENTITY IF EXISTS;')
    cursor.execute('ALTER TABLE artworks_artwork DROP CONSTRAINT artworks_artwork_pkey;')
    cursor.execute('ALTER TABLE artworks_artwork ALTER COLUMN archive_id DROP NOT NULL;')
    cursor.execute('ALTER TABLE artworks_artwork ALTER COLUMN archive_id DROP DEFAULT;')
    cursor.execute('ALTER TABLE artworks_artwork RENAME COLUMN uuid TO id;')
    cursor.execute('ALTER TABLE artworks_artwork ALTER COLUMN id SET NOT NULL;')
    cursor.execute('ALTER TABLE artworks_artwork ALTER COLUMN id DROP DEFAULT;')
    cursor.execute('ALTER TABLE artworks_artwork ADD PRIMARY KEY (id);')

    # Use new uuid field as foreign key id on related tables
    for table in artwork_relationship_tables:
        cursor.execute(f'ALTER TABLE {table} DROP COLUMN artwork_id;')
        cursor.execute(f'ALTER TABLE {table} RENAME COLUMN artwork_uuid TO artwork_id;')
        cursor.execute(
            f'ALTER TABLE {table} ADD CONSTRAINT {table}_artwork_id_fk FOREIGN KEY (artwork_id) REFERENCES artworks_artwork (id)'
        )


def artwork_id_to_shortuuid_reverse(apps, schema_editor):
    cursor = connection.cursor()

    # for artworks created after this migration the archive_id is null,
    # so we'll generate new int ids for them first
    cursor.execute('SELECT MAX(archive_id) FROM artworks_artwork;')
    result = cursor.fetchone()
    new_id = result[0] + 1 if result[0] else 1
    cursor.execute('SELECT id FROM artworks_artwork WHERE archive_id IS NULL;')
    results = cursor.fetchall()
    for result in results:
        cursor.execute('UPDATE artworks_artwork SET archive_id = %s WHERE id = %s', [new_id, result[0]])
        new_id += 1

    # fetch all mappings of old ids to new uuids
    cursor.execute('SELECT id, archive_id FROM artworks_artwork;')
    results = cursor.fetchall()
    artwork_uuid_to_id = {result[0]: result[1] for result in results}

    # drop foreign keys on related table and restore old album ids
    for table in artwork_relationship_tables:
        cursor.execute(
            f'ALTER TABLE {table} DROP CONSTRAINT {table}_artwork_id_fk'
        )
        cursor.execute(
            f'ALTER TABLE {table} RENAME COLUMN artwork_id TO artwork_uuid;'
        )
        cursor.execute(
            f'ALTER TABLE {table} ADD COLUMN artwork_id BIGINT;'
        )
        cursor.execute(f'SELECT artwork_uuid FROM {table};')
        results = cursor.fetchall()
        for result in results:
            cursor.execute(
                f'UPDATE {table} SET artwork_id = %s WHERE artwork_uuid = %s;',
                [artwork_uuid_to_id[result[0]], result[0]],
            )

    # restore old primary key on album
    cursor.execute('ALTER TABLE artworks_artwork DROP CONSTRAINT artworks_artwork_pkey;')
    cursor.execute('ALTER TABLE artworks_artwork DROP COLUMN id;')
    cursor.execute('ALTER TABLE artworks_artwork RENAME COLUMN archive_id TO id;')
    cursor.execute('ALTER TABLE artworks_artwork ADD PRIMARY KEY (id);')
    # and add the auto increment starting with +1 of the highest found id
    cursor.execute('ALTER TABLE artworks_artwork ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY;')
    cursor.execute('ALTER SEQUENCE artworks_artwork_id_seq RESTART WITH %s;', [new_id])

    # set foreign keys on related tables and drop temporary uuid fields
    cursor.execute('SET CONSTRAINTS ALL IMMEDIATE;')
    for table in artwork_relationship_tables:
        cursor.execute(
            f'ALTER TABLE {table} ADD CONSTRAINT {table}_artwork_id_fk FOREIGN KEY (artwork_id) REFERENCES artworks_artwork (id)'
        )
        cursor.execute(f'ALTER TABLE {table} DROP COLUMN artwork_uuid;')


def update_slides_to_uuid(apps, schema_editor):
    Album = apps.get_model('artworks', 'Album')
    cursor = connection.cursor()
    cursor.execute('SELECT archive_id, id FROM artworks_artwork;')
    results = cursor.fetchall()
    artwork_id_map = {result[0]: result[1] for result in results}

    for album in Album.objects.all():
        for slide in album.slides:
            for item in slide['items']:
                item['id'] = artwork_id_map[item['id']]
        album.save()


def update_slides_to_uuid_reverse(apps, schema_editor):
    Album = apps.get_model('artworks', 'Album')
    cursor = connection.cursor()
    cursor.execute('SELECT id, archive_id FROM artworks_artwork;')
    results = cursor.fetchall()
    artwork_uuid_map = {result[0]: result[1] for result in results}

    for album in Album.objects.all():
        for slide in album.slides:
            for item in slide['items']:
                item['id'] = artwork_uuid_map[item['id']]
        album.save()


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0095_alter_artwork_options'),
    ]

    operations = [
        migrations.RunPython(
            code=artwork_id_to_shortuuid, reverse_code=artwork_id_to_shortuuid_reverse
        ),
        migrations.RunPython(
            code=update_slides_to_uuid, reverse_code=update_slides_to_uuid_reverse
        ),
    ]
