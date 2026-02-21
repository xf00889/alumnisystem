# Generated migration to update VMGO acronym format

from django.db import migrations


def update_vmgo_format(apps, schema_editor):
    """Update VMGO goals and values to use acronym format"""
    NORSUVMGOHistory = apps.get_model('cms', 'NORSUVMGOHistory')
    
    try:
        vmgo = NORSUVMGOHistory.objects.first()
        if vmgo:
            # Update Goals with ASPIRE acronym format
            vmgo.goals = """A
Achieve global recognition by program excellence

S
Strengthen research through impactful innovation

P
Promote enhanced community extension services

I
Integrate partnerships and international relations

R
Revitalize infrastructure with operational systems

E
Enrich student life and leadership opportunities"""
            
            # Update Core Values with SHINE acronym format
            vmgo.core_values = """S
Spirituality

H
Honesty

I
Innovation

N
Nurturance

E
Excellence"""
            
            vmgo.save()
            print("Successfully updated VMGO acronym format")
    except Exception as e:
        print(f"Error updating VMGO format: {e}")


def reverse_vmgo_format(apps, schema_editor):
    """Reverse the VMGO format update"""
    NORSUVMGOHistory = apps.get_model('cms', 'NORSUVMGOHistory')
    
    try:
        vmgo = NORSUVMGOHistory.objects.first()
        if vmgo:
            # Restore original format
            vmgo.goals = """ASPIRE:
• Achieve global recognition by program excellence
• Strengthen research through impactful innovation
• Promote enhanced community extension services
• Integrate partnerships and international relations
• Revitalize infrastructure with operational systems
• Enrich student life and leadership opportunities"""
            
            vmgo.core_values = """SHINE:
• Spirituality
• Honesty
• Innovation
• Nurturance
• Excellence"""
            
            vmgo.save()
    except Exception as e:
        print(f"Error reversing VMGO format: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0015_populate_vmgo_default_content'),
    ]

    operations = [
        migrations.RunPython(update_vmgo_format, reverse_vmgo_format),
    ]
