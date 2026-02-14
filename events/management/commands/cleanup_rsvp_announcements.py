from django.core.management.base import BaseCommand
from announcements.models import Announcement


class Command(BaseCommand):
    help = 'Remove RSVP confirmation announcements that should be private notifications'

    def handle(self, *args, **options):
        # Find all RSVP confirmation announcements
        rsvp_announcements = Announcement.objects.filter(
            title__startswith='RSVP Confirmation:'
        )
        
        count = rsvp_announcements.count()
        
        if count > 0:
            rsvp_announcements.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully removed {count} RSVP confirmation announcement(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No RSVP confirmation announcements found')
            )
