from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test users for debugging'

    def handle(self, *args, **options):
        # Create test user 1
        if not User.objects.filter(username='testuser1').exists():
            user1 = User.objects.create_user(
                username='testuser1',
                email='test1@example.com',
                password='password123',
                first_name='Test',
                last_name='User1'
            )
            self.stdout.write(self.style.SUCCESS(f'Created user: {user1.username}'))
        else:
            self.stdout.write(self.style.WARNING('User testuser1 already exists'))
            
        # Create test user 2
        if not User.objects.filter(username='testuser2').exists():
            user2 = User.objects.create_user(
                username='testuser2',
                email='test2@example.com',
                password='password123',
                first_name='Test',
                last_name='User2'
            )
            self.stdout.write(self.style.SUCCESS(f'Created user: {user2.username}'))
        else:
            self.stdout.write(self.style.WARNING('User testuser2 already exists'))
            
        # Create test user 3
        if not User.objects.filter(username='darelltest').exists():
            user3 = User.objects.create_user(
                username='darelltest',
                email='darell@example.com',
                password='password123',
                first_name='Darell',
                last_name='Test'
            )
            self.stdout.write(self.style.SUCCESS(f'Created user: {user3.username}'))
        else:
            self.stdout.write(self.style.WARNING('User darelltest already exists'))
            
        self.stdout.write(self.style.SUCCESS('Test users created successfully')) 