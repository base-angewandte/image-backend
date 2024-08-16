import argparse
import csv
import re

import requests

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from artworks.models import Keyword, Location, Person


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
        # Validate gnd/getty ids with the regexes
        if data_type in ['artist', 'location']:
            invalid_ids = [
                f'{entry[1]} for {entry[0]}'
                for entry in entries
                if not re.match(
                    settings.GND_ID_REGEX,
                    entry[1],
                )
            ]
        else:
            invalid_ids = [
                f'{entry[1]} for {entry[0]}'
                for entry in entries
                if not re.match(
                    settings.GETTY_ID_REGEX,
                    entry[1],
                )
            ]
        if invalid_ids:
            raise CommandError(
                f'Your dataset contains the following invalid {settings.GND_LABEL} IDs:\n'
                + '\n'.join(invalid_ids),
            )
        # entries_not_found: initialize the Artist model and check
        # if the name from the csv file of the artist exists in the db
        entries_not_found = []
        # indistinct_names: add all double entries of an artist's name from the db to the list
        indistinct_names = []
        data_not_found = []
        request_errors = []
        # updated: if the name generated from the GND data doesn't differ from the one originally stored in image,
        # we update the whole entry, including the name and if not we update without the name
        updated = []
        updated_without_name = []
        validation_errors = []
        integrity_errors = []
        count = 0
        total = len(entries)
        for entry in entries:
            if options['show_progress'] and count % 10 == 0:
                self.stdout.write(f'[status] {count} of {total} processed')
            count += 1

            # Check if the data exists in the corresponding model and handle special cases
            Model = {  # noqa: N806
                'artist': Person,
                'location': Location,
                'keyword': Keyword,
            }[data_type]

            try:
                instance = Model.objects.get(name=entry[0])
            except Model.DoesNotExist:
                entries_not_found.append(entry)
                continue
            except Model.MultipleObjectsReturned:
                indistinct_names.append(entry)
                continue

            # Retrieve external metadata
            gnd_url = f'{settings.GND_API_BASE_URL}{entry[1]}'
            getty_url = f'{entry[1]}.json'
            url = {
                'artist': gnd_url,
                'location': gnd_url,
                'keyword': getty_url,
            }[data_type]

            try:
                response = requests.get(
                    url,
                    timeout=settings.REQUESTS_TIMEOUT,
                )
            except requests.RequestException:
                request_errors.append(entry)
                continue
            if response.status_code != 200:
                if response.status_code == 404:
                    data_not_found.append(entry)
                else:
                    request_errors.append(entry)
                continue
            data = response.json()

            # Process retrieved data
            if data_type in ['artist', 'location']:
                instance.gnd_id = entry[1]
                instance.gnd_overwrite = True
                instance.update_with_gnd_data(data)

                # if the name generated from the GND data differs from the one
                # originally stored in image, we restore the old name and
                # deactivate the gnd_overwrite flag
                if instance.name != entry[0]:
                    instance.name = entry[0]
                    instance.gnd_overwrite = False
                    updated_without_name.append(entry)
                else:
                    updated.append(entry)

                try:
                    instance.save()
                except ValidationError as ve:
                    if data_type == 'artist':
                        # try to store potentially invalid dates in date_display first
                        # this can happen if a date has valid format but is not a real
                        # calendar date (e.g. a Feb. 29 in a non-leap-year)
                        try:
                            instance.date_display = (
                                f'{instance.date_birth} - {instance.date_death}'
                            )
                            instance.date_birth = None
                            instance.date_death = None
                            instance.save()
                        except ValidationError as e:
                            validation_errors.append((entry, repr(e)))
                    else:
                        validation_errors.append((entry, repr(ve)))
                except IntegrityError as e:
                    integrity_errors.append((entry, repr(e)))
            elif data_type == 'keyword':
                instance.getty_id = entry[1]
                instance.getty_overwrite = True
                instance.update_with_getty_data(data)

                # if the name generated from the Getty AAT differs from the one
                # originally stored in image, we restore the old name and
                # deactivate the getty_overwrite flag
                if instance.name != entry[0]:
                    instance.name = entry[0]
                    instance.getty_overwrite = False
                    updated_without_name.append(entry)
                else:
                    updated.append(entry)

                try:
                    instance.save()
                except IntegrityError as e:
                    integrity_errors.append((entry, repr(e)))

        self.stdout.write(f'Updated {len(updated)} entries.')
        self.stdout.write(
            f'Updated {len(updated_without_name)} entries, without overwriting the name.',
        )
        # all checks: if the there are entries in the initialized lists from above,
        # write out there elements/length/count.
        if entries_not_found:
            self.stdout.write(
                self.style.WARNING(
                    f'No {data_type} with matching name found in {len(entries_not_found)} cases:',
                ),
            )
            for entry in entries_not_found:
                self.stdout.write(f'{entry[0]} with ID {entry[1]}')
        if indistinct_names:
            self.stdout.write(
                self.style.WARNING(
                    f'Duplicate name entries found in {len(indistinct_names)} cases:',
                ),
            )
            for entry in indistinct_names:
                self.stdout.write(entry[0])
        if data_not_found:
            label = {
                'artist': settings.GND_LABEL,
                'location': settings.GND_LABEL,
                'keyword': settings.GETTY_LABEL,
            }[data_type]

            self.stdout.write(
                self.style.WARNING(
                    f'No {label} entry found for {len(data_not_found)} IDs:',
                ),
            )
            for entry in data_not_found:
                self.stdout.write(f'{entry[1]} for {entry[0]}')
        if request_errors:
            self.stdout.write(
                self.style.ERROR(f'Request error for {len(request_errors)} entries:'),
            )
            for entry in request_errors:
                self.stdout.write(f'{entry[1]} for {entry[0]}')
        if validation_errors:
            self.stdout.write(
                self.style.ERROR(
                    f'Validation error for {len(validation_errors)} entries:',
                ),
            )
            for entry in validation_errors:
                self.stdout.write(f'{entry[0][1]} {entry[0][0]}: {entry[1]}')
        if integrity_errors:
            self.stdout.write(
                self.style.ERROR(
                    f'Integrity error for {len(integrity_errors)} entries:',
                ),
            )
            for entry in integrity_errors:
                self.stdout.write(f'{entry[0][1]} {entry[0][0]}: {entry[1]}')
