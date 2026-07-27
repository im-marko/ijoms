'use client';

import { useEffect, useState } from 'react';
import api, { getApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { ALL_ROLES, ROLE_LABELS, isSupervisorOrAbove } from '@/lib/roles';
import { Notice, UserRole } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Megaphone, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const PRIORITY_STYLES: Record<string, string> = {
  low: 'border-l-gray-400',
  medium: 'border-l-blue-500',
  high: 'border-l-orange-500',
  critical: 'border-l-red-500',
};

interface NoticeForm {
  title: string;
  content: string;
  priority: string;
  expiry_date: string;
  target_roles: UserRole[];
}

const EMPTY_FORM: NoticeForm = { title: '', content: '', priority: 'medium', expiry_date: '', target_roles: [] };

function RoleTargetPicker({ value, onChange }: { value: UserRole[]; onChange: (roles: UserRole[]) => void }) {
  const toggle = (role: UserRole) => {
    onChange(value.includes(role) ? value.filter((r) => r !== role) : [...value, role]);
  };
  return (
    <div className="space-y-2">
      <Label>Target Roles <span className="font-normal text-gray-400">(none selected = everyone)</span></Label>
      <div className="flex flex-wrap gap-2">
        {ALL_ROLES.map((role) => (
          <button
            key={role}
            type="button"
            onClick={() => toggle(role)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              value.includes(role)
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-200 text-gray-500 hover:bg-gray-50'
            }`}
          >
            {ROLE_LABELS[role]}
          </button>
        ))}
      </div>
    </div>
  );
}

function NoticeFormFields({ form, setForm }: { form: NoticeForm; setForm: (f: NoticeForm) => void }) {
  return (
    <>
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
          <Select value={form.priority} onValueChange={(v) => v && setForm({ ...form, priority: String(v) })}>
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
      <RoleTargetPicker value={form.target_roles} onChange={(roles) => setForm({ ...form, target_roles: roles })} />
    </>
  );
}

export default function NoticeBoardPage() {
  const { user } = useAuth();
  const [notices, setNotices] = useState<Notice[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState<NoticeForm>(EMPTY_FORM);
  const [editing, setEditing] = useState<Notice | null>(null);
  const [editForm, setEditForm] = useState<NoticeForm>(EMPTY_FORM);

  const canManage = !!user && isSupervisorOrAbove(user.role);

  const fetchNotices = async () => {
    try {
      const res = await api.get('/noticeboard/');
      setNotices(res.data.results || res.data);
    } catch (err) {
      toast.error(getApiError(err, 'Failed to load notices'));
    }
  };

  useEffect(() => { fetchNotices(); }, []);

  const buildPayload = (f: NoticeForm) => {
    const payload: Record<string, unknown> = {
      title: f.title, content: f.content, priority: f.priority, target_roles: f.target_roles,
    };
    if (f.expiry_date) payload.expiry_date = f.expiry_date;
    return payload;
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/noticeboard/create/', buildPayload(form));
      toast.success('Notice published');
      setDialogOpen(false);
      setForm(EMPTY_FORM);
      fetchNotices();
    } catch (err) {
      toast.error(getApiError(err, 'Failed to create notice'));
    }
  };

  const openEdit = (notice: Notice) => {
    setEditing(notice);
    setEditForm({
      title: notice.title,
      content: notice.content,
      priority: notice.priority,
      expiry_date: notice.expiry_date ? notice.expiry_date.slice(0, 16) : '',
      target_roles: (notice.target_roles || []) as UserRole[],
    });
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    try {
      await api.patch(`/noticeboard/${editing.id}/`, buildPayload(editForm));
      toast.success('Notice updated');
      setEditing(null);
      fetchNotices();
    } catch (err) {
      toast.error(getApiError(err, 'Failed to update notice'));
    }
  };

  const handleDelete = async (notice: Notice) => {
    if (!window.confirm(`Delete notice "${notice.title}"?`)) return;
    try {
      await api.delete(`/noticeboard/${notice.id}/`);
      toast.success('Notice deleted');
      fetchNotices();
    } catch (err) {
      toast.error(getApiError(err, 'Failed to delete notice'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Notice Board</h1>
        {canManage && (
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger render={<Button><Plus className="mr-2 h-4 w-4" />New Notice</Button>} />
            <DialogContent>
              <DialogHeader><DialogTitle>Create Notice</DialogTitle></DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <NoticeFormFields form={form} setForm={setForm} />
                <Button type="submit" className="w-full">Publish Notice</Button>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {canManage && (
        <Dialog open={!!editing} onOpenChange={(open) => !open && setEditing(null)}>
          <DialogContent>
            <DialogHeader><DialogTitle>Edit Notice</DialogTitle></DialogHeader>
            <form onSubmit={handleEdit} className="space-y-4">
              <NoticeFormFields form={editForm} setForm={setEditForm} />
              <Button type="submit" className="w-full">Save Changes</Button>
            </form>
          </DialogContent>
        </Dialog>
      )}

      <div className="space-y-4">
        {notices.map((notice) => (
          <Card key={notice.id} className={`border-l-4 ${PRIORITY_STYLES[notice.priority]}`}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{notice.title}</CardTitle>
                <div className="flex items-center gap-2">
                  {(notice.target_roles || []).map((role) => (
                    <Badge key={role} variant="outline" className="text-xs">
                      {ROLE_LABELS[role as UserRole] ?? role}
                    </Badge>
                  ))}
                  <Badge variant={notice.priority === 'critical' ? 'destructive' : 'secondary'} className="capitalize">
                    {notice.priority}
                  </Badge>
                  <span className="text-xs text-gray-400">
                    {new Date(notice.created_at).toLocaleDateString()}
                  </span>
                  {canManage && (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => openEdit(notice)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(notice)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </>
                  )}
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
