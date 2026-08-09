"""Default job categories every new company starts with."""

DEFAULT_CATEGORIES = [
    {'name': 'Network Installation', 'sla_hours': 48, 'description': 'New network infrastructure setup and cabling'},
    {'name': 'Hardware Repair', 'sla_hours': 24, 'description': 'Repair of physical hardware components'},
    {'name': 'Software Installation', 'sla_hours': 12, 'description': 'Installation and configuration of software systems'},
    {'name': 'Preventive Maintenance', 'sla_hours': 72, 'description': 'Scheduled maintenance of equipment and systems'},
    {'name': 'Emergency Repair', 'sla_hours': 4, 'description': 'Critical system failures requiring immediate attention'},
    {'name': 'Security System', 'sla_hours': 24, 'description': 'CCTV, access control, and alarm system work'},
    {'name': 'Server Maintenance', 'sla_hours': 8, 'description': 'Server hardware and OS maintenance tasks'},
    {'name': 'Electrical Work', 'sla_hours': 36, 'description': 'Electrical installations and fault resolution'},
]


def create_default_categories(company):
    from .models import JobCategory
    for cat in DEFAULT_CATEGORIES:
        JobCategory.objects.get_or_create(
            company=company, name=cat['name'], defaults=cat,
        )
