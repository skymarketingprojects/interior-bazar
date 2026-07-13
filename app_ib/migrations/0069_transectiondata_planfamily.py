# Generated for TASK 5 — real per-family revenue analytics.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_ib', '0068_leadquery_timeline'),
    ]

    operations = [
        migrations.AddField(
            model_name='transectiondata',
            name='planFamily',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
