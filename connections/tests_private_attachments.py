"""Integration tests requiring Django and the project test database."""
from core.testing_clients import CompletedPortalSetupMixin, HTTPSClient

import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from core.file_validators import validate_message_attachment
from .models import Connection, DirectConversation, DirectMessage
from .private_storage import private_message_storage


class AttachmentValidationTests(TestCase):
    def test_masquerading_jpg_is_rejected(self):
        file = SimpleUploadedFile('resume.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
        with self.assertRaises(ValidationError):
            validate_message_attachment(file)

    def test_arbitrary_zip_is_rejected(self):
        file = SimpleUploadedFile('payload.zip', b'PK\x03\x04junk')
        with self.assertRaises(ValidationError):
            validate_message_attachment(file)

    def test_path_name_is_sanitized(self):
        from core.file_validators import sanitize_filename
        self.assertEqual(sanitize_filename(r'folder\private\resume.pdf'), 'resume.pdf')

    def test_pdf_must_have_pdf_signature(self):
        file = SimpleUploadedFile('resume.pdf', b'not a pdf', content_type='application/pdf')
        with self.assertRaises(ValidationError):
            validate_message_attachment(file)


class PrivateAttachmentAccessTests(CompletedPortalSetupMixin, TestCase):
    client_class = HTTPSClient
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = override_settings(PRIVATE_MESSAGE_UPLOAD_ROOT=self.directory.name, RATELIMIT_ENABLE=False)
        self.override.enable()
        self.addCleanup(self.override.disable)
        private_message_storage.__dict__.pop('base_location', None)
        private_message_storage.__dict__.pop('location', None)
        self.User = get_user_model()
        self.sender = self.User.objects.create_user(username='msg_sender', password='testpass')
        self.member = self.User.objects.create_user(username='msg_member', password='testpass')
        self.outsider = self.User.objects.create_user(username='msg_outsider', password='testpass')
        self.conversation = DirectConversation.objects.create(conversation_type='direct')
        self.conversation.participants.add(self.sender, self.member)
        self.message = DirectMessage.objects.create(
            conversation=self.conversation, sender=self.sender, content='Resume',
            attachment_display_name='resume.pdf',
        )
        self.message.attachment.save('resume.pdf', ContentFile(b'%PDF-1.4\n%%EOF'), save=True)
        self.url = reverse('connections:message_attachment', kwargs={'token': self.message.attachment_token})
        self.addCleanup(lambda: private_message_storage.__dict__.pop('base_location', None))
        self.addCleanup(lambda: private_message_storage.__dict__.pop('location', None))

    def test_unauthenticated_cannot_download(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_unrelated_user_cannot_download(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_group_or_direct_member_can_download(self):
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4\n%%EOF')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertEqual(response['Cache-Control'], 'private, no-store, max-age=0')
        self.assertNotIn('connections/messages/', self.url)

    def test_message_removed_from_conversation_revokes_access(self):
        self.conversation.participants.remove(self.member)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_blocked_direct_contact_cannot_download_earlier_files(self):
        Connection.objects.create(requester=self.sender, receiver=self.member, status='BLOCKED')
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_legacy_public_media_path_is_blocked(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get('/media/connections/messages/resume.pdf').status_code, 404)
