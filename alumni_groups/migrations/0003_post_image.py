# Optional group feed photos. Existing posts remain unchanged.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('alumni_groups', '0002_alumnigroup_profile_photo')]
    operations = [migrations.AddField(
        model_name='post', name='image',
        field=models.ImageField(blank=True, null=True, upload_to='group_post_images/%Y/%m/'),
    )]
