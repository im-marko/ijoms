import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from auditlog.models import AuditLog
from notifications.models import Notification
from .models import Job, JobCategory, JobStatusHistory
from .services import escalate_overdue_jobs

User = get_user_model()

PASSWORD = 'Compl3x!Passw0rd'


def make_user(role, email, username):
    return User.objects.create_user(
        username=username, email=email, password=PASSWORD, role=role,
        first_name=username.capitalize(), last_name='User',
    )


class JobsBaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.md = make_user('managing_director', 'md@example.com', 'md')
        cls.om = make_user('operations_manager', 'om@example.com', 'om')
        cls.supervisor = make_user('supervisor', 'sup@example.com', 'sup')
        cls.technician = make_user('technician', 'tech@example.com', 'tech')
        cls.technician2 = make_user('technician', 'tech2@example.com', 'tech2')
        cls.finance = make_user('finance_officer', 'fin@example.com', 'fin')
        cls.category = JobCategory.objects.create(name='Electrical', sla_hours=24)

    def make_job(self, **overrides):
        defaults = dict(
            title='Fix generator',
            description='Generator will not start',
            category=self.category,
            created_by=self.om,
            customer_name='Acme Ltd',
        )
        defaults.update(overrides)
        return Job.objects.create(**defaults)


class JobCreateTests(JobsBaseTestCase):
    def test_create_with_technician_assignment(self):
        self.client.force_authenticate(self.om)
        response = self.client.post('/api/jobs/create/', {
            'title': 'Install router',
            'description': 'New site installation',
            'category': self.category.pk,
            'priority': 'high',
            'assigned_to': self.technician.pk,
            'customer_name': 'Beta Corp',
        })
        self.assertEqual(response.status_code, 201, response.data)

        job = Job.objects.get(title='Install router')
        self.assertEqual(job.status, 'assigned')
        self.assertEqual(job.assigned_to, self.technician)
        self.assertEqual(job.created_by, self.om)
        self.assertIsNotNone(job.sla_deadline)

        # Status history row for the initial assignment
        self.assertTrue(
            JobStatusHistory.objects.filter(
                job=job, from_status='open', to_status='assigned',
                changed_by=self.om,
            ).exists()
        )

        # Audit log with JSON-serializable changes (regression: model
        # instances used to be stored raw in the JSONField)
        log = AuditLog.objects.get(action='create', entity_type='Job', entity_id=str(job.pk))
        self.assertEqual(log.user, self.om)
        json.dumps(log.changes)  # must not raise
        self.assertEqual(log.changes['assigned_to'], self.technician.pk)
        self.assertEqual(log.changes['category'], self.category.pk)

        # Assignee notified
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.technician, related_job=job, type='in_app',
            ).exists()
        )

    def test_create_assigning_non_technician_rejected(self):
        self.client.force_authenticate(self.om)
        response = self.client.post('/api/jobs/create/', {
            'title': 'Bad assignment',
            'description': 'Should fail',
            'category': self.category.pk,
            'assigned_to': self.supervisor.pk,
            'customer_name': 'Acme Ltd',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('assigned_to', response.data)

    def test_create_as_technician_forbidden(self):
        self.client.force_authenticate(self.technician)
        response = self.client.post('/api/jobs/create/', {
            'title': 'Nope',
            'description': 'Nope',
            'category': self.category.pk,
            'customer_name': 'Acme Ltd',
        })
        self.assertEqual(response.status_code, 403)

    def test_create_as_finance_officer_forbidden(self):
        self.client.force_authenticate(self.finance)
        response = self.client.post('/api/jobs/create/', {
            'title': 'Nope',
            'description': 'Nope',
            'category': self.category.pk,
            'customer_name': 'Acme Ltd',
        })
        self.assertEqual(response.status_code, 403)


class JobUpdateTests(JobsBaseTestCase):
    def test_patch_updates_title_but_ignores_status_and_assignee(self):
        job = self.make_job()
        self.client.force_authenticate(self.om)
        response = self.client.patch(f'/api/jobs/{job.pk}/', {
            'title': 'Renamed job',
            'status': 'closed',
            'assigned_to': self.technician.pk,
        })
        self.assertEqual(response.status_code, 200, response.data)
        job.refresh_from_db()
        self.assertEqual(job.title, 'Renamed job')
        self.assertEqual(job.status, 'open')  # state machine not bypassed
        self.assertIsNone(job.assigned_to)

    def test_patch_as_technician_forbidden(self):
        job = self.make_job(assigned_to=self.technician, status='assigned')
        self.client.force_authenticate(self.technician)
        response = self.client.patch(f'/api/jobs/{job.pk}/', {'title': 'Hacked'})
        self.assertEqual(response.status_code, 403)


class JobStatusTransitionTests(JobsBaseTestCase):
    def test_valid_transition_writes_history(self):
        job = self.make_job(assigned_to=self.technician, status='assigned')
        self.client.force_authenticate(self.technician)
        response = self.client.post(
            f'/api/jobs/{job.pk}/status/',
            {'status': 'in_progress', 'notes': 'Starting work'},
        )
        self.assertEqual(response.status_code, 200, response.data)
        job.refresh_from_db()
        self.assertEqual(job.status, 'in_progress')
        self.assertTrue(
            JobStatusHistory.objects.filter(
                job=job, from_status='assigned', to_status='in_progress',
                changed_by=self.technician,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action='status_change', entity_type='Job', entity_id=str(job.pk),
            ).exists()
        )

    def test_invalid_transition_rejected(self):
        job = self.make_job()  # open
        self.client.force_authenticate(self.om)
        response = self.client.post(
            f'/api/jobs/{job.pk}/status/', {'status': 'in_progress'}
        )
        self.assertEqual(response.status_code, 400)
        job.refresh_from_db()
        self.assertEqual(job.status, 'open')

    def test_reopen_closed_job_as_supervisor(self):
        job = self.make_job(status='closed')
        job.refresh_from_db()
        self.assertIsNotNone(job.closed_at)
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            f'/api/jobs/{job.pk}/status/', {'status': 'open', 'notes': 'Reopening'}
        )
        self.assertEqual(response.status_code, 200, response.data)
        job.refresh_from_db()
        self.assertEqual(job.status, 'open')
        self.assertIsNone(job.closed_at)

    def test_reopen_closed_job_as_assigned_technician_forbidden(self):
        job = self.make_job(status='closed', assigned_to=self.technician)
        self.client.force_authenticate(self.technician)
        response = self.client.post(
            f'/api/jobs/{job.pk}/status/', {'status': 'open'}
        )
        self.assertEqual(response.status_code, 403)
        job.refresh_from_db()
        self.assertEqual(job.status, 'closed')


class JobAssignTests(JobsBaseTestCase):
    def test_supervisor_assigns_technician_to_open_job(self):
        job = self.make_job()  # open, unassigned
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            f'/api/jobs/{job.pk}/assign/', {'assigned_to': self.technician.pk}
        )
        self.assertEqual(response.status_code, 200, response.data)
        job.refresh_from_db()
        self.assertEqual(job.assigned_to, self.technician)
        self.assertEqual(job.status, 'assigned')
        self.assertTrue(
            JobStatusHistory.objects.filter(
                job=job, from_status='open', to_status='assigned',
                changed_by=self.supervisor,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action='assignment', entity_type='Job', entity_id=str(job.pk),
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.technician, related_job=job, type='in_app',
            ).exists()
        )

    def test_reassignment_writes_reassignment_audit_action(self):
        job = self.make_job(assigned_to=self.technician, status='assigned')
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            f'/api/jobs/{job.pk}/assign/', {'assigned_to': self.technician2.pk}
        )
        self.assertEqual(response.status_code, 200, response.data)
        job.refresh_from_db()
        self.assertEqual(job.assigned_to, self.technician2)
        log = AuditLog.objects.get(
            action='reassignment', entity_type='Job', entity_id=str(job.pk)
        )
        self.assertEqual(log.changes['from'], self.technician.pk)
        self.assertEqual(log.changes['to'], self.technician2.pk)

    def test_assign_as_technician_forbidden(self):
        job = self.make_job()
        self.client.force_authenticate(self.technician)
        response = self.client.post(
            f'/api/jobs/{job.pk}/assign/', {'assigned_to': self.technician.pk}
        )
        self.assertEqual(response.status_code, 403)

    def test_assign_closed_job_rejected(self):
        job = self.make_job(status='closed')
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            f'/api/jobs/{job.pk}/assign/', {'assigned_to': self.technician.pk}
        )
        self.assertEqual(response.status_code, 400)


class JobListScopingTests(JobsBaseTestCase):
    def test_technician_sees_only_own_jobs(self):
        mine = self.make_job(title='Mine', assigned_to=self.technician, status='assigned')
        self.make_job(title='Other tech', assigned_to=self.technician2, status='assigned')
        self.make_job(title='Unassigned')

        self.client.force_authenticate(self.technician)
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        ids = [row['id'] for row in response.data['results']]
        self.assertEqual(ids, [mine.pk])

    def test_manager_sees_all_jobs(self):
        self.make_job(title='One', assigned_to=self.technician, status='assigned')
        self.make_job(title='Two')
        self.client.force_authenticate(self.om)
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_finance_officer_can_list_jobs(self):
        self.make_job()
        self.client.force_authenticate(self.finance)
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)


class JobDetailTransitionsTests(JobsBaseTestCase):
    def test_closed_job_allowed_transitions_by_role(self):
        job = self.make_job(status='closed', assigned_to=self.technician)

        self.client.force_authenticate(self.supervisor)
        response = self.client.get(f'/api/jobs/{job.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['allowed_transitions'], ['open'])

        self.client.force_authenticate(self.technician)
        response = self.client.get(f'/api/jobs/{job.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['allowed_transitions'], [])

    def test_detail_includes_allowed_transitions_for_open_job(self):
        job = self.make_job()
        self.client.force_authenticate(self.om)
        response = self.client.get(f'/api/jobs/{job.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(response.data['allowed_transitions']),
            sorted(['assigned', 'escalated', 'closed']),
        )


class EscalationServiceTests(JobsBaseTestCase):
    def test_overdue_job_is_escalated(self):
        job = self.make_job(assigned_to=self.technician, status='assigned')
        job.sla_deadline = timezone.now() - timedelta(hours=2)
        job.save()

        escalated = escalate_overdue_jobs()
        self.assertEqual([j.pk for j in escalated], [job.pk])

        job.refresh_from_db()
        self.assertEqual(job.status, 'escalated')

        history = JobStatusHistory.objects.get(job=job, to_status='escalated')
        self.assertIsNone(history.changed_by)
        self.assertEqual(history.from_status, 'assigned')

        log = AuditLog.objects.get(
            action='escalation', entity_type='Job', entity_id=str(job.pk)
        )
        self.assertIsNone(log.user)
        json.dumps(log.changes)  # JSON-serializable

        # Assignee, creator, and active managers/supervisors all notified
        for recipient in (self.technician, self.om, self.supervisor):
            self.assertTrue(
                Notification.objects.filter(
                    recipient=recipient, related_job=job, type='in_app',
                ).exists(),
                f'missing notification for {recipient.email}',
            )

    def test_closed_and_future_deadline_jobs_not_escalated(self):
        closed = self.make_job(status='closed')
        Job.objects.filter(pk=closed.pk).update(
            sla_deadline=timezone.now() - timedelta(hours=5)
        )
        future = self.make_job(title='Future job')  # deadline now + 24h

        escalated = escalate_overdue_jobs()
        self.assertEqual(escalated, [])

        closed.refresh_from_db()
        future.refresh_from_db()
        self.assertEqual(closed.status, 'closed')
        self.assertEqual(future.status, 'open')
