import shortuuid

from django.db import connection, migrations


def album_id_to_shortuuid(apps, schema_editor):
    cursor = connection.cursor()

    # Add new uuid column to album and fetch all ids
    cursor.execute(
        'ALTER TABLE artworks_album ADD COLUMN uuid VARCHAR(22) DEFAULT NULL;'
    )
    cursor.execute('SELECT id FROM artworks_album;')
    results = cursor.fetchall()
    # Add new uuid colum to tables with foreign keys on album
    cursor.execute(
        'ALTER TABLE artworks_folderalbumrelation ADD COLUMN album_uuid VARCHAR(22) DEFAULT NULL;'
    )
    cursor.execute(
        'ALTER TABLE artworks_permissionsrelation ADD COLUMN album_uuid VARCHAR(22) DEFAULT NULL;'
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
        cursor.execute('UPDATE artworks_album SET uuid = %s WHERE id = %s;', params)
        # Also update the related tables with the new uuids
        cursor.execute(
            'UPDATE artworks_folderalbumrelation SET album_uuid = %s WHERE album_id = %s;',
            params,
        )
        cursor.execute(
            'UPDATE artworks_permissionsrelation SET album_uuid = %s WHERE album_id = %s;',
            params,
        )

    # Drop foreign key constraints on related tables
    query = """
        SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_name = '{}'
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%%album_id%%';
    """
    for table in ['artworks_folderalbumrelation', 'artworks_permissionsrelation']:
        cursor.execute(query.format(table))
        fk_constraint = cursor.fetchone()
        cursor.execute(
            f'ALTER TABLE {table} DROP CONSTRAINT {fk_constraint[0]};'
        )

    # Archive old pk on album and adopt new uuid for it
    cursor.execute('ALTER TABLE artworks_album RENAME COLUMN id TO archive_id;')
    # the constraint name was never updated through the artworkcollection to album migrations:
    cursor.execute(
        'ALTER TABLE artworks_album DROP CONSTRAINT artworks_artworkcollection_pkey;'
    )
    cursor.execute('ALTER TABLE artworks_album ALTER COLUMN archive_id DROP IDENTITY IF EXISTS;')
    cursor.execute('ALTER TABLE artworks_album ALTER COLUMN archive_id DROP NOT NULL;')
    cursor.execute('ALTER TABLE artworks_album ALTER COLUMN archive_id DROP DEFAULT;')
    cursor.execute('ALTER TABLE artworks_album RENAME COLUMN uuid TO id;')
    cursor.execute('ALTER TABLE artworks_album ALTER COLUMN id SET NOT NULL;')
    cursor.execute('ALTER TABLE artworks_album ALTER COLUMN id DROP DEFAULT;')
    cursor.execute('ALTER TABLE artworks_album ADD PRIMARY KEY (id);')

    # Use new uuid field as foreign key id on related tables
    for table in ['artworks_folderalbumrelation', 'artworks_permissionsrelation']:
        cursor.execute(f'ALTER TABLE {table} DROP COLUMN album_id;')
        cursor.execute(f'ALTER TABLE {table} RENAME COLUMN album_uuid TO album_id;')
        cursor.execute(
            f'ALTER TABLE {table} ADD CONSTRAINT {table}_artworks_album_id_fk FOREIGN KEY (album_id) REFERENCES artworks_album (id)'
        )

    # add back unique constraint on (album_id, user_id) for permissionsrelation
    cursor.execute(
        'ALTER TABLE artworks_permissionsrelation ADD CONSTRAINT artworks_permissionsrelation_album_id_user_id_uniq UNIQUE (album_id, user_id);'
    )


def album_id_to_shortuuid_reverse(apps, schema_editor):
    cursor = connection.cursor()

    # for albums created after this migration the archive_id is null,
    # so we'll generate new int ids for them first
    cursor.execute('SELECT MAX(archive_id) FROM artworks_album;')
    result = cursor.fetchone()
    new_id = result[0] + 1 if result[0] else 1
    cursor.execute('SELECT id FROM artworks_album WHERE archive_id IS NULL;')
    results = cursor.fetchall()
    for result in results:
        cursor.execute('UPDATE artworks_album SET archive_id = %s WHERE id = %s', [new_id, result[0]])
        new_id += 1

    # fetch all mappings of old ids to new uuids
    cursor.execute('SELECT id, archive_id FROM artworks_album;')
    results = cursor.fetchall()
    album_uuid_to_id = {result[0]: result[1] for result in results}

    # drop foreign keys on related table and restore old album ids
    for table in ['artworks_folderalbumrelation', 'artworks_permissionsrelation']:
        cursor.execute(
            f'ALTER TABLE {table} DROP CONSTRAINT {table}_artworks_album_id_fk'
        )
        cursor.execute(
            f'ALTER TABLE {table} RENAME COLUMN album_id TO album_uuid;'
        )
        cursor.execute(
            f'ALTER TABLE {table} ADD COLUMN album_id BIGINT;'
        )
        cursor.execute(f'SELECT album_uuid FROM {table};')
        results = cursor.fetchall()
        for result in results:
            cursor.execute(
                f'UPDATE {table} SET album_id = %s WHERE album_uuid = %s;',
                [album_uuid_to_id[result[0]], result[0]],
            )

    # restore old primary key on album
    cursor.execute('ALTER TABLE artworks_album DROP CONSTRAINT artworks_album_pkey;')
    cursor.execute('ALTER TABLE artworks_album DROP COLUMN id;')
    cursor.execute('ALTER TABLE artworks_album RENAME COLUMN archive_id TO id;')
    cursor.execute('ALTER TABLE artworks_album ADD PRIMARY KEY (id);')
    cursor.execute(
        'ALTER TABLE artworks_album RENAME CONSTRAINT artworks_album_pkey TO artworks_artworkcollection_pkey;'
    )
    # and add the auto increment starting with +1 of the highest found id
    cursor.execute('ALTER TABLE artworks_album ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY;')
    cursor.execute('ALTER SEQUENCE artworks_album_id_seq RESTART WITH %s;', [new_id])

    # set foreign keys on related tables and drop temporary uuid fields
    cursor.execute('SET CONSTRAINTS ALL IMMEDIATE;')
    cursor.execute(
        'ALTER TABLE artworks_folderalbumrelation ADD CONSTRAINT artworks_folderalbumrelation_artworks_album_id_fk FOREIGN KEY (album_id) REFERENCES artworks_album (id)'
    )
    cursor.execute(
        'ALTER TABLE artworks_permissionsrelation ADD CONSTRAINT artworks_permissionsrelation_artworks_album_id_fk FOREIGN KEY (album_id) REFERENCES artworks_album (id)'
    )
    cursor.execute('ALTER TABLE artworks_folderalbumrelation DROP COLUMN album_uuid;')
    cursor.execute('ALTER TABLE artworks_permissionsrelation DROP COLUMN album_uuid;')

    # add back unique constraint on (album_id, user_id) for permissionsrelation
    cursor.execute(
        'ALTER TABLE artworks_permissionsrelation ADD CONSTRAINT artworks_permissionsrelation_album_id_user_id_uniq UNIQUE (album_id, user_id);'
    )


class Migration(migrations.Migration):
    dependencies = [
        ('artworks', '0060_alter_album_options'),
    ]

    operations = [
        migrations.RunPython(
            code=album_id_to_shortuuid, reverse_code=album_id_to_shortuuid_reverse
        ),
    ]
