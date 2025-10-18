from django.contrib import admin
from django.utils.html import format_html
from .models.contact import Address, ContactInfo
from .models.content import Post, Comment, Reaction
from .models.smtp_config import SMTPConfig

# Register existing models if they aren't already registered
try:
    admin.site.register(Address)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(ContactInfo)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(Post)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(Comment)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(Reaction)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(SMTPConfig)
except admin.sites.AlreadyRegistered:
    pass