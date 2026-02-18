from django.core.management.base import BaseCommand
from django.utils.text import slugify
from announcements.models import Category
from django.db import transaction


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
        updated_count = 0
        
        try:
            with transaction.atomic():
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
                            self.style.SUCCESS(f'✅ Created category: {category.name}')
                        )
                    else:
                        # Update existing category if needed
                        if category.description != category_data['description']:
                            category.description = category_data['description']
                            category.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f'🔄 Updated category: {category.name}')
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'ℹ️  Category already exists: {category.name}')
                            )

                # Verify categories were created
                total_categories = Category.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(f'\n📊 Summary:')
                )
                self.stdout.write(f'   • Created: {created_count} new categories')
                self.stdout.write(f'   • Updated: {updated_count} categories')
                self.stdout.write(f'   • Total in database: {total_categories} categories')
                
                if total_categories == 0:
                    self.stdout.write(
                        self.style.ERROR('⚠️  WARNING: No categories in database!')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Successfully populated announcement categories')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error populating categories: {str(e)}')
            )
            raise
