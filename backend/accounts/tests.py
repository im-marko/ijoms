from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from auditlog.models import AuditLog
from .test_utils import PASSWORD, TEST_REST_FRAMEWORK, make_company, make_user

User = get_user_model()


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class AccountsAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company('Acme Services')
        cls.md = make_user('admin', 'md@example.com', 'md', company=cls.company)
        cls.om = make_user('operations_manager', 'om@example.com', 'om', company=cls.company)
        cls.supervisor = make_user('supervisor', 'sup@example.com', 'sup', company=cls.company)
        cls.technician = make_user('technician', 'tech@example.com', 'tech', company=cls.company)
        cls.finance = make_user('finance_officer', 'fin@example.com', 'fin', company=cls.company)

    # ------------------------------------------------------------------
    # Self-service profile (/me/)
    # ------------------------------------------------------------------
    def test_me_cannot_change_role_but_profile_fields_updatable(self):
        self.client.force_authenticate(self.technician)
        response = self.client.patch('/api/auth/me/', {
            'role': 'admin',
            'first_name': 'Updated',
            'phone': '0771234567',
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.technician.refresh_from_db()
        self.assertEqual(self.technician.role, 'technician')
        self.assertEqual(self.technician.first_name, 'Updated')
        self.assertEqual(self.technician.phone, '0771234567')

    def test_me_includes_company_and_password_flags(self):
        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['company'], self.company.pk)
        self.assertEqual(response.data['company_name'], self.company.name)
        self.assertTrue(response.data['has_usable_password'])

    # ------------------------------------------------------------------
    # Admin user management
    # ------------------------------------------------------------------
    def test_md_can_create_user_with_chosen_role(self):
        self.client.force_authenticate(self.md)
        response = self.client.post('/api/auth/users/', {
            'email': 'newsup@example.com',
            'username': 'newsup',
            'first_name': 'Nadia',
            'last_name': 'Super',
            'role': 'supervisor',
            'password': PASSWORD,
        })
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email='newsup@example.com')
        self.assertEqual(user.role, 'supervisor')
        self.assertEqual(user.company, self.company)
        self.assertTrue(user.check_password(PASSWORD))

    def test_non_md_cannot_create_user(self):
        for actor in (self.om, self.supervisor, self.technician, self.finance):
            self.client.force_authenticate(actor)
            response = self.client.post('/api/auth/users/', {
                'email': f'blocked-{actor.pk}@example.com',
                'username': f'blocked{actor.pk}',
                'first_name': 'Blocked',
                'last_name': 'User',
                'role': 'technician',
                'password': PASSWORD,
            })
            self.assertEqual(response.status_code, 403)

    def test_md_cannot_change_own_role(self):
        self.client.force_authenticate(self.md)
        response = self.client.patch(
            f'/api/auth/users/{self.md.pk}/', {'role': 'technician'}
        )
        self.assertEqual(response.status_code, 400)
        self.md.refresh_from_db()
        self.assertEqual(self.md.role, 'admin')

    def test_md_cannot_deactivate_self(self):
        self.client.force_authenticate(self.md)
        response = self.client.patch(
            f'/api/auth/users/{self.md.pk}/', {'is_active': False}
        )
        self.assertEqual(response.status_code, 400)
        self.md.refresh_from_db()
        self.assertTrue(self.md.is_active)

    def test_md_set_password_and_login_with_new_password(self):
        self.client.force_authenticate(self.md)
        new_password = 'Fresh!Secret9182'
        response = self.client.post(
            f'/api/auth/users/{self.technician.pk}/set-password/',
            {'new_password': new_password},
        )
        self.assertEqual(response.status_code, 200, response.data)

        self.client.force_authenticate(None)
        login = self.client.post('/api/auth/login/', {
            'email': self.technician.email,
            'password': new_password,
        })
        self.assertEqual(login.status_code, 200, login.data)
        self.assertIn('access', login.data)

    # ------------------------------------------------------------------
    # Login auditing
    # ------------------------------------------------------------------
    def test_login_success_creates_audit_log(self):
        response = self.client.post('/api/auth/login/', {
            'email': self.supervisor.email,
            'password': PASSWORD,
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.supervisor, action='login', entity_type='User',
                entity_id=str(self.supervisor.pk),
            ).exists()
        )

    def test_login_failure_creates_no_audit_log(self):
        response = self.client.post('/api/auth/login/', {
            'email': self.supervisor.email,
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, 401)
        self.assertFalse(AuditLog.objects.filter(action='login').exists())
