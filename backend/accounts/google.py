"""Google ID token verification, isolated so tests can mock it."""
from django.conf import settings


class GoogleAuthError(Exception):
    pass


def verify_google_token(credential):
    """Verify a Google Identity Services ID token.

    Returns {'email', 'given_name', 'family_name'} or raises GoogleAuthError.
    """
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleAuthError('Google sign-in is not configured.')
    try:
        claims = id_token.verify_oauth2_token(
            credential, google_requests.Request(), settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise GoogleAuthError('Invalid Google token.') from exc

    if not claims.get('email') or not claims.get('email_verified'):
        raise GoogleAuthError('Google account email is not verified.')

    return {
        'email': claims['email'],
        'given_name': claims.get('given_name', ''),
        'family_name': claims.get('family_name', ''),
    }
