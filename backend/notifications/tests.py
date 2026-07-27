from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Notification
from .services import send_whatsapp_notification

User = get_user_model()

PASSWORD = 'Compl3x!Passw0rd'


def make_user(role, email, username, **extra):
    return User.objects.create_user(
        username=username, email=email, password=PASSWORD, role=role,
        first_name=username.capitalize(), last_name='User', **extra,
    )


class NotificationAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.technician = make_user('technician', 'tech@example.com', 'tech')
        cls.other = make_user('technician', 'other@example.com', 'other')
        cls.mine1 = Notification.objects.create(
            recipient=cls.technician, type='in_app', subject='Mine 1',
            message='m', status='sent',
        )
        cls.mine2 = Notification.objects.create(
            recipient=cls.technician, type='in_app', subject='Mine 2',
            message='m', status='sent', read=True,
        )
        cls.mine_email = Notification.objects.create(
            recipient=cls.technician, type='email', subject='Mine email',
            message='m', status='sent',
        )
        cls.theirs = Notification.objects.create(
            recipient=cls.other, type='in_app', subject='Theirs',
            message='m', status='sent',
        )

    def test_list_returns_only_own_notifications(self):
        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        ids = {row['id'] for row in response.data['results']}
        self.assertEqual(ids, {self.mine1.pk, self.mine2.pk, self.mine_email.pk})

    def test_mark_read(self):
        self.client.force_authenticate(self.technician)
        response = self.client.post(f'/api/notifications/{self.mine1.pk}/read/')
        self.assertEqual(response.status_code, 200)
        self.mine1.refresh_from_db()
        self.assertTrue(self.mine1.read)

    def test_mark_read_on_other_users_notification_404(self):
        self.client.force_authenticate(self.technician)
        response = self.client.post(f'/api/notifications/{self.theirs.pk}/read/')
        self.assertEqual(response.status_code, 404)
        self.theirs.refresh_from_db()
        self.assertFalse(self.theirs.read)

    def test_unread_count_counts_only_unread_in_app(self):
        # mine1 = in_app unread, mine2 = in_app read, mine_email = email unread
        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)


class WhatsAppServiceTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.recipient = make_user(
            'technician', 'wa@example.com', 'wa', phone='+263 77 123 4567'
        )

    @override_settings(WHATSAPP_ENABLED=False)
    def test_returns_none_when_disabled(self):
        result = send_whatsapp_notification(self.recipient, 'Hello')
        self.assertIsNone(result)
        self.assertFalse(Notification.objects.filter(type='whatsapp').exists())

    @override_settings(
        WHATSAPP_ENABLED=True,
        WHATSAPP_PHONE_NUMBER_ID='x',
        WHATSAPP_ACCESS_TOKEN='y',
    )
    @patch('notifications.services.requests.post')
    def test_sends_and_normalizes_phone_number(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        notification = send_whatsapp_notification(self.recipient, 'Job update')

        self.assertIsNotNone(notification)
        self.assertEqual(notification.type, 'whatsapp')
        self.assertEqual(notification.status, 'sent')
        self.assertIsNotNone(notification.sent_at)

        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs['json']
        # '+' and spaces stripped from the stored phone number
        self.assertEqual(payload['to'], '263771234567')
        self.assertEqual(payload['text']['body'], 'Job update')

    @override_settings(
        WHATSAPP_ENABLED=True,
        WHATSAPP_PHONE_NUMBER_ID='x',
        WHATSAPP_ACCESS_TOKEN='y',
    )
    @patch('notifications.services.requests.post')
    def test_missing_phone_number_marks_failed(self, mock_post):
        no_phone = make_user('technician', 'nophone@example.com', 'nophone')
        notification = send_whatsapp_notification(no_phone, 'Hello')
        self.assertEqual(notification.status, 'failed')
        mock_post.assert_not_called()
