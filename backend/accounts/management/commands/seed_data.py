"""
Seed a company with realistic mock data.
Usage: python manage.py seed_data [--company <slug>]
Defaults to (creating) the Demo Company.
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import Company
from jobs.models import Job, JobCategory, JobStatusHistory
from noticeboard.models import Notice
from notifications.models import Notification
from auditlog.models import AuditLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds a company with mock data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company', default='demo', metavar='SLUG',
            help='Slug of the company to seed (default: demo, created if missing).',
        )

    def handle(self, *args, **options):
        slug = options['company']
        company = Company.objects.filter(slug=slug).first()
        if company is None:
            if slug != 'demo':
                raise CommandError(f'Company with slug "{slug}" does not exist.')
            company = Company.objects.create(name='Demo Company', slug='demo')

        self.stdout.write(f'Seeding company "{company.name}"...\n')

        self._create_users(company)
        self._create_categories(company)
        self._create_jobs(company)
        self._create_notices(company)
        self._create_audit_logs(company)

        self.stdout.write(self.style.SUCCESS('\nDone! Mock data seeded successfully.'))
        self.stdout.write(self.style.SUCCESS('\nLogin credentials (all passwords: "Test@1234"):'))
        for u in User.objects.filter(company=company):
            self.stdout.write(f'  {u.email:<35} role: {u.get_role_display()}')

    def _create_users(self, company):
        self.stdout.write('  Creating users...')
        users_data = [
            {'email': 'director@ijoms.com', 'username': 'director', 'first_name': 'James',
             'last_name': 'Mwangi', 'role': 'admin', 'phone': '+254700100100'},
            {'email': 'opsmanager@ijoms.com', 'username': 'opsmanager', 'first_name': 'Sarah',
             'last_name': 'Ochieng', 'role': 'operations_manager', 'phone': '+254700200200'},
            {'email': 'supervisor1@ijoms.com', 'username': 'supervisor1', 'first_name': 'Peter',
             'last_name': 'Kamau', 'role': 'supervisor', 'phone': '+254700300300'},
            {'email': 'supervisor2@ijoms.com', 'username': 'supervisor2', 'first_name': 'Grace',
             'last_name': 'Wanjiku', 'role': 'supervisor', 'phone': '+254700300301'},
            {'email': 'tech1@ijoms.com', 'username': 'tech1', 'first_name': 'David',
             'last_name': 'Njoroge', 'role': 'technician', 'phone': '+254700400400'},
            {'email': 'tech2@ijoms.com', 'username': 'tech2', 'first_name': 'Mary',
             'last_name': 'Akinyi', 'role': 'technician', 'phone': '+254700400401'},
            {'email': 'tech3@ijoms.com', 'username': 'tech3', 'first_name': 'John',
             'last_name': 'Otieno', 'role': 'technician', 'phone': '+254700400402'},
            {'email': 'tech4@ijoms.com', 'username': 'tech4', 'first_name': 'Ann',
             'last_name': 'Muthoni', 'role': 'technician', 'phone': '+254700400403'},
            {'email': 'tech5@ijoms.com', 'username': 'tech5', 'first_name': 'Brian',
             'last_name': 'Kiprop', 'role': 'technician', 'phone': '+254700400404'},
            {'email': 'finance@ijoms.com', 'username': 'finance', 'first_name': 'Lucy',
             'last_name': 'Chebet', 'role': 'finance_officer', 'phone': '+254700500500'},
        ]
        for data in users_data:
            if not User.objects.filter(email=data['email']).exists():
                User.objects.create_user(password='Test@1234', company=company, **data)
        self.stdout.write(self.style.SUCCESS(f'  {len(users_data)} users created'))

    def _create_categories(self, company):
        self.stdout.write('  Creating job categories...')
        from jobs.defaults import DEFAULT_CATEGORIES, create_default_categories
        create_default_categories(company)
        self.stdout.write(self.style.SUCCESS(f'  {len(DEFAULT_CATEGORIES)} categories created'))

    def _create_jobs(self, company):
        self.stdout.write('  Creating jobs...')
        now = timezone.now()
        technicians = list(User.objects.filter(company=company, role='technician'))
        supervisors = list(User.objects.filter(company=company, role__in=['operations_manager', 'supervisor']))
        categories = list(JobCategory.objects.filter(company=company))

        customers = [
            ('Nairobi Business Park', '+254711111111', 'admin@nbp.co.ke'),
            ('Westlands Mall', '+254722222222', 'ops@westlandsmall.com'),
            ('KCA University', '+254733333333', 'ict@kca.ac.ke'),
            ('Safari Hotels Group', '+254744444444', 'maintenance@safarihotels.com'),
            ('Equity Bank HQ', '+254755555555', 'it@equitybank.co.ke'),
            ('Kenyatta Hospital', '+254766666666', 'tech@knhospital.go.ke'),
            ('JKIA Terminal 2', '+254777777777', 'ops@jkia.go.ke'),
            ('Karen Country Club', '+254788888888', 'admin@karenclub.co.ke'),
            ('Uhuru Gardens', '+254799999999', 'maintenance@uhurugardens.go.ke'),
            ('Aga Khan Hospital', '+254710101010', 'ict@agakhan.org'),
            ('Strathmore University', '+254720202020', 'support@strathmore.edu'),
            ('Two Rivers Mall', '+254730303030', 'facilities@tworivers.co.ke'),
            ('Nation Media Group', '+254740404040', 'it@nationmedia.com'),
            ('Safaricom HQ', '+254750505050', 'infra@safaricom.co.ke'),
            ('Garden City Mall', '+254760606060', 'ops@gardencity.co.ke'),
        ]

        job_titles = {
            'Network Installation': [
                'LAN cabling for new office wing', 'Wi-Fi access point deployment',
                'Fibre optic termination - Floor 3', 'Network switch rack installation',
                'Structured cabling for conference rooms',
            ],
            'Hardware Repair': [
                'Replace faulty UPS unit', 'Desktop PC motherboard replacement',
                'Printer repair - paper jam mechanism', 'Monitor replacement - cracked screen',
                'Laptop keyboard replacement',
            ],
            'Software Installation': [
                'Windows Server 2022 deployment', 'ERP system installation',
                'Antivirus rollout - 50 workstations', 'Office 365 migration',
                'POS system software update',
            ],
            'Preventive Maintenance': [
                'Quarterly server room inspection', 'UPS battery health check',
                'Air conditioning maintenance - server room', 'Fire suppression system test',
                'Generator maintenance schedule',
            ],
            'Emergency Repair': [
                'Main server down - critical failure', 'Power outage affecting data center',
                'Ransomware incident response', 'Network backbone failure',
                'Core switch failure - building offline',
            ],
            'Security System': [
                'CCTV camera replacement - parking lot', 'Access control card reader install',
                'Alarm system upgrade', 'DVR storage expansion',
                'Biometric scanner installation',
            ],
            'Server Maintenance': [
                'RAID array rebuild', 'Server RAM upgrade',
                'Backup system configuration', 'Domain controller patching',
                'Virtual machine migration',
            ],
            'Electrical Work': [
                'Power distribution unit installation', 'Emergency lighting repair',
                'Electrical panel upgrade', 'Socket installation - new workstations',
                'Surge protector installation',
            ],
        }

        statuses_with_weights = [
            ('open', 15),
            ('assigned', 20),
            ('in_progress', 25),
            ('escalated', 10),
            ('closed', 30),
        ]
        priorities = ['low', 'medium', 'medium', 'high', 'high', 'critical']

        created_count = 0
        for i in range(60):
            cat = random.choice(categories)
            titles = job_titles.get(cat.name, ['General task'])
            title = random.choice(titles)
            customer = random.choice(customers)
            creator = random.choice(supervisors)
            priority = random.choice(priorities)

            # Pick status weighted
            status = random.choices(
                [s[0] for s in statuses_with_weights],
                weights=[s[1] for s in statuses_with_weights],
            )[0]

            # Random creation date in the last 90 days
            days_ago = random.randint(0, 90)
            created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
            sla_deadline = created_at + timedelta(hours=cat.sla_hours)

            assigned_to = None
            closed_at = None
            resolution_notes = ''

            if status in ('assigned', 'in_progress', 'escalated', 'closed'):
                assigned_to = random.choice(technicians)

            if status == 'closed':
                close_delta = timedelta(hours=random.randint(2, cat.sla_hours + 24))
                closed_at = created_at + close_delta
                resolution_notes = random.choice([
                    'Issue resolved. All systems operational.',
                    'Replaced faulty component. Tested and verified working.',
                    'Software patched and reconfigured. Customer confirmed fix.',
                    'Completed installation. Customer signed off.',
                    'Temporary fix applied. Permanent solution scheduled for next maintenance window.',
                    'Root cause identified and addressed. Monitoring for recurrence.',
                ])

            job = Job(
                company=company,
                title=f'{title} - {customer[0]}',
                description=f'Job requested by {customer[0]}. {cat.description}. '
                            f'Contact: {customer[1]}. Priority: {priority}.',
                category=cat,
                priority=priority,
                status=status,
                assigned_to=assigned_to,
                created_by=creator,
                customer_name=customer[0],
                customer_contact=customer[1],
                customer_email=customer[2],
                sla_deadline=sla_deadline,
                resolution_notes=resolution_notes,
                closed_at=closed_at,
            )
            job.save()
            # Override created_at
            Job.objects.filter(pk=job.pk).update(created_at=created_at)

            # Create status history entries
            self._create_status_history(job, status, created_at, creator, assigned_to, technicians)
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'  {created_count} jobs created'))

    def _create_status_history(self, job, final_status, created_at, creator, assigned_to, technicians):
        transitions = []
        t = created_at + timedelta(minutes=random.randint(5, 120))

        if final_status in ('assigned', 'in_progress', 'escalated', 'closed'):
            transitions.append({
                'from_status': 'open', 'to_status': 'assigned',
                'changed_by': creator, 'notes': 'Job assigned to technician',
                'created_at': t,
            })
            t += timedelta(minutes=random.randint(30, 480))

        if final_status in ('in_progress', 'closed'):
            transitions.append({
                'from_status': 'assigned', 'to_status': 'in_progress',
                'changed_by': assigned_to or random.choice(technicians),
                'notes': 'Work started on site',
                'created_at': t,
            })
            t += timedelta(hours=random.randint(1, 48))

        if final_status == 'escalated':
            transitions.append({
                'from_status': 'assigned', 'to_status': 'escalated',
                'changed_by': assigned_to or random.choice(technicians),
                'notes': random.choice([
                    'SLA deadline approaching, escalating for priority attention.',
                    'Unable to resolve with current resources. Needs senior technician.',
                    'Customer escalation - high priority response required.',
                    'Parts unavailable. Escalating to procurement.',
                ]),
                'created_at': t,
            })

        if final_status == 'closed':
            transitions.append({
                'from_status': 'in_progress', 'to_status': 'closed',
                'changed_by': assigned_to or creator,
                'notes': 'Job completed and closed',
                'created_at': t,
            })

        for tr in transitions:
            h = JobStatusHistory.objects.create(
                job=job,
                from_status=tr['from_status'],
                to_status=tr['to_status'],
                changed_by=tr['changed_by'],
                notes=tr['notes'],
            )
            JobStatusHistory.objects.filter(pk=h.pk).update(created_at=tr['created_at'])

    def _create_notices(self, company):
        self.stdout.write('  Creating notices...')
        director = User.objects.filter(company=company, role='admin').first()
        ops = User.objects.filter(company=company, role='operations_manager').first()
        supervisor = User.objects.filter(company=company, role='supervisor').first()
        now = timezone.now()

        notices = [
            {
                'title': 'System Maintenance Window - April 19',
                'content': 'The iJOMS system will undergo scheduled maintenance on Saturday, April 19 from 02:00 to 06:00 EAT. '
                           'Please ensure all critical jobs are updated before the maintenance window. '
                           'The system will be unavailable during this period.',
                'priority': 'high', 'target_roles': [], 'created_by': director,
                'expiry_date': now + timedelta(days=5),
            },
            {
                'title': 'New SLA Policy Effective May 1',
                'content': 'Effective May 1, 2026, all Emergency Repair jobs must be acknowledged within 30 minutes of assignment. '
                           'Failure to acknowledge within the window will trigger automatic escalation. '
                           'Please review the updated SLA guidelines in the shared drive.',
                'priority': 'critical', 'target_roles': ['technician', 'supervisor'],
                'created_by': ops, 'expiry_date': now + timedelta(days=30),
            },
            {
                'title': 'Quarterly Performance Review Schedule',
                'content': 'Q1 2026 performance reviews will be conducted from April 21-25. '
                           'All technicians should prepare their job completion reports. '
                           'Supervisors will schedule individual review sessions.',
                'priority': 'medium', 'target_roles': ['technician', 'supervisor'],
                'created_by': ops, 'expiry_date': now + timedelta(days=14),
            },
            {
                'title': 'Welcome New Team Members',
                'content': 'We are pleased to welcome Brian Kiprop and Ann Muthoni to our technician team. '
                           'They bring extensive experience in network infrastructure and security systems respectively. '
                           'Please join us in welcoming them to the iJOMS family.',
                'priority': 'low', 'target_roles': [], 'created_by': director,
                'expiry_date': now + timedelta(days=7),
            },
            {
                'title': 'Safety Briefing - Electrical Work Protocol',
                'content': 'All technicians assigned to electrical work must complete the updated safety certification before May 15. '
                           'Training sessions are available every Tuesday at 09:00 in the main conference room. '
                           'Contact your supervisor to register.',
                'priority': 'high', 'target_roles': ['technician'],
                'created_by': supervisor, 'expiry_date': now + timedelta(days=31),
            },
            {
                'title': 'Monthly Team Meeting - April 30',
                'content': 'The monthly all-hands meeting will be held on April 30 at 14:00 in the boardroom. '
                           'Agenda includes Q1 performance review, Q2 targets, and the upcoming system upgrade roadmap. '
                           'Attendance is mandatory for all supervisors and above.',
                'priority': 'medium',
                'target_roles': ['admin', 'operations_manager', 'supervisor'],
                'created_by': director, 'expiry_date': now + timedelta(days=16),
            },
        ]

        for n in notices:
            Notice.objects.get_or_create(company=company, title=n['title'], defaults=n)
        self.stdout.write(self.style.SUCCESS(f'  {len(notices)} notices created'))

    def _create_audit_logs(self, company):
        self.stdout.write('  Creating audit log entries...')
        now = timezone.now()
        users = list(User.objects.filter(company=company))
        jobs = list(Job.objects.filter(company=company)[:30])

        actions = [
            ('create', 'Job'), ('update', 'Job'), ('status_change', 'Job'),
            ('assignment', 'Job'), ('create', 'Notice'), ('login', 'User'),
            ('update', 'User'), ('escalation', 'Job'),
        ]

        entries = []
        for i in range(80):
            action, entity_type = random.choice(actions)
            user = random.choice(users)
            entity_id = ''
            changes = {}

            if entity_type == 'Job' and jobs:
                job = random.choice(jobs)
                entity_id = str(job.pk)
                if action == 'status_change':
                    changes = {'from': 'open', 'to': 'assigned', 'notes': 'Job assigned'}
                elif action == 'assignment':
                    tech = random.choice([u for u in users if u.role == 'technician'])
                    changes = {'assigned_to': tech.get_full_name()}
            elif entity_type == 'User':
                entity_id = str(random.choice(users).pk)
            elif entity_type == 'Notice':
                entity_id = str(random.randint(1, 6))

            entries.append(AuditLog(
                company=company,
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                changes=changes,
                ip_address=f'192.168.1.{random.randint(10, 250)}',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/135.0',
            ))

        AuditLog.objects.bulk_create(entries)

        # Spread out created_at timestamps (scoped: never touch other companies' rows)
        logs = AuditLog.objects.filter(company=company).order_by('-pk')[:80]
        for j, log in enumerate(logs):
            ts = now - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            AuditLog.objects.filter(pk=log.pk).update(created_at=ts)

        self.stdout.write(self.style.SUCCESS(f'  {len(entries)} audit log entries created'))
