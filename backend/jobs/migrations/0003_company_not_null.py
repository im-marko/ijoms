import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_backfill_demo_company'),
        ('jobs', '0002_remove_job_jobs_job_status_007c84_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='jobs', to='accounts.company',
            ),
        ),
        migrations.AlterField(
            model_name='jobcategory',
            name='company',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='job_categories', to='accounts.company',
            ),
        ),
    ]
