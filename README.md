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

- **Authentication & RBAC** - 5 roles: Managing Director, Operations Manager, Supervisor, Technician, Finance Officer
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
```

## Demo Accounts

After running `python manage.py seed_data`, these accounts are available (password: `Test@1234`):

| Email | Role |
|-------|------|
| director@ijoms.com | Managing Director |
| opsmanager@ijoms.com | Operations Manager |
| supervisor1@ijoms.com | Supervisor |
| tech1@ijoms.com | Technician |
| finance@ijoms.com | Finance Officer |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login/` | JWT login |
| `POST /api/auth/register/` | User registration |
| `GET /api/auth/me/` | Current user profile |
| `GET /api/jobs/` | List jobs (filtered, paginated) |
| `POST /api/jobs/create/` | Create a new job |
| `GET /api/jobs/<id>/` | Job detail with status history |
| `POST /api/jobs/<id>/status/` | Update job status |
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

| Feature | Director | Ops Manager | Supervisor | Technician | Finance |
|---------|:--------:|:-----------:|:----------:|:----------:|:-------:|
| View all jobs | Yes | Yes | Yes | Own only | No |
| Create/assign jobs | No | Yes | Yes | No | No |
| Update job status | No | Yes | Yes | Own only | No |
| View analytics | Yes | Yes | Limited | No | No |
| Manage users | Yes | No | No | No | No |
| Create notices | Yes | Yes | Yes | No | No |
| View audit logs | Yes | Yes | No | No | No |

## License

Private - Internal Use Only
