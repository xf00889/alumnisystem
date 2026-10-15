"""Runtime tests for safe retention of failed event/campaign form images."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from core import pending_form_images as pending


class PendingFormImagesTests(SimpleTestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        storage = FileSystemStorage(location=self.tmp.name)
        patcher = patch.object(pending, 'default_storage', storage)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.owner = SimpleNamespace(user=SimpleNamespace(pk=21, is_authenticated=True))
        self.other = SimpleNamespace(user=SimpleNamespace(pk=22, is_authenticated=True))
        self.scope = 'events.event.image'

    @staticmethod
    def image():
        buffer = BytesIO()
        Image.new('RGB', (18, 18), '#193b60').save(buffer, format='PNG')
        return SimpleUploadedFile('sample.png', buffer.getvalue(), content_type='image/png')

    def test_upload_can_be_recovered_only_by_owner_and_for_same_form(self):
        token, name = pending.hold(self.owner, self.image(), self.scope)
        self.assertTrue(token)
        self.assertEqual(name, 'sample.png')
        self.assertIsNotNone(pending.recover(self.owner, token, self.scope, 'anything.jpg'))
        self.assertIsNone(pending.recover(self.other, token, self.scope, 'anything.jpg'))
        self.assertIsNone(pending.recover(self.owner, token, 'donations.campaign.featured_image', 'anything.jpg'))
        pending.clear(self.owner, token, self.scope)
        self.assertIsNone(pending.recover(self.owner, token, self.scope, 'anything.jpg'))

    def test_invalid_image_is_not_kept(self):
        file = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        token, _ = pending.hold(self.owner, file, self.scope)
        self.assertEqual(token, '')

    def test_oversize_file_is_not_kept(self):
        file = SimpleUploadedFile('huge.png', b'a' * (pending.MAX_SIZE + 1), content_type='image/png')
        token, _ = pending.hold(self.owner, file, self.scope)
        self.assertEqual(token, '')
