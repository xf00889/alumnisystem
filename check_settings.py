import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "norsu_alumni.settings")
django.setup()

# Import settings
from django.conf import settings

print("Current ALLOWED_HOSTS setting:", settings.ALLOWED_HOSTS)
print("Type of ALLOWED_HOSTS:", type(settings.ALLOWED_HOSTS))
print("'192.168.1.6' in ALLOWED_HOSTS:", '192.168.1.6' in settings.ALLOWED_HOSTS) 