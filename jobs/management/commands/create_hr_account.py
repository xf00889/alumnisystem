"""Create one dedicated HR account, without granting Django staff/superuser rights.

Usage: python manage.py create_hr_account --username example --email example@university.edu
The password is entered via an interactive terminal, never a shell argument.
"""
from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Provision a dedicated, limited HR workspace account (interactive password).'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)

    def handle(self, *args, **options):
        username = options['username'].strip()
        email = options['email'].strip().lower()
        User = get_user_model()
        if not username or not email or '@' not in email:
            raise CommandError('A username and valid email address are required.')
        if User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=email).exists():
            raise CommandError('An account with this username or email already exists; use role management instead.')
        first = getpass('HR account password: ')
        second = getpass('Confirm password: ')
        if first != second:
            raise CommandError('Passwords do not match.')
        tentative = User(username=username, email=email)
        try:
            validate_password(first, user=tentative)
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=first, is_staff=False, is_superuser=False)
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.is_hr = True
            profile.is_alumni_coordinator = False
            profile.save(update_fields=['is_hr', 'is_alumni_coordinator'])
        self.stdout.write(self.style.SUCCESS('Dedicated HR account created. Assign no staff or superuser permissions.'))
