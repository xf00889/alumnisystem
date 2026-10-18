from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0024_web_push')]

    operations = [
        migrations.CreateModel(
            name='DailyVisitor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.DateField(db_index=True)),
                ('ip_address', models.GenericIPAddressField(protocol='both', unpack_ipv4=True)),
                ('first_seen', models.DateTimeField()),
                ('last_seen', models.DateTimeField(db_index=True)),
                ('sampled_page_loads', models.PositiveIntegerField(default=1)),
            ],
            options={'ordering': ('-last_seen',)},
        ),
        migrations.AddConstraint(model_name='dailyvisitor', constraint=models.UniqueConstraint(fields=('day', 'ip_address'), name='unique_site_visitor_per_day')),
        migrations.AddIndex(model_name='dailyvisitor', index=models.Index(fields=['day','last_seen'], name='site_visitor_day_seen_idx')),
    ]
