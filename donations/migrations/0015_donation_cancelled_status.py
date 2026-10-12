from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):
    dependencies = [('donations', '0014_donation_payment_security')]

    operations = [
        migrations.AlterField(
            model_name='donation',
            name='status',
            field=models.CharField(
                _('Status'), max_length=20, default='pending_payment',
                choices=[
                    ('pending_payment', _('Pending Payment')),
                    ('pending_verification', _('Pending Verification')),
                    ('cancelled', _('Cancelled')),
                    ('completed', _('Completed')),
                    ('failed', _('Failed')),
                    ('refunded', _('Refunded')),
                    ('disputed', _('Disputed')),
                ],
            ),
        ),
    ]
