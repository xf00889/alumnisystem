from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from jobs.models import JobPosting, JobApplication

class Command(BaseCommand):
    help = 'Creates HR group and assigns necessary permissions'

    def handle(self, *args, **options):
        # Create HR group
        hr_group, created = Group.objects.get_or_create(name='HR')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created HR group'))
        else:
            self.stdout.write('HR group already exists')
            
        # Get content types
        job_ct = ContentType.objects.get_for_model(JobPosting)
        application_ct = ContentType.objects.get_for_model(JobApplication)
        
        # Define permissions that HR should have
        permissions = [
            # JobPosting permissions
            Permission.objects.get(codename='add_jobposting', content_type=job_ct),
            Permission.objects.get(codename='change_jobposting', content_type=job_ct),
            Permission.objects.get(codename='view_jobposting', content_type=job_ct),
            # JobApplication permissions
            Permission.objects.get(codename='view_jobapplication', content_type=application_ct),
            Permission.objects.get(codename='change_jobapplication', content_type=application_ct),
        ]
        
        # Assign permissions to group
        hr_group.permissions.add(*permissions)
        
        self.stdout.write(self.style.SUCCESS('Successfully set up HR group permissions')) 