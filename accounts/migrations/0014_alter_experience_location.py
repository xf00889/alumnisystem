from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_auto_verify_documents"),
    ]

    operations = [
        migrations.AlterField(
            model_name="experience",
            name="location",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
