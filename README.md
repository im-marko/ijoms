# iJOMS - Intelligent Job & Operations Management System

A centralized web platform for managing operational jobs, assigning technicians, tracking customer data, and delivering analytics for data-driven decisions.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 6 + Django REST Framework |
| Frontend | Next.js 16 (App Router) + Tailwind CSS + shadcn/ui |
| Database | PostgreSQL (SQLite for dev) |
| Auth | JWT (SimpleJWT) with role-based access control |
| Charts | Recharts |
| Notifications | Email (SMTP) + WhatsApp Business Cloud API + In-App |

## Features

- **Authentication & RBAC** - 5 roles: Admin, Operations Manager, Supervisor, Technician, Finance Officer
- **Job Management** - Full lifecycle: create, assign, track, escalate, close with SLA deadlines
- **Job Dashboard** - Real-time stats, status distribution charts, technician workload
- **Notice Board** - Targeted announcements with priority levels and expiry dates
- **Notifications** - Email, WhatsApp, and in-app notifications on job events
- **Analytics & Reporting** - Job volume trends, SLA compliance, technician performance, escalation rates, CSV export
- **Audit Logs** - Searchable trail of all system actions with filtering by user, action, entity, and date range

## Project Structure

```
ijoms/
├── backend/                # Django REST API
│   ├── accounts/           # User model, auth, RBAC permissions
│   ├── jobs/               # Job CRUD, status state machine, categories
│   ├── notifications/      # Email, WhatsApp, in-app notification services
│   ├── analytics/          # Reports, dashboards, CSV export
│   ├── noticeboard/        # Announcements with role targeting
│   ├── auditlog/           # Audit trail with middleware auto-capture
│   └── ijoms/              # Django settings & root URL config
├── frontend/               # Next.js App Router
│   └── src/
│       ├── app/
│       │   ├── (auth)/     # Login & register pages
│       │   └── (dashboard)/ # Dashboard, jobs, noticeboard, analytics, audit logs
│       ├── components/     # Sidebar, Header, shadcn/ui components
│       ├── lib/            # API client (Axios + JWT interceptor), auth context
│       └── types/          # TypeScript interfaces
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (optional, SQLite works for development)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data    # Load mock data (60 jobs, 10 users, notices, audit logs)
python manage.py runserver    # Starts on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev                   # Starts on http://localhost:3000
```

### Environment Variables

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Backend environment variables (optional, defaults work for dev):
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=ijoms
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=yourpassword
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_TEMPLATE_NAME=your_approved_template   # required for messages outside the 24h service window
WHATSAPP_TEMPLATE_LANGUAGE=en_US
WHATSAPP_ENABLED=auto        # auto = on when credentials present; or true/false
CRON_SECRET=some-long-random-string   # protects POST /api/jobs/run-sla-check/
```

### WhatsApp notifications

WhatsApp sends use the Meta WhatsApp Business Cloud API and activate automatically
once `WHATSAPP_PHONE_NUMBER_ID` and `WHATSAPP_ACCESS_TOKEN` are set. Notifications
go out on job assignment, status changes, and SLA escalations, to users with a
phone number on their profile. Business-initiated messages outside an open 24-hour
customer service window require a Meta-**approved template** — create one with a
single body parameter (`{{1}}`) and set `WHATSAPP_TEMPLATE_NAME`; without a
template, free-form text is only delivered inside an open service window.

### SLA auto-escalation

Jobs past their SLA deadline are automatically moved to **Escalated**, with a
status-history entry, an audit record, and notifications to the assignee, the
job creator, and all managers/supervisors.

```bash
python manage.py check_sla              # run once
python manage.py check_sla --loop 300   # dev watcher: re-check every 5 minutes
```

In production, schedule `POST /api/jobs/run-sla-check/` (e.g. GitHub Actions cron)
with header `X-Cron-Secret: $CRON_SECRET`.

## Demo Accounts

After running `python manage.py seed_data`, these mock accounts are available.
**Password for every account: `Test@1234`**

| Email | Password | Role |
|-------|----------|------|
| director@ijoms.com | Test@1234 | Admin |
| opsmanager@ijoms.com | Test@1234 | Operations Manager |
| supervisor1@ijoms.com | Test@1234 | Supervisor |
| supervisor2@ijoms.com | Test@1234 | Supervisor |
| tech1@ijoms.com | Test@1234 | Technician |
| tech2@ijoms.com | Test@1234 | Technician |
| tech3@ijoms.com | Test@1234 | Technician |
| tech4@ijoms.com | Test@1234 | Technician |
| tech5@ijoms.com | Test@1234 | Technician |
| finance@ijoms.com | Test@1234 | Finance Officer |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login/` | JWT login (audited) |
| `POST /api/auth/register/` | Self-registration (always creates a Technician) |
| `GET/PATCH /api/auth/me/` | Current user profile (role/email immutable) |
| `POST /api/auth/change-password/` | Change own password |
| `GET/POST /api/auth/users/` | List/create users (Admin only) |
| `PATCH /api/auth/users/<id>/` | Update a user (Admin only) |
| `POST /api/auth/users/<id>/set-password/` | Admin password reset (Admin only) |
| `GET /api/jobs/` | List jobs (filtered, paginated) |
| `POST /api/jobs/create/` | Create a new job |
| `GET /api/jobs/<id>/` | Job detail with status history + allowed transitions |
| `PATCH /api/jobs/<id>/` | Edit job fields (status/assignee excluded) |
| `POST /api/jobs/<id>/status/` | Update job status (state machine enforced) |
| `POST /api/jobs/<id>/assign/` | Assign/reassign a technician |
| `POST /api/jobs/run-sla-check/` | Cron endpoint: escalate overdue jobs (X-Cron-Secret) |
| `GET /api/jobs/categories/` | Job categories |
| `GET /api/notifications/` | User notifications |
| `GET /api/noticeboard/` | Active notices |
| `GET /api/analytics/summary/` | Dashboard summary stats |
| `GET /api/analytics/technician-performance/` | Technician metrics |
| `GET /api/analytics/job-volume/` | Job volume over time |
| `GET /api/analytics/escalation-trends/` | Escalation trends |
| `GET /api/analytics/export/jobs/` | Export jobs as CSV |
| `GET /api/audit-logs/` | Audit log entries (filtered) |

## Role Permissions

| Feature | Admin | Ops Manager | Supervisor | Technician | Finance |
|---------|:--------:|:-----------:|:----------:|:----------:|:-------:|
| View all jobs | Yes | Yes | Yes | Own only | Read-only |
| Create/edit/assign jobs | No | Yes | Yes | No | No |
| Update job status | Yes | Yes | Yes | Own only | No |
| Reopen closed jobs | Yes | Yes | Yes | No | No |
| Dashboard summary | Yes | Yes | Yes | Own stats | Yes |
| View analytics | Yes | Yes | Limited | No | No |
| Manage users | Yes | No | No | No | No |
| Create notices | Yes | Yes | Yes | No | No |
| View audit logs | Yes | Yes | No | No | No |

## License

Private - Internal Use Only
