import json

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.test_utils import make_company, make_user
from .mixins import log_action
from .models import AuditLog

User = get_user_model()


class AuditLogAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company('Audit TestCo')
        cls.om = make_user('operations_manager', 'om@example.com', 'om', company=cls.company)
        cls.technician = make_user('technician', 'tech@example.com', 'tech', company=cls.company)
        AuditLog.objects.create(
            company=cls.company, user=cls.om, action='create',
            entity_type='Job', entity_id='1',
        )
        AuditLog.objects.create(
            company=cls.company, user=cls.om, action='update',
            entity_type='Job', entity_id='1',
        )
        AuditLog.objects.create(
            company=cls.company, user=cls.technician, action='login',
            entity_type='User', entity_id=str(cls.technician.pk),
        )

    def test_list_as_operations_manager(self):
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/audit-logs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)

    def test_list_as_technician_forbidden(self):
        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/audit-logs/')
        self.assertEqual(response.status_code, 403)

    def test_action_filter(self):
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/audit-logs/?action=create')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        for row in response.data['results']:
            self.assertEqual(row['action'], 'create')


class LogActionSerializationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company('Audit TestCo 2')
        cls.om = make_user('operations_manager', 'om2@example.com', 'om2', company=cls.company)
        cls.technician = make_user('technician', 'tech2@example.com', 'tech2', company=cls.company)

    def test_log_action_coerces_model_instances_and_datetimes(self):
        now = timezone.now()
        # Must not raise despite non-JSON-native values
        log_action(
            user=self.om,
            action='update',
            entity_type='Job',
            entity_id=42,
            changes={
                'assigned_to': self.technician,       # model instance
                'deadline': now,                       # datetime
                'nested': {'user': self.om},           # nested model instance
                'items': [self.technician, 'text', 3],
            },
        )
        log = AuditLog.objects.get(entity_type='Job', entity_id='42')
        # Stored changes must be plain JSON-serializable data
        json.dumps(log.changes)
        self.assertEqual(log.changes['assigned_to'], str(self.technician))
        self.assertEqual(log.changes['nested']['user'], str(self.om))
        self.assertEqual(log.changes['items'][0], str(self.technician))
        self.assertIsInstance(log.changes['deadline'], str)
