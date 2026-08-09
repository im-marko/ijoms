from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from accounts.test_utils import make_company, make_user
from auditlog.models import AuditLog
from .models import Notice

User = get_user_model()


class NoticeboardAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company('Notice TestCo')
        cls.supervisor = make_user('supervisor', 'sup@example.com', 'sup', company=cls.company)
        cls.technician = make_user('technician', 'tech@example.com', 'tech', company=cls.company)
        cls.finance = make_user('finance_officer', 'fin@example.com', 'fin', company=cls.company)

    def test_create_notice_as_supervisor_is_audited(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post('/api/noticeboard/create/', {
            'title': 'Maintenance window',
            'content': 'System down Saturday night.',
            'priority': 'high',
        })
        self.assertEqual(response.status_code, 201, response.data)
        notice = Notice.objects.get(title='Maintenance window')
        self.assertEqual(notice.created_by, self.supervisor)
        # Regression: notice creation used to leave no audit trail
        self.assertTrue(
            AuditLog.objects.filter(
                action='create', entity_type='Notice', entity_id=str(notice.pk),
                user=self.supervisor,
            ).exists()
        )

    def test_create_notice_as_technician_forbidden(self):
        self.client.force_authenticate(self.technician)
        response = self.client.post('/api/noticeboard/create/', {
            'title': 'Nope', 'content': 'Nope',
        })
        self.assertEqual(response.status_code, 403)

    def test_invalid_target_role_rejected(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post('/api/noticeboard/create/', {
            'title': 'Bad roles',
            'content': 'x',
            'target_roles': ['bogus_role'],
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('target_roles', response.data)

    def test_role_targeting_visibility(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post('/api/noticeboard/create/', {
            'title': 'Technicians only',
            'content': 'Tool inspection due.',
            'target_roles': ['technician'],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)

        # Visible to technician
        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/noticeboard/')
        self.assertEqual(response.status_code, 200)
        titles = [n['title'] for n in response.data['results']]
        self.assertIn('Technicians only', titles)

        # Hidden from finance officer
        self.client.force_authenticate(self.finance)
        response = self.client.get('/api/noticeboard/')
        self.assertEqual(response.status_code, 200)
        titles = [n['title'] for n in response.data['results']]
        self.assertNotIn('Technicians only', titles)

    def test_empty_target_roles_visible_to_all(self):
        Notice.objects.create(
            company=self.company, title='Everyone', content='All-hands notice.',
            created_by=self.supervisor, target_roles=[],
        )
        for user in (self.technician, self.finance, self.supervisor):
            self.client.force_authenticate(user)
            response = self.client.get('/api/noticeboard/')
            self.assertEqual(response.status_code, 200)
            titles = [n['title'] for n in response.data['results']]
            self.assertIn('Everyone', titles, f'not visible to {user.email}')
