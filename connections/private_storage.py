"""Message attachment storage outside publicly served MEDIA_ROOT.

The web server must never alias PRIVATE_MESSAGE_UPLOAD_ROOT as static/media.
"""
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property


@deconstructible
class PrivateMessageStorage(FileSystemStorage):
    @cached_property
    def base_location(self):
        return str(settings.PRIVATE_MESSAGE_UPLOAD_ROOT)

    def url(self, name):
        raise ValueError('Private message files have no public URL. Use the authorized download view.')


private_message_storage = PrivateMessageStorage()


def private_message_upload_path(instance, filename):
    # Never place user-controlled names or identifiers in the storage path.
    suffix = Path(filename).suffix.lower()
    return f'connections/messages/{uuid.uuid4().hex}{suffix}'
