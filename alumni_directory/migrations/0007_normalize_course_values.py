from django.db import migrations


def normalize_courses(apps, schema_editor):
    Alumni = apps.get_model('alumni_directory', 'Alumni')

    # Map full display names and variants to canonical course codes
    normalization_map = {
        # Elementary Education variants
        'Bachelor of Elementary Education': 'BEED',
        'BEED-GC': 'BEED',
        'BS in Elementary Education': 'BEED',
        # Secondary Education variants
        'Bachelor of Secondary Education': 'BSED',
        'BS in Secondary Education': 'BSED',
        # Other full-name variants found in the database
        'Bachelor of Science in Computer Science': 'BSCS',
        'Bachelor of Science in Information Technology': 'BSIT',
        'Bachelor of Science in Criminology': 'BSCRIM',
        'Bachelor of Science in Industrial Technology': 'BIT',
        'Bachelor of Science in Hospitality Management': 'BSHM',
        'Bachelor of Science in Business Administration': 'BSBA',
        'Bachelor of Science in Agriculture': 'BSA-AGRI',
        'Bachelor of Science in Forestry': 'BSF',
        'Bachelor of Science in Office Administration': 'BSOSM',
        'Bachelor of Science in Office Systems Management': 'BSOSM',
        'Bachelor of Agricultural Technology': 'BIT',
        'BS in Nursing': 'BSN',
    }

    for old_value, new_value in normalization_map.items():
        updated = Alumni.objects.filter(course=old_value).update(course=new_value)
        if updated:
            print(f"  Normalized {updated} record(s): '{old_value}' -> '{new_value}'")


def reverse_normalize(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('alumni_directory', '0006_set_default_campus'),
    ]

    operations = [
        migrations.RunPython(normalize_courses, reverse_normalize),
    ]
