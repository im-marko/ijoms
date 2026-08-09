'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard, Briefcase, Bell, BarChart3, Megaphone,
  ScrollText, LogOut, Users, Settings,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin', 'operations_manager', 'supervisor', 'technician', 'finance_officer'] },
  { href: '/jobs', label: 'Jobs', icon: Briefcase, roles: ['admin', 'operations_manager', 'supervisor', 'technician', 'finance_officer'] },
  { href: '/noticeboard', label: 'Notice Board', icon: Megaphone, roles: ['admin', 'operations_manager', 'supervisor', 'technician', 'finance_officer'] },
  { href: '/notifications', label: 'Notifications', icon: Bell, roles: ['admin', 'operations_manager', 'supervisor', 'technician', 'finance_officer'] },
  { href: '/analytics', label: 'Analytics', icon: BarChart3, roles: ['admin', 'operations_manager', 'supervisor'] },
  { href: '/audit-logs', label: 'Audit Logs', icon: ScrollText, roles: ['admin', 'operations_manager'] },
  { href: '/users', label: 'Users', icon: Users, roles: ['admin'] },
  { href: '/settings', label: 'Settings', icon: Settings, roles: ['admin', 'operations_manager', 'supervisor', 'technician', 'finance_officer'] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  const filtered = navItems.filter((item) => item.roles.includes(user.role));

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-white">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Briefcase className="h-6 w-6 shrink-0 text-blue-600" />
        {user.company_name ? (
          <div className="min-w-0">
            <p className="truncate text-base font-bold leading-tight text-blue-600">{user.company_name}</p>
            <p className="text-[10px] font-medium uppercase tracking-wider text-gray-400">Job Pilot</p>
          </div>
        ) : (
          <span className="text-xl font-bold text-blue-600">Job Pilot</span>
        )}
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {filtered.map((item) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-4">
        <div className="mb-3 px-3">
          <p className="text-sm font-medium text-gray-900">{user.first_name} {user.last_name}</p>
          <p className="text-xs text-gray-500">{user.role_display}</p>
        </div>
        <button
          onClick={() => logout()}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
        >
          <LogOut className="h-5 w-5" />
          Logout
        </button>
      </div>
    </aside>
  );
}
