import { UserRole } from '@/types';

export const ALL_ROLES: UserRole[] = [
  'managing_director',
  'operations_manager',
  'supervisor',
  'technician',
  'finance_officer',
];

export const ROLE_LABELS: Record<UserRole, string> = {
  managing_director: 'Managing Director',
  operations_manager: 'Operations Manager',
  supervisor: 'Supervisor',
  technician: 'Technician',
  finance_officer: 'Finance Officer',
};

export const MANAGER_ROLES: UserRole[] = ['managing_director', 'operations_manager'];
export const SUPERVISOR_AND_ABOVE: UserRole[] = [...MANAGER_ROLES, 'supervisor'];
export const CAN_MANAGE_JOBS: UserRole[] = ['operations_manager', 'supervisor'];

export function isManagerOrAbove(role: UserRole): boolean {
  return MANAGER_ROLES.includes(role);
}

export function isSupervisorOrAbove(role: UserRole): boolean {
  return SUPERVISOR_AND_ABOVE.includes(role);
}

export function canManageJobs(role: UserRole): boolean {
  return CAN_MANAGE_JOBS.includes(role);
}
