import argparse
import csv
import re
from datetime import datetime

import requests

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from artworks.models import Artist


class Command(BaseCommand):
    help = 'Import data from external sources (e.g. GND) for Artists, Locations and Keywords'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--skip-header',
            dest='skip_header',
            action='store_true',
            help='Skip header row',
        )
        parser.set_defaults(skip_header=False)
        parser.add_argument(
            '-p',
            '--progress',
            dest='show_progress',
            action='store_true',
            help='Show progress information',
        )
        parser.set_defaults(show_progress=False)
        parser.add_argument(
            'type',
            type=str,
            help='The type of data that should be imported',
            choices=['artist', 'location', 'keyword'],
        )
        parser.add_argument(
            'file',
            type=argparse.FileType('r'),
            help='CSV file containing the mapping of labels to external source IDs',
        )

    def handle(self, *args, **options):
        file = options['file']
        data_type = options['type']
        entries = []

        reader = csv.reader(file, delimiter=';')
        header = True
        for row in reader:
            if header and options['skip_header']:
                header = False
                continue
            entries.append([row[0].strip(), row[1].strip()])

        if data_type == 'artist':
            invalid_ids = []
            for entry in entries:
                if not re.match(
                    r'^(1[0123]?\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X])$',
                    entry[1],
                ):
                    invalid_ids.append(f'{entry[1]} for {entry[0]}')
            if invalid_ids:
                raise CommandError(
                    'Your dataset contains the following invalid GND IDs:\n'
                    + '\n'.join(invalid_ids)
                )

            artists_not_found = []
            indistinct_names = []
            gnd_data_not_found = []
            request_errors = []
            updated = []
            updated_without_name = []
            count = 0
            total = len(entries)
            for entry in entries:
                if options['show_progress'] and count % 10 == 0:
                    self.stdout.write(f'[status] {count} of {total} processed')
                count += 1

                try:
                    artist = Artist.objects.get(name=entry[0])
                except Artist.DoesNotExist:
                    artists_not_found.append(entry)
                    continue
                except Artist.MultipleObjectsReturned:
                    indistinct_names.append(entry)
                    continue

                try:
                    response = requests.get(
                        settings.GND_API_BASE_URL + entry[1],
                        timeout=settings.REQUESTS_TIMEOUT,
                    )
                except requests.RequestException:
                    request_errors.append(entry)
                    continue

                if response.status_code != 200:
                    if response.status_code == 404:
                        gnd_data_not_found.append(entry)
                    else:
                        request_errors.append(entry)
                    continue

                gnd_data = response.json()
                artist.gnd_id = entry[1]
                artist.external_metadata['gnd'] = {
                    'date_requested': datetime.now().isoformat(),
                    'response_data': gnd_data,
                }
                artist.set_name_from_gnd_data(gnd_data)
                artist.set_synonyms_from_gnd_data(gnd_data)
                artist.set_birth_death_from_gnd_data(gnd_data)

                # if the name generated from the GND data differs from the one
                # originally stored in image, we restore the old name and
                # deactivate the gnd_overwrite flag
                if artist.name != entry[0]:
                    artist.name = entry[0]
                    artist.gnd_overwrite = False
                    updated_without_name.append(entry)
                else:
                    updated.append(entry)

                artist.save()

            self.stdout.write(f'Updated {len(updated)} entries.')
            self.stdout.write(
                f'Updated {len(updated_without_name)} entries, without overwriting the name.'
            )
            self.stdout.write(
                self.style.WARNING(
                    f'No Artist with matching name found in {len(artists_not_found)} cases:'
                )
            )
            for entry in artists_not_found:
                self.stdout.write(f'{entry[0]} with GND ID {entry[1]}')
            self.stdout.write(
                self.style.WARNING(
                    f'Duplicate artist names found in {len(artists_not_found)} cases:'
                )
            )
            for entry in artists_not_found:
                self.stdout.write(entry[0])
            self.stdout.write(
                self.style.WARNING(
                    f'No GND entry found for {len(gnd_data_not_found)} IDs:'
                )
            )
            for entry in gnd_data_not_found:
                self.stdout.write(f'{entry[1]} for {entry[0]}')
            self.stdout.write(
                self.style.WARNING(f'Request error for {len(request_errors)} entries:')
            )
            for entry in request_errors:
                self.stdout.write(f'{entry[1]} for {entry[0]}')

        elif data_type == 'location':
            raise CommandError('Importing location metadata is not yet implemented.')

        elif data_type == 'keyword':
            raise CommandError('Importing keyword metadata is not yet implemented.')
