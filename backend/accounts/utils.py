import re
import secrets

from django.utils.text import slugify

# No 0/O/1/I — codes are read aloud and typed by hand.
INVITE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def generate_username(email):
    """Derive a unique username from an email's local part."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    base = re.sub(r'[^a-z0-9._-]', '', email.split('@')[0].lower()) or 'user'
    candidate = base
    suffix = 2
    while User.objects.filter(username=candidate).exists():
        candidate = f'{base}{suffix}'
        suffix += 1
    return candidate


def generate_invite_code(company_name):
    """Build a PREF-XXXX invite code from the company name."""
    prefix = re.sub(r'[^A-Z0-9]', '', company_name.upper())[:4]
    prefix = (prefix + 'XXXX')[:4]
    suffix = ''.join(secrets.choice(INVITE_ALPHABET) for _ in range(4))
    return f'{prefix}-{suffix}'


def generate_company_slug(name):
    """Unique slug for a company, numeric suffix on collision."""
    from .models import Company

    base = slugify(name) or 'company'
    candidate = base
    suffix = 2
    while Company.objects.filter(slug=candidate).exists():
        candidate = f'{base}-{suffix}'
        suffix += 1
    return candidate
