from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('cms', '0019_legalpage')]
    operations = [migrations.AlterField(
        model_name='legalpage', name='page_type',
        field=models.CharField(choices=[
            ('terms', 'Terms of Use'), ('privacy', 'Privacy Notice'),
            ('cookie-policy', 'Cookie Policy'),
            ('community-guidelines', 'Community Guidelines'),
            ('data-privacy-request', 'Data Privacy Request'),
        ], max_length=40, unique=True),
    )]
