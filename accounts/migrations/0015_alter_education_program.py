from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_alter_experience_location"),
    ]

    operations = [
        migrations.AlterField(
            model_name="education",
            name="program",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
