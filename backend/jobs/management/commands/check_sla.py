import time

from django.core.management.base import BaseCommand

from jobs.services import escalate_overdue_jobs


class Command(BaseCommand):
    help = 'Escalate jobs past their SLA deadline. Use --loop for a dev watcher.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop', type=int, metavar='SECONDS', default=0,
            help='Re-run every N seconds instead of exiting (dev mode).',
        )

    def handle(self, *args, **options):
        interval = options['loop']
        while True:
            escalated = escalate_overdue_jobs()
            if escalated:
                refs = ', '.join(j.reference_number for j in escalated)
                self.stdout.write(self.style.WARNING(f'Escalated {len(escalated)}: {refs}'))
            else:
                self.stdout.write('No overdue jobs.')
            if not interval:
                break
            time.sleep(interval)
