"""Tests for POST /api/auth/google/ with the token verifier mocked out.

verify_google_token is imported into accounts.views by name, so the patch
target is 'accounts.views.verify_google_token'.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from jobs.defaults import DEFAULT_CATEGORIES
from jobs.models import JobCategory
from .google import GoogleAuthError
from .models import Company
from .test_utils import TEST_REST_FRAMEWORK, make_company, make_user

User = get_user_model()

CLAIMS = {
    'email': 'guser@example.com',
    'given_name': 'Goo',
    'family_name': 'Gle',
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class GoogleAuthTests(APITestCase):
    @patch('accounts.views.verify_google_token', return_value=dict(CLAIMS))
    def test_existing_email_logs_in_and_ignores_company_name(self, mock_verify):
        company = make_company('Existing Co')
        make_user('technician', 'guser@example.com', 'guser', company=company)
        companies_before = Company.objects.count()

        response = self.client.post('/api/auth/google/', {
            'credential': 'tok', 'company_name': 'Should Be Ignored',
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'guser@example.com')
        # No new company was created for an existing user
        self.assertEqual(Company.objects.count(), companies_before)

    @patch('accounts.views.verify_google_token', return_value=dict(CLAIMS))
    def test_existing_inactive_user_rejected(self, mock_verify):
        company = make_company('Inactive Co')
        user = make_user('technician', 'guser@example.com', 'guser', company=company)
        user.is_active = False
        user.save(update_fields=['is_active'])

        response = self.client.post('/api/auth/google/', {'credential': 'tok'})
        self.assertEqual(response.status_code, 401)

    @patch('accounts.views.verify_google_token', return_value=dict(CLAIMS))
    def test_new_email_with_invite_code_joins_as_technician(self, mock_verify):
        company = make_company('Invite Co')
        response = self.client.post('/api/auth/google/', {
            'credential': 'tok', 'invite_code': company.invite_code.lower(),
        })
        self.assertEqual(response.status_code, 201, response.data)

        user = User.objects.get(email='guser@example.com')
        self.assertEqual(user.role, 'technician')
        self.assertEqual(user.company, company)
        self.assertFalse(user.has_usable_password())

        access = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, 200, me.data)
        self.assertFalse(me.data['has_usable_password'])

    @patch('accounts.views.verify_google_token', return_value=dict(CLAIMS))
    def test_new_email_with_company_name_creates_company_as_admin(self, mock_verify):
        response = self.client.post('/api/auth/google/', {
            'credential': 'tok', 'company_name': 'Google Founders Ltd',
        })
        self.assertEqual(response.status_code, 201, response.data)

        user = User.objects.get(email='guser@example.com')
        self.assertEqual(user.role, 'admin')
        self.assertIsNotNone(user.company)
        self.assertEqual(user.company.name, 'Google Founders Ltd')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(
            JobCategory.objects.filter(company=user.company).count(),
            len(DEFAULT_CATEGORIES),
        )

    @patch('accounts.views.verify_google_token', return_value=dict(CLAIMS))
    def test_new_email_without_company_or_code_needs_company(self, mock_verify):
        response = self.client.post('/api/auth/google/', {'credential': 'tok'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, {
            'needs_company': True,
            'email': 'guser@example.com',
            'first_name': 'Goo',
            'last_name': 'Gle',
        })
        self.assertFalse(User.objects.filter(email='guser@example.com').exists())

    @patch('accounts.views.verify_google_token', side_effect=GoogleAuthError('Invalid Google token.'))
    def test_verifier_failure_returns_401(self, mock_verify):
        response = self.client.post('/api/auth/google/', {'credential': 'bad'})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(User.objects.filter(email='guser@example.com').exists())

    @patch('accounts.views.verify_google_token', return_value=dict(CLAIMS))
    def test_new_email_with_bad_invite_code_rejected(self, mock_verify):
        response = self.client.post('/api/auth/google/', {
            'credential': 'tok', 'invite_code': 'ZZZZ-9999',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('invite_code', response.data)
        self.assertFalse(User.objects.filter(email='guser@example.com').exists())
