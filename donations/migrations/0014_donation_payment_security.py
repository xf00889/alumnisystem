from django.db import migrations, models
import donations.storage


class Migration(migrations.Migration):
    dependencies = [('donations', '0013_campaign_allow_donations_campaign_gcash_config')]
    operations = [
        migrations.AddField('donation', 'gcash_account_name', models.CharField(max_length=100, blank=True)),
        migrations.AddField('donation', 'gcash_account_number', models.CharField(max_length=15, blank=True)),
        migrations.AddField('donation', 'gcash_payment_instructions', models.TextField(blank=True)),
        migrations.AddField('donation', 'gcash_qr_snapshot', models.ImageField(upload_to='donation_gcash_qr/', blank=True, null=True)),
        migrations.AlterField('donation', 'payment_proof', models.ImageField(upload_to='payment_proofs/', storage=donations.storage.private_payment_storage, blank=True, null=True, verbose_name='Payment Proof')),
    ]
