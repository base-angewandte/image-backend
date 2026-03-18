from django.core.management.base import BaseCommand
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone


class Command(BaseCommand):
    help = 'Initialize the custom user model app, to deal with migration dependencies.'

    def handle(self, *args, **options):
        migration = MigrationRecorder.Migration.objects.filter(
            app='accounts',
            name='0001_initial',
        )
        if migration.exists():
            self.stdout.write(
                self.style.WARNING(
                    '0001_initial already exists.',
                ),
            )
        else:
            MigrationRecorder.Migration.objects.create(
                app='accounts',
                name='0001_initial',
                applied=timezone.now(),
            )
            self.stdout.write(
                self.style.SUCCESS(
                    '0001_initial migration was successfully fake-applied, continue now with normal migration process.',
                ),
            )
