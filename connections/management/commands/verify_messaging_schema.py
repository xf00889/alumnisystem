"""Read-only deployment preflight for private-message schema readiness.

Usage: python manage.py verify_messaging_schema
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = 'Verify the private-message schema migration required by the messaging inbox.'

    def handle(self, *args, **options):
        database = connections['default']
        try:
            recorder = MigrationRecorder(database)
            applied = ('connections', '0004_private_message_attachments') in recorder.applied_migrations()
            with database.cursor() as cursor:
                table = 'connections_directmessage'
                columns = {
                    item.name for item in database.introspection.get_table_description(cursor, table)
                }
        except Exception as error:
            raise CommandError('Unable to inspect the messaging database. Check database connectivity and server logs.') from error

        expected = {'attachment_token', 'attachment_display_name'}
        missing = expected - columns
        if not applied or missing:
            details = []
            if not applied:
                details.append('connections.0004_private_message_attachments has not been applied')
            if missing:
                details.append('missing database columns: ' + ', '.join(sorted(missing)))
            raise CommandError(
                'The deployed messaging schema is not ready (' + '; '.join(details) + '). '
                'Back up the database, review migration state, then run python manage.py migrate. '
                'Do not fake a migration or change the live schema manually.'
            )
        self.stdout.write(self.style.SUCCESS('Messaging schema verified: migration and required columns are present.'))
