'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { Notice } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Megaphone } from 'lucide-react';
import { toast } from 'sonner';

const PRIORITY_STYLES: Record<string, string> = {
  low: 'border-l-gray-400',
  medium: 'border-l-blue-500',
  high: 'border-l-orange-500',
  critical: 'border-l-red-500',
};

export default function NoticeBoardPage() {
  const { user } = useAuth();
  const [notices, setNotices] = useState<Notice[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ title: '', content: '', priority: 'medium', expiry_date: '' });

  const canCreate = user && ['managing_director', 'operations_manager', 'supervisor'].includes(user.role);

  const fetchNotices = async () => {
    try {
      const res = await api.get('/noticeboard/');
      setNotices(res.data.results || res.data);
    } catch {}
  };

  useEffect(() => { fetchNotices(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = { ...form, target_roles: [] };
      if (!payload.expiry_date) delete payload.expiry_date;
      await api.post('/noticeboard/create/', payload);
      toast.success('Notice published');
      setDialogOpen(false);
      setForm({ title: '', content: '', priority: 'medium', expiry_date: '' });
      fetchNotices();
    } catch (err: any) {
      toast.error('Failed to create notice');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Notice Board</h1>
        {canCreate && (
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger render={<Button><Plus className="mr-2 h-4 w-4" />New Notice</Button>} />
            <DialogContent>
              <DialogHeader><DialogTitle>Create Notice</DialogTitle></DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label>Title</Label>
                  <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Content</Label>
                  <Textarea required rows={4} value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Select value={form.priority} onValueChange={(v) => v && setForm({ ...form, priority: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Expiry Date</Label>
                    <Input type="datetime-local" value={form.expiry_date} onChange={(e) => setForm({ ...form, expiry_date: e.target.value })} />
                  </div>
                </div>
                <Button type="submit" className="w-full">Publish Notice</Button>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="space-y-4">
        {notices.map((notice) => (
          <Card key={notice.id} className={`border-l-4 ${PRIORITY_STYLES[notice.priority]}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{notice.title}</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant={notice.priority === 'critical' ? 'destructive' : 'secondary'} className="capitalize">
                    {notice.priority}
                  </Badge>
                  <span className="text-xs text-gray-400">
                    {new Date(notice.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{notice.content}</p>
              {notice.created_by_detail && (
                <p className="mt-3 text-xs text-gray-400">
                  Posted by {notice.created_by_detail.first_name} {notice.created_by_detail.last_name}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
        {notices.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Megaphone className="h-12 w-12 text-gray-300" />
              <p className="mt-4 text-gray-500">No notices yet</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
