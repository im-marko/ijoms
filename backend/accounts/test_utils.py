"""Shared helpers for the test suite under multi-tenancy."""
import copy

from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import Company

User = get_user_model()

PASSWORD = 'Compl3x!Passw0rd'

# Relax the scoped throttles so test runs never trip them (throttle history
# lives in the default cache, which survives across tests).
TEST_REST_FRAMEWORK = copy.deepcopy(settings.REST_FRAMEWORK)
TEST_REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'login': '1000/min',
    'register': '1000/hour',
    'google': '1000/min',
}


def make_company(name='TestCo'):
    return Company.objects.create(name=name)


def make_user(role, email, username, company=None, **extra):
    return User.objects.create_user(
        username=username, email=email, password=PASSWORD, role=role,
        first_name=username.capitalize(), last_name='User', company=company,
        **extra,
    )
