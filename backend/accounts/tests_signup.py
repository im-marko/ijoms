"""Tests for the self-signup flows: company signup, invite-code join,
company detail, and invite regeneration."""
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from jobs.defaults import DEFAULT_CATEGORIES
from jobs.models import JobCategory
from .models import Company
from .test_utils import PASSWORD, TEST_REST_FRAMEWORK, make_company, make_user

User = get_user_model()


def signup_payload(**overrides):
    payload = {
        'email': 'founder@example.com',
        'first_name': 'Fiona',
        'last_name': 'Founder',
        'password': PASSWORD,
        'password_confirm': PASSWORD,
        'company_name': 'Fresh Ventures',
    }
    payload.update(overrides)
    return payload


def join_payload(invite_code, **overrides):
    payload = {
        'email': 'joiner@example.com',
        'first_name': 'Joe',
        'last_name': 'Joiner',
        'password': PASSWORD,
        'password_confirm': PASSWORD,
        'invite_code': invite_code,
    }
    payload.update(overrides)
    return payload


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class SignupCompanyTests(APITestCase):
    def test_signup_creates_company_admin_and_default_categories(self):
        response = self.client.post('/api/auth/signup-company/', signup_payload())
        self.assertEqual(response.status_code, 201, response.data)

        user = User.objects.get(email='founder@example.com')
        self.assertEqual(user.role, 'admin')
        self.assertIsNotNone(user.company)

        company = user.company
        self.assertEqual(company.name, 'Fresh Ventures')
        self.assertTrue(company.slug)
        self.assertTrue(company.invite_code)

        # 8 default job categories seeded for the new company
        self.assertEqual(
            JobCategory.objects.filter(company=company).count(),
            len(DEFAULT_CATEGORIES),
        )
        names = set(
            JobCategory.objects.filter(company=company).values_list('name', flat=True)
        )
        self.assertIn('Hardware Repair', names)

        # Returned access token authenticates against /me/
        access = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, 200, me.data)
        self.assertEqual(me.data['email'], 'founder@example.com')
        self.assertEqual(me.data['company'], company.pk)

    def test_signup_duplicate_email_rejected(self):
        company = make_company('Existing Co')
        make_user('technician', 'founder@example.com', 'founder', company=company)
        response = self.client.post('/api/auth/signup-company/', signup_payload())
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class JoinCompanyTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company('Joinable Co')

    def test_join_with_valid_code_case_insensitive(self):
        response = self.client.post(
            '/api/auth/join/', join_payload(self.company.invite_code.lower())
        )
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email='joiner@example.com')
        self.assertEqual(user.role, 'technician')
        self.assertEqual(user.company, self.company)

    def test_join_with_invalid_code_rejected(self):
        response = self.client.post('/api/auth/join/', join_payload('ZZZZ-9999'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('invite_code', response.data)
        self.assertFalse(User.objects.filter(email='joiner@example.com').exists())

    def test_join_with_existing_email_rejected(self):
        make_user('technician', 'joiner@example.com', 'joiner', company=self.company)
        response = self.client.post(
            '/api/auth/join/', join_payload(self.company.invite_code)
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class CompanyEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company('Endpoint Co')
        cls.admin = make_user('admin', 'admin@example.com', 'admin', company=cls.company)
        cls.technician = make_user('technician', 'tech@example.com', 'tech', company=cls.company)

    def test_admin_sees_invite_code(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/auth/company/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Endpoint Co')
        self.assertIsInstance(response.data['invite_code'], str)
        self.assertEqual(response.data['invite_code'], self.company.invite_code)

    def test_technician_does_not_see_invite_code(self):
        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/auth/company/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['invite_code'])

    def test_unauthenticated_gets_401(self):
        response = self.client.get('/api/auth/company/')
        self.assertEqual(response.status_code, 401)


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class RegenerateInviteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company('Regen Co')
        cls.admin = make_user('admin', 'admin@example.com', 'admin', company=cls.company)
        cls.technician = make_user('technician', 'tech@example.com', 'tech', company=cls.company)

    def test_admin_regenerates_and_old_code_stops_working(self):
        old_code = self.company.invite_code
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/auth/company/regenerate-invite/')
        self.assertEqual(response.status_code, 200, response.data)
        new_code = response.data['invite_code']
        self.assertNotEqual(new_code, old_code)
        self.company.refresh_from_db()
        self.assertEqual(self.company.invite_code, new_code)

        # Old code no longer joins
        self.client.force_authenticate(None)
        response = self.client.post('/api/auth/join/', join_payload(old_code))
        self.assertEqual(response.status_code, 400)
        self.assertIn('invite_code', response.data)

        # New code still joins
        response = self.client.post('/api/auth/join/', join_payload(new_code))
        self.assertEqual(response.status_code, 201, response.data)

    def test_technician_cannot_regenerate(self):
        self.client.force_authenticate(self.technician)
        response = self.client.post('/api/auth/company/regenerate-invite/')
        self.assertEqual(response.status_code, 403)
