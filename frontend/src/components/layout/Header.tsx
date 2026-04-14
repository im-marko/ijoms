'use client';

import { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Notification } from '@/types';

export default function Header() {
  const { user } = useAuth();
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const fetchUnread = async () => {
    try {
      const res = await api.get('/notifications/unread-count/');
      setUnread(res.data.unread_count);
    } catch {}
  };

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications/?page_size=5');
      setNotifications(res.data.results || res.data);
    } catch {}
  };

  useEffect(() => {
    fetchUnread();
    const interval = setInterval(fetchUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  const markAllRead = async () => {
    await api.post('/notifications/read-all/');
    setUnread(0);
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <h2 className="text-lg font-semibold text-gray-800">
        Welcome, {user?.first_name}
      </h2>

      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <button
              className="relative rounded-full p-2 hover:bg-gray-100"
              onClick={fetchNotifications}
            >
              <Bell className="h-5 w-5 text-gray-600" />
              {unread > 0 && (
                <Badge className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs flex items-center justify-center">
                  {unread}
                </Badge>
              )}
            </button>
          }
        />
        <DropdownMenuContent align="end" className="w-80">
          <div className="flex items-center justify-between px-3 py-2 border-b">
            <span className="text-sm font-semibold">Notifications</span>
            {unread > 0 && (
              <button onClick={markAllRead} className="text-xs text-blue-600 hover:underline">
                Mark all read
              </button>
            )}
          </div>
          {notifications.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-500">No notifications</div>
          ) : (
            notifications.map((n) => (
              <DropdownMenuItem key={n.id} className="flex flex-col items-start gap-1 p-3">
                <span className={cn('text-sm', !n.read && 'font-semibold')}>{n.subject}</span>
                <span className="text-xs text-gray-500">{new Date(n.created_at).toLocaleString()}</span>
              </DropdownMenuItem>
            ))
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}
