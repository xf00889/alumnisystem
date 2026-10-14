from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_alter_education_program'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='birth_place',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='profile',
            name='civil_status',
            field=models.CharField(blank=True, choices=[('SINGLE', 'Single'), ('MARRIED', 'Married'), ('WIDOWED', 'Widowed'), ('SEPARATED', 'Separated'), ('OTHER', 'Other')], max_length=20),
        ),
        migrations.AddField(
            model_name='profile',
            name='education_level',
            field=models.CharField(blank=True, choices=[('HS', 'High School'), ('COLLEGE', 'College'), ('GRADUATE', 'Graduate School'), ('OTHER', 'Other')], max_length=20),
        ),
        migrations.AddField(
            model_name='profile',
            name='emergency_contact_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='profile',
            name='emergency_contact_number',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='profile',
            name='emergency_contact_relationship',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='employer_sector',
            field=models.CharField(blank=True, choices=[('PRIVATE', 'Private'), ('GOVERNMENT', 'Government'), ('NON_PROFIT', 'Non-profit'), ('SELF', 'Self-employed'), ('OTHER', 'Other')], max_length=20),
        ),
        migrations.AddField(
            model_name='profile',
            name='employment_address',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='profile',
            name='landline_number',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='profile',
            name='maiden_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='profile',
            name='middle_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='profile',
            name='workplace_reference_contact',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='profile',
            name='workplace_reference_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='profile',
            name='workplace_reference_position',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
