from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('alumni_directory', '0010_alter_alumni_campus_alter_alumni_college')]

    operations = [
        migrations.AddField('graduateregistry','middle_name', models.CharField(blank=True,max_length=150)),
        migrations.AddField('graduateregistry','suffix', models.CharField(blank=True,max_length=30)),
        migrations.AddField('graduateregistry','college', models.CharField(blank=True,max_length=10,choices=[
            ('CAS','College of Arts and Sciences'),('CBA','College of Business Administration'),
            ('CAFF','College of Agriculture, Forestry and Fisheries'),('CCJE','College of Criminal Justice Education'),
            ('CEA','College of Engineering'),('CIT','College of Industrial Technology'),('COL','College of Law'),
            ('CNPAHS','College of Nursing, Pharmacy and Allied Health Sciences'),('CTE','College of Education'),
            ('CTHM','College of Tourism and Hospitality Management'),
        ])),
        migrations.AddField('graduateregistry','major',models.CharField(blank=True,max_length=200)),
        migrations.AddField('graduateregistry','source_filename',models.CharField(blank=True,max_length=255)),
        migrations.AddField('graduateregistry','source_sheet',models.CharField(blank=True,max_length=100)),
        migrations.AddField('graduateregistry','source_row',models.PositiveIntegerField(blank=True,null=True)),
    ]
