from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from jobs.models import Job, JobCategory

User = get_user_model()

PASSWORD = 'Compl3x!Passw0rd'


def make_user(role, email, username):
    return User.objects.create_user(
        username=username, email=email, password=PASSWORD, role=role,
        first_name=username.capitalize(), last_name='User',
    )


class AnalyticsAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.om = make_user('operations_manager', 'om@example.com', 'om')
        cls.supervisor = make_user('supervisor', 'sup@example.com', 'sup')
        cls.technician = make_user('technician', 'tech@example.com', 'tech')
        cls.technician2 = make_user('technician', 'tech2@example.com', 'tech2')
        cls.category = JobCategory.objects.create(name='Electrical', sla_hours=24)

        def job(title, **kw):
            defaults = dict(
                title=title, description='d', category=cls.category,
                created_by=cls.om, customer_name='Acme',
            )
            defaults.update(kw)
            return Job.objects.create(**defaults)

        cls.job1 = job('Tech1 job A', assigned_to=cls.technician, status='assigned')
        cls.job2 = job('Tech1 job B', assigned_to=cls.technician, status='in_progress')
        cls.job3 = job('Tech2 job', assigned_to=cls.technician2, status='assigned')
        cls.job4 = job('Unassigned job')

    def test_summary_scoped_to_technician_own_jobs(self):
        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/analytics/summary/')
        self.assertEqual(response.status_code, 200)
        summary = response.data['job_summary']
        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['by_status'].get('assigned'), 1)
        self.assertEqual(summary['by_status'].get('in_progress'), 1)

    def test_summary_global_for_operations_manager(self):
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/analytics/summary/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['job_summary']['total'], 4)

    def test_job_volume_bad_days_param_falls_back(self):
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/analytics/job-volume/?days=abc')
        self.assertEqual(response.status_code, 200)

    def test_job_volume_bogus_period_falls_back(self):
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/analytics/job-volume/?period=bogus')
        self.assertEqual(response.status_code, 200)

    def test_technician_performance_forbidden_for_supervisor(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get('/api/analytics/technician-performance/')
        self.assertEqual(response.status_code, 403)

    def test_technician_performance_allowed_for_operations_manager(self):
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/analytics/technician-performance/')
        self.assertEqual(response.status_code, 200)
        names = {row['technician_id'] for row in response.data}
        self.assertIn(self.technician.pk, names)

    def test_export_jobs_csv(self):
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/analytics/export/jobs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode()
        self.assertIn('Reference', content)
        self.assertIn(self.job1.reference_number, content)
