"""Cross-tenant isolation suite: two companies must never see each other's
users, jobs, categories, notices, audit logs, analytics, or notifications."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from auditlog.models import AuditLog
from jobs.models import Job, JobCategory
from jobs.services import escalate_overdue_jobs
from noticeboard.models import Notice
from notifications.models import Notification
from .test_utils import TEST_REST_FRAMEWORK, make_company, make_user

User = get_user_model()


def make_job(company, category, created_by, title='Job', **overrides):
    defaults = dict(
        company=company, title=title, description='d', category=category,
        created_by=created_by, customer_name='Customer',
    )
    defaults.update(overrides)
    return Job.objects.create(**defaults)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class TenancyIsolationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company_a = make_company('Alpha Ltd')
        cls.company_b = make_company('Bravo Ltd')

        cls.a_admin = make_user('admin', 'a-admin@example.com', 'aadmin', company=cls.company_a)
        cls.a_supervisor = make_user('supervisor', 'a-sup@example.com', 'asup', company=cls.company_a)
        cls.a_tech = make_user('technician', 'a-tech@example.com', 'atech', company=cls.company_a)
        cls.b_admin = make_user('admin', 'b-admin@example.com', 'badmin', company=cls.company_b)
        cls.b_supervisor = make_user('supervisor', 'b-sup@example.com', 'bsup', company=cls.company_b)
        cls.b_tech = make_user('technician', 'b-tech@example.com', 'btech', company=cls.company_b)

        # Same category name may exist in both companies
        cls.a_category = JobCategory.objects.create(
            company=cls.company_a, name='Hardware Repair', sla_hours=24,
        )
        cls.b_category = JobCategory.objects.create(
            company=cls.company_b, name='Hardware Repair', sla_hours=24,
        )

        cls.a_job = make_job(cls.company_a, cls.a_category, cls.a_supervisor, title='Alpha job')
        cls.b_job = make_job(cls.company_b, cls.b_category, cls.b_supervisor, title='Bravo job')

        cls.a_notice = Notice.objects.create(
            company=cls.company_a, title='Alpha notice', content='a',
            created_by=cls.a_supervisor,
        )
        cls.b_notice = Notice.objects.create(
            company=cls.company_b, title='Bravo notice', content='b',
            created_by=cls.b_supervisor,
        )

        AuditLog.objects.create(
            company=cls.company_a, user=cls.a_admin, action='create',
            entity_type='Job', entity_id=str(cls.a_job.pk),
        )
        AuditLog.objects.create(
            company=cls.company_b, user=cls.b_admin, action='create',
            entity_type='Job', entity_id=str(cls.b_job.pk),
        )

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def test_user_list_scoped_to_own_company(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 200)
        emails = {row['email'] for row in response.data['results']}
        self.assertEqual(emails, {
            'a-admin@example.com', 'a-sup@example.com', 'a-tech@example.com',
        })

    def test_user_detail_cross_tenant_404(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get(f'/api/auth/users/{self.b_tech.pk}/')
        self.assertEqual(response.status_code, 404)
        response = self.client.patch(
            f'/api/auth/users/{self.b_tech.pk}/', {'first_name': 'Hacked'}
        )
        self.assertEqual(response.status_code, 404)
        self.b_tech.refresh_from_db()
        self.assertNotEqual(self.b_tech.first_name, 'Hacked')

    def test_set_password_cross_tenant_404(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.post(
            f'/api/auth/users/{self.b_tech.pk}/set-password/',
            {'new_password': 'Another!Secret512'},
        )
        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------
    def test_job_list_excludes_other_company(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        ids = {row['id'] for row in response.data['results']}
        self.assertIn(self.a_job.pk, ids)
        self.assertNotIn(self.b_job.pk, ids)

    def test_job_detail_cross_tenant_404(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get(f'/api/jobs/{self.b_job.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_job_status_update_cross_tenant_404(self):
        self.client.force_authenticate(self.a_supervisor)
        response = self.client.post(
            f'/api/jobs/{self.b_job.pk}/status/', {'status': 'closed'}
        )
        self.assertEqual(response.status_code, 404)
        self.b_job.refresh_from_db()
        self.assertEqual(self.b_job.status, 'open')

    def test_job_assign_cross_tenant_404(self):
        self.client.force_authenticate(self.a_supervisor)
        response = self.client.post(
            f'/api/jobs/{self.b_job.pk}/assign/', {'assigned_to': self.a_tech.pk}
        )
        self.assertEqual(response.status_code, 404)

    def test_assign_own_job_to_other_companys_technician_rejected(self):
        self.client.force_authenticate(self.a_supervisor)
        response = self.client.post(
            f'/api/jobs/{self.a_job.pk}/assign/', {'assigned_to': self.b_tech.pk}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('assigned_to', response.data)
        self.a_job.refresh_from_db()
        self.assertIsNone(self.a_job.assigned_to)

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------
    def test_category_name_can_repeat_across_companies(self):
        self.assertEqual(
            JobCategory.objects.filter(name='Hardware Repair').count(), 2
        )
        self.client.force_authenticate(self.a_admin)
        response = self.client.get('/api/jobs/categories/')
        self.assertEqual(response.status_code, 200)
        ids = {row['id'] for row in response.data['results']}
        self.assertEqual(ids, {self.a_category.pk})

    def test_duplicate_category_name_within_company_rejected(self):
        """A duplicate name within one company is a 400, not a second row."""
        self.client.force_authenticate(self.a_supervisor)
        response = self.client.post('/api/jobs/categories/', {
            'name': 'Hardware Repair', 'sla_hours': 8,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            JobCategory.objects.filter(
                company=self.company_a, name='Hardware Repair'
            ).count(),
            1,
        )

    # ------------------------------------------------------------------
    # Notices
    # ------------------------------------------------------------------
    def test_notice_list_excludes_other_company(self):
        self.client.force_authenticate(self.a_tech)
        response = self.client.get('/api/noticeboard/')
        self.assertEqual(response.status_code, 200)
        titles = {row['title'] for row in response.data['results']}
        self.assertIn('Alpha notice', titles)
        self.assertNotIn('Bravo notice', titles)

    def test_notice_detail_and_delete_cross_tenant_404(self):
        self.client.force_authenticate(self.a_supervisor)
        response = self.client.get(f'/api/noticeboard/{self.b_notice.pk}/')
        self.assertEqual(response.status_code, 404)
        response = self.client.delete(f'/api/noticeboard/{self.b_notice.pk}/')
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Notice.objects.filter(pk=self.b_notice.pk).exists())

    # ------------------------------------------------------------------
    # Audit logs
    # ------------------------------------------------------------------
    def test_audit_log_list_scoped(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get('/api/audit-logs/')
        self.assertEqual(response.status_code, 200)
        entity_ids = {row['entity_id'] for row in response.data['results']}
        self.assertIn(str(self.a_job.pk), entity_ids)
        self.assertNotIn(str(self.b_job.pk), entity_ids)

    def test_audit_log_filter_by_foreign_user_returns_nothing(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get(f'/api/audit-logs/?user_id={self.b_admin.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    def test_summary_counts_only_own_jobs(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get('/api/analytics/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['job_summary']['total'],
            Job.objects.filter(company=self.company_a).count(),
        )

    def test_technician_performance_only_own_technicians(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get('/api/analytics/technician-performance/')
        self.assertEqual(response.status_code, 200)
        ids = {row['technician_id'] for row in response.data}
        self.assertEqual(ids, {self.a_tech.pk})

    def test_export_csv_only_own_jobs(self):
        self.client.force_authenticate(self.a_admin)
        response = self.client.get('/api/analytics/export/jobs/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn(self.a_job.reference_number, content)
        self.assertNotIn(self.b_job.reference_number, content)

    # ------------------------------------------------------------------
    # Escalation
    # ------------------------------------------------------------------
    def _make_overdue_jobs(self):
        past = timezone.now() - timedelta(hours=3)
        a_overdue = make_job(
            self.company_a, self.a_category, self.a_supervisor,
            title='Alpha overdue', assigned_to=self.a_tech, status='assigned',
        )
        b_overdue = make_job(
            self.company_b, self.b_category, self.b_supervisor,
            title='Bravo overdue', assigned_to=self.b_tech, status='assigned',
        )
        Job.objects.filter(pk__in=[a_overdue.pk, b_overdue.pk]).update(sla_deadline=past)
        a_overdue.refresh_from_db()
        b_overdue.refresh_from_db()
        return a_overdue, b_overdue

    def test_escalation_notifies_within_each_company_only(self):
        a_overdue, b_overdue = self._make_overdue_jobs()
        escalated = escalate_overdue_jobs()
        self.assertEqual(
            {job.pk for job in escalated}, {a_overdue.pk, b_overdue.pk}
        )
        a_overdue.refresh_from_db()
        b_overdue.refresh_from_db()
        self.assertEqual(a_overdue.status, 'escalated')
        self.assertEqual(b_overdue.status, 'escalated')

        a_recipients = Notification.objects.filter(
            related_job=a_overdue
        ).values_list('recipient__company_id', flat=True)
        self.assertTrue(len(a_recipients) > 0)
        self.assertEqual(set(a_recipients), {self.company_a.pk})

        b_recipients = Notification.objects.filter(
            related_job=b_overdue
        ).values_list('recipient__company_id', flat=True)
        self.assertTrue(len(b_recipients) > 0)
        self.assertEqual(set(b_recipients), {self.company_b.pk})

    @override_settings(CRON_SECRET='test-cron-secret')
    def test_run_sla_check_reports_counts_without_references(self):
        a_overdue, b_overdue = self._make_overdue_jobs()
        response = self.client.post(
            '/api/jobs/run-sla-check/', HTTP_X_CRON_SECRET='test-cron-secret',
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(set(response.data.keys()), {'escalated', 'by_company'})
        self.assertEqual(response.data['escalated'], 2)
        self.assertEqual(response.data['by_company'], {
            self.company_a.slug: 1, self.company_b.slug: 1,
        })
        body = response.content.decode()
        self.assertNotIn(a_overdue.reference_number, body)
        self.assertNotIn(b_overdue.reference_number, body)

    # ------------------------------------------------------------------
    # Company-less users
    # ------------------------------------------------------------------
    def test_companyless_user_gets_empty_lists(self):
        orphan = make_user('admin', 'orphan@example.com', 'orphan', company=None)
        self.client.force_authenticate(orphan)

        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        response = self.client.get('/api/noticeboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
