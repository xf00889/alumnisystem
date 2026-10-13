import uuid
from pathlib import PurePosixPath

from django.db import migrations, models

import connections.private_storage


def populate_attachment_tokens(apps, schema_editor):
    Message = apps.get_model('connections', 'DirectMessage')
    for row in Message.objects.all().iterator(chunk_size=500):
        changes = {'attachment_token': uuid.uuid4()}
        if row.attachment:
            changes['attachment_display_name'] = PurePosixPath(row.attachment.name).name[:160]
        Message.objects.filter(pk=row.pk).update(**changes)


class Migration(migrations.Migration):
    dependencies = [('connections', '0003_directconversation_group_photo')]
    operations = [
        migrations.AddField(
            model_name='directmessage', name='attachment_token',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='directmessage', name='attachment_display_name',
            field=models.CharField(max_length=160, blank=True),
        ),
        migrations.RunPython(populate_attachment_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='directmessage', name='attachment_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='directmessage', name='attachment',
            field=models.FileField(
                blank=True, null=True,
                upload_to=connections.private_storage.private_message_upload_path,
                storage=connections.private_storage.PrivateMessageStorage(),
            ),
        ),
    ]
