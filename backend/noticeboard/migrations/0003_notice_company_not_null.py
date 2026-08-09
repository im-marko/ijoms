import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_backfill_demo_company'),
        ('noticeboard', '0002_notice_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notice',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notices', to='accounts.company',
            ),
        ),
    ]
