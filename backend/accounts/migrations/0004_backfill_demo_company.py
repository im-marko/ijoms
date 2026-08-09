import re
import secrets

from django.db import migrations

INVITE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def _invite_code(name):
    prefix = (re.sub(r'[^A-Z0-9]', '', name.upper())[:4] + 'XXXX')[:4]
    return prefix + '-' + ''.join(secrets.choice(INVITE_ALPHABET) for _ in range(4))


def backfill(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Company = apps.get_model('accounts', 'Company')
    Job = apps.get_model('jobs', 'Job')
    JobCategory = apps.get_model('jobs', 'JobCategory')
    Notice = apps.get_model('noticeboard', 'Notice')
    AuditLog = apps.get_model('auditlog', 'AuditLog')

    has_data = any(
        model.objects.exists()
        for model in (User, Job, JobCategory, Notice, AuditLog)
    )
    if not has_data:
        return  # fresh install — companies arrive via signup/seed

    demo = Company.objects.filter(slug='demo').first()
    if demo is None:
        demo = Company.objects.create(
            name='Demo Company', slug='demo', invite_code=_invite_code('Demo Company'),
        )

    User.objects.filter(company__isnull=True, is_superuser=False).update(company=demo)
    for model in (Job, JobCategory, Notice, AuditLog):
        model.objects.filter(company__isnull=True).update(company=demo)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_company_alter_user_managers_user_company'),
        ('jobs', '0002_remove_job_jobs_job_status_007c84_idx_and_more'),
        ('noticeboard', '0002_notice_company'),
        ('auditlog', '0002_auditlog_company_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
