from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0025_daily_visitor_analytics')]
    operations = [migrations.CreateModel(
        name='DailyBrowserVisit',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('day', models.DateField(db_index=True)),
            ('visitor_key', models.CharField(db_index=True, max_length=64)),
            ('first_seen', models.DateTimeField()),
            ('last_seen', models.DateTimeField(db_index=True)),
            ('sampled_page_loads', models.PositiveIntegerField(default=1)),
        ],
        options={'ordering': ('-last_seen',)},
    ), migrations.AddConstraint(
        model_name='dailybrowservisit',
        constraint=models.UniqueConstraint(fields=('day', 'visitor_key'), name='unique_browser_visit_per_day'),
    )]
