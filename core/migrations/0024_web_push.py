from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('core', '0023_coordinator_campus'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='WebPushSubscription',fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
            ('endpoint', models.URLField(max_length=2048, unique=True)),
            ('p256dh', models.CharField(max_length=512)),
            ('auth', models.CharField(max_length=256)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='web_push_subscriptions', to=settings.AUTH_USER_MODEL)),
        ],options={'indexes':[models.Index(fields=['user'], name='webpush_user_idx')]}),
        migrations.CreateModel(name='WebPushDelivery',fields=[
            ('id', models.BigAutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
            ('status', models.CharField(max_length=12, default='pending', choices=[('pending','Pending'),('sent','Sent'),('failed','Failed')])),
            ('attempts', models.PositiveSmallIntegerField(default=0)),
            ('retry_after', models.DateTimeField(blank=True, null=True)),
            ('sent_at', models.DateTimeField(blank=True, null=True)),
            ('last_error', models.CharField(blank=True, max_length=160)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='web_push_deliveries', to='core.notification')),
            ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='core.webpushsubscription')),
        ],options={'indexes':[models.Index(fields=['status','retry_after'],name='webpush_due_idx')],
                  'constraints':[models.UniqueConstraint(fields=['notification','subscription'],name='webpush_notification_subscription_once')]}),
    ]
