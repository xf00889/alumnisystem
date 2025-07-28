from django.core.management.base import BaseCommand
from django.utils.text import slugify
from announcements.models import Category


class Command(BaseCommand):
    help = 'Populate announcement categories'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Campus News', 'description': 'General news and updates about campus activities'},
            {'name': 'Events', 'description': 'Upcoming events and activities for alumni'},
            {'name': 'Career Opportunities', 'description': 'Job postings and career-related announcements'},
            {'name': 'Alumni Spotlight', 'description': 'Featuring successful alumni and their achievements'},
            {'name': 'Fundraising', 'description': 'Fundraising campaigns and donation drives'},
            {'name': 'Volunteer Opportunities', 'description': 'Volunteer opportunities for alumni'},
            {'name': 'Academic Updates', 'description': 'Academic program updates and educational news'},
            {'name': 'Community Service', 'description': 'Community service projects and initiatives'},
        ]

        created_count = 0
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'slug': slugify(category_data['name'])
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories')
        )