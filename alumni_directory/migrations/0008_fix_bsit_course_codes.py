from django.db import migrations


def fix_course_codes(apps, schema_editor):
    Alumni = apps.get_model('alumni_directory', 'Alumni')

    # Order matters: rename BSIT -> BSINT first, then BIT -> BSIT
    updated = Alumni.objects.filter(course='BSIT').update(course='BSINT')
    if updated:
        print(f"  Renamed {updated} record(s): 'BSIT' -> 'BSINT' (Information Technology)")

    updated = Alumni.objects.filter(course='BIT').update(course='BSIT')
    if updated:
        print(f"  Renamed {updated} record(s): 'BIT' -> 'BSIT' (Industrial Technology)")

    updated = Alumni.objects.filter(course='BSIT-ET').update(course='BSIT')
    if updated:
        print(f"  Renamed {updated} record(s): 'BSIT-ET' -> 'BSIT' (Industrial Technology - Electronics)")

    updated = Alumni.objects.filter(course='BSIT-INDTECH').update(course='BSIT')
    if updated:
        print(f"  Renamed {updated} record(s): 'BSIT-INDTECH' -> 'BSIT' (Industrial Technology)")


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('alumni_directory', '0007_normalize_course_values'),
    ]

    operations = [
        migrations.RunPython(fix_course_codes, reverse),
    ]
