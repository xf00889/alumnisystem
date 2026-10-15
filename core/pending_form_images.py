"""Short-lived, owner-bound previews for form uploads after validation errors.

Image files are verified, limited to 5 MiB and stored under an unpredictable
media path. Never trust posted file paths: only signed one-hour tokens are used.
This module never changes the saved model until the form validates.
"""
import io
import uuid

from django.core import signing
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse
from django.views.decorators.cache import never_cache
from PIL import Image, UnidentifiedImageError

MAX_SIZE = 5 * 1024 * 1024
SALT = 'norsu.form.image.v1'
TYPES = {'JPEG': ('image/jpeg', 'jpg'), 'PNG': ('image/png', 'png'), 'WEBP': ('image/webp', 'webp')}


def _data(request, token, scope):
    try:
        data = signing.loads(token, salt=SALT, max_age=3600)
    except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return None
    if (not request.user.is_authenticated or data.get('uid') != request.user.pk or
            data.get('scope') != scope or
            not str(data.get('path', '')).startswith('pending-form-images/')):
        return None
    return data


def checked_image_bytes(upload):
    if not upload or upload.size > MAX_SIZE or upload.size == 0:
        raise ValueError('Choose an image up to 5 MB.')
    upload.seek(0)
    payload = upload.read(MAX_SIZE + 1)
    upload.seek(0)
    if not payload or len(payload) > MAX_SIZE:
        raise ValueError('Choose an image up to 5 MB.')
    try:
        with Image.open(io.BytesIO(payload)) as img:
            mime, ext = TYPES[img.format]
            img.verify()
    except (KeyError, OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        raise ValueError('Only valid JPG, PNG and WebP images are supported.')
    return payload, mime, ext


def hold(request, uploaded, scope, prior=''):
    if uploaded:
        try:
            payload, mime, ext = checked_image_bytes(uploaded)
        except ValueError:
            return '', ''
        clear(request, prior, scope)
        path = default_storage.save(
            f'pending-form-images/{uuid.uuid4().hex}.{ext}', ContentFile(payload))
        token = signing.dumps({'uid': request.user.pk, 'scope': scope,
                               'path': path, 'mime': mime}, salt=SALT)
        return token, uploaded.name
    if _data(request, prior, scope):
        return prior, 'Previously selected image'
    return '', ''


def recover(request, token, scope, name):
    data = _data(request, token, scope)
    if not data or not default_storage.exists(data['path']):
        return None
    with default_storage.open(data['path'], 'rb') as stored:
        content = stored.read(MAX_SIZE + 1)
    if len(content) > MAX_SIZE:
        return None
    # Revalidate stored bytes; never trust an altered file in media storage.
    extension = data['path'].rsplit('.', 1)[-1]
    candidate = SimpleUploadedFile(f'restored-image.{extension}', content, content_type=data['mime'])
    try:
        checked_image_bytes(candidate)
    except ValueError:
        return None
    candidate.seek(0)
    return candidate


def clear(request, token, scope):
    data = _data(request, token, scope)
    if data:
        default_storage.delete(data['path'])


@never_cache
def preview(request, token, scope):
    data = _data(request, token, scope)
    if not data or not default_storage.exists(data['path']):
        raise Http404
    with default_storage.open(data['path'], 'rb') as stored:
        payload = stored.read(MAX_SIZE + 1)
    if len(payload) > MAX_SIZE:
        raise Http404
    response = HttpResponse(payload, content_type=data['mime'])
    response['Cache-Control'] = 'private, no-store, max-age=0'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
