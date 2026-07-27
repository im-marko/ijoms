export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  role_display: string;
  phone: string;
  is_active: boolean;
  date_joined: string;
}

export type UserRole =
  | 'managing_director'
  | 'operations_manager'
  | 'supervisor'
  | 'technician'
  | 'finance_officer';

/** Shape returned by GET /jobs/ (JobListSerializer). */
export interface JobListItem {
  id: number;
  reference_number: string;
  title: string;
  category: number;
  category_name?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: JobStatus;
  assigned_to: number | null;
  assigned_to_name: string | null;
  created_by: number;
  created_by_name: string | null;
  customer_name: string;
  sla_deadline: string | null;
  is_sla_breached: boolean;
  created_at: string;
  updated_at: string;
}

/** Shape returned by GET /jobs/<id>/ (JobDetailSerializer). */
export interface Job {
  id: number;
  reference_number: string;
  title: string;
  description: string;
  category: number;
  category_detail?: JobCategory;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: JobStatus;
  assigned_to: number | null;
  assigned_to_detail?: User | null;
  created_by: number;
  created_by_detail?: User;
  customer_name: string;
  customer_contact: string;
  customer_email: string;
  sla_deadline: string | null;
  is_sla_breached: boolean;
  resolution_notes: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  status_history?: JobStatusHistory[];
  allowed_transitions: JobStatus[];
}

export type JobStatus = 'open' | 'assigned' | 'in_progress' | 'escalated' | 'closed';

export interface JobCategory {
  id: number;
  name: string;
  sla_hours: number;
  description: string;
  is_active: boolean;
}

export interface JobStatusHistory {
  id: number;
  from_status: string;
  to_status: string;
  changed_by: number | null;
  changed_by_detail?: User | null;
  notes: string;
  created_at: string;
}

export interface Notice {
  id: number;
  title: string;
  content: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  target_roles: string[];
  expiry_date: string | null;
  is_active: boolean;
  created_by: number;
  created_by_detail?: User;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  type: 'email' | 'whatsapp' | 'in_app';
  subject: string;
  message: string;
  status: string;
  related_job: number | null;
  read: boolean;
  sent_at: string | null;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user: number | null;
  user_detail?: User;
  action: string;
  entity_type: string;
  entity_id: string;
  changes: Record<string, unknown>;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
