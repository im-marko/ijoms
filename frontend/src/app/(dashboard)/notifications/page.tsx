'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { formatDistanceToNow } from 'date-fns';
import api, { getApiError } from '@/lib/api';
import { Notification, PaginatedResponse } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCheck } from 'lucide-react';
import { toast } from 'sonner';

const TYPE_COLORS: Record<string, string> = {
  in_app: 'bg-blue-100 text-blue-700',
  email: 'bg-purple-100 text-purple-700',
  whatsapp: 'bg-green-100 text-green-700',
};
const TYPE_LABELS: Record<string, string> = {
  in_app: 'In-App',
  email: 'Email',
  whatsapp: 'WhatsApp',
};

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const fetchNotifications = async () => {
    try {
      const res = await api.get<PaginatedResponse<Notification>>('/notifications/', { params: { page } });
      setNotifications(res.data.results);
      setTotal(res.data.count);
    } catch (err) {
      toast.error(getApiError(err));
    }
  };

  useEffect(() => { fetchNotifications(); }, [page]);

  const handleClick = async (n: Notification) => {
    if (!n.read) {
      setNotifications((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      try {
        await api.post(`/notifications/${n.id}/read/`);
      } catch (err) {
        toast.error(getApiError(err));
      }
    }
    if (n.related_job) {
      router.push(`/jobs/${n.related_job}`);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all/');
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      toast.success('All notifications marked as read');
    } catch (err) {
      toast.error(getApiError(err));
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
        <Button variant="outline" onClick={handleMarkAllRead} disabled={unreadCount === 0}>
          <CheckCheck className="mr-2 h-4 w-4" />Mark all as read
        </Button>
      </div>

      <Card>
        <CardContent className="divide-y p-0">
          {notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => handleClick(n)}
              className={`flex cursor-pointer items-start gap-3 px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800 ${
                !n.read ? 'bg-blue-50 dark:bg-blue-950/40' : ''
              }`}
            >
              <div className="mt-1.5 h-2 w-2 flex-shrink-0">
                {!n.read && <span className="block h-2 w-2 rounded-full bg-blue-600" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-sm ${!n.read ? 'font-bold text-gray-900' : 'font-medium text-gray-700'}`}>
                    {n.subject}
                  </span>
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${TYPE_COLORS[n.type] || 'bg-gray-100 text-gray-700'}`}>
                    {TYPE_LABELS[n.type] || n.type}
                  </span>
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-gray-500">{n.message}</p>
              </div>
              <span className="flex-shrink-0 text-xs text-gray-400">
                {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
              </span>
            </div>
          ))}
          {notifications.length === 0 && (
            <div className="py-8 text-center text-gray-500">No notifications</div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="text-sm text-gray-500">Page {page} of {Math.ceil(total / 20)}</span>
          <Button variant="outline" size="sm" disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}
    </div>
  );
}
