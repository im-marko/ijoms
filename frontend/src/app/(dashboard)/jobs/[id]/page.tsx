'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import api, { getApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { canManageJobs } from '@/lib/roles';
import { Job, User } from '@/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from '@/components/ui/dialog';
import { ArrowLeft, Clock, Pencil, UserPlus } from 'lucide-react';
import { toast } from 'sonner';

export default function JobDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);

  const [technicians, setTechnicians] = useState<User[]>([]);
  const [assignTo, setAssignTo] = useState('');
  const [assigning, setAssigning] = useState(false);

  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    title: '', description: '', priority: '', customer_name: '',
    customer_contact: '', customer_email: '',
  });

  const canManage = !!user && canManageJobs(user.role);

  const fetchJob = async () => {
    try {
      const res = await api.get(`/jobs/${id}/`);
      setJob(res.data);
    } catch (err) {
      toast.error(getApiError(err, 'Job not found'));
      router.push('/jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchJob(); }, [id]);

  useEffect(() => {
    if (!canManage) return;
    api.get('/auth/technicians/')
      .then((res) => setTechnicians(res.data.results ?? res.data))
      .catch((err) => toast.error(getApiError(err, 'Failed to load technicians')));
  }, [canManage]);

  const handleStatusUpdate = async () => {
    if (!newStatus) return;
    try {
      const res = await api.post(`/jobs/${id}/status/`, { status: newStatus, notes });
      setJob(res.data);
      setNewStatus('');
      setNotes('');
      toast.success('Status updated');
    } catch (err) {
      toast.error(getApiError(err, 'Failed to update status'));
    }
  };

  const handleAssign = async () => {
    if (!assignTo) return;
    setAssigning(true);
    try {
      const res = await api.post(`/jobs/${id}/assign/`, { assigned_to: Number(assignTo) });
      setJob(res.data);
      setAssignTo('');
      toast.success('Technician assigned');
    } catch (err) {
      toast.error(getApiError(err, 'Failed to assign technician'));
    } finally {
      setAssigning(false);
    }
  };

  const openEdit = () => {
    if (!job) return;
    setEditForm({
      title: job.title,
      description: job.description,
      priority: job.priority,
      customer_name: job.customer_name,
      customer_contact: job.customer_contact,
      customer_email: job.customer_email,
    });
    setEditOpen(true);
  };

  const handleEditSave = async () => {
    try {
      const res = await api.patch(`/jobs/${id}/`, editForm);
      setJob(res.data);
      setEditOpen(false);
      toast.success('Job updated');
    } catch (err) {
      toast.error(getApiError(err, 'Failed to update job'));
    }
  };

  if (loading || !job) {
    return <div className="flex items-center justify-center py-20"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" /></div>;
  }

  const transitions = job.allowed_transitions ?? [];
  const canUpdate = user && (
    user.role !== 'finance_officer' &&
    (user.role !== 'technician' || job.assigned_to === user.id)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => router.push('/jobs')}>
            <ArrowLeft className="mr-2 h-4 w-4" />Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{job.title}</h1>
            <p className="font-mono text-sm text-gray-500">{job.reference_number}</p>
          </div>
        </div>
        {canManage && (
          <Dialog open={editOpen} onOpenChange={setEditOpen}>
            <DialogTrigger
              render={
                <Button variant="outline" size="sm" onClick={openEdit}>
                  <Pencil className="mr-2 h-4 w-4" />Edit Job
                </Button>
              }
            />
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>Edit Job</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Title</Label>
                  <Input value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select value={editForm.priority} onValueChange={(v) => v && setEditForm({ ...editForm, priority: String(v) })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {['low', 'medium', 'high', 'critical'].map((p) => (
                        <SelectItem key={p} value={p} className="capitalize">{p}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Customer</Label>
                    <Input value={editForm.customer_name} onChange={(e) => setEditForm({ ...editForm, customer_name: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Contact</Label>
                    <Input value={editForm.customer_contact} onChange={(e) => setEditForm({ ...editForm, customer_contact: e.target.value })} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Customer Email</Label>
                  <Input type="email" value={editForm.customer_email} onChange={(e) => setEditForm({ ...editForm, customer_email: e.target.value })} />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setEditOpen(false)}>Cancel</Button>
                <Button onClick={handleEditSave}>Save Changes</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main info */}
        <Card className="md:col-span-2">
          <CardHeader><CardTitle>Job Details</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-gray-500">Description</Label>
              <p className="mt-1">{job.description}</p>
            </div>
            <Separator />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-500">Category</Label>
                <p>{job.category_detail?.name || '-'}</p>
              </div>
              <div>
                <Label className="text-gray-500">Priority</Label>
                <p className="capitalize">{job.priority}</p>
              </div>
              <div>
                <Label className="text-gray-500">Status</Label>
                <Badge className="mt-1 capitalize">{job.status.replace('_', ' ')}</Badge>
              </div>
              <div>
                <Label className="text-gray-500">SLA Deadline</Label>
                <p>{job.sla_deadline ? new Date(job.sla_deadline).toLocaleString() : '-'}</p>
                {job.is_sla_breached && <Badge variant="destructive" className="mt-1">SLA Breached</Badge>}
              </div>
            </div>
            <Separator />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-500">Customer</Label>
                <p>{job.customer_name}</p>
              </div>
              <div>
                <Label className="text-gray-500">Contact</Label>
                <p>{job.customer_contact || '-'}</p>
              </div>
              <div>
                <Label className="text-gray-500">Assigned To</Label>
                <p>{job.assigned_to_detail ? `${job.assigned_to_detail.first_name} ${job.assigned_to_detail.last_name}` : 'Unassigned'}</p>
              </div>
              <div>
                <Label className="text-gray-500">Created By</Label>
                <p>{job.created_by_detail ? `${job.created_by_detail.first_name} ${job.created_by_detail.last_name}` : '-'}</p>
              </div>
            </div>
            {job.resolution_notes && (
              <>
                <Separator />
                <div>
                  <Label className="text-gray-500">Resolution Notes</Label>
                  <p className="mt-1">{job.resolution_notes}</p>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Actions + history */}
        <div className="space-y-6">
          {canManage && job.status !== 'closed' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserPlus className="h-4 w-4" />
                  {job.assigned_to ? 'Reassign Technician' : 'Assign Technician'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Technician</Label>
                  <Select value={assignTo} onValueChange={(v) => v && setAssignTo(String(v))}>
                    <SelectTrigger><SelectValue placeholder="Select technician" /></SelectTrigger>
                    <SelectContent>
                      {technicians
                        .filter((t) => t.id !== job.assigned_to)
                        .map((t) => (
                          <SelectItem key={t.id} value={String(t.id)}>
                            {t.first_name} {t.last_name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleAssign} disabled={!assignTo || assigning} className="w-full">
                  {job.assigned_to ? 'Reassign' : 'Assign'}
                </Button>
              </CardContent>
            </Card>
          )}

          {canUpdate && transitions.length > 0 && (
            <Card>
              <CardHeader><CardTitle>Update Status</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>New Status</Label>
                  <Select value={newStatus} onValueChange={(v) => v && setNewStatus(String(v))}>
                    <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
                    <SelectContent>
                      {transitions.map((s) => (
                        <SelectItem key={s} value={s} className="capitalize">{s.replace('_', ' ')}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional notes..." />
                </div>
                <Button onClick={handleStatusUpdate} disabled={!newStatus} className="w-full">
                  Update Status
                </Button>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader><CardTitle>Status History</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(job.status_history || []).map((h) => (
                  <div key={h.id} className="flex items-start gap-3 text-sm">
                    <Clock className="mt-0.5 h-4 w-4 text-gray-400" />
                    <div>
                      <p>
                        <span className="capitalize font-medium">{h.from_status.replace('_', ' ')}</span>
                        {' -> '}
                        <span className="capitalize font-medium">{h.to_status.replace('_', ' ')}</span>
                      </p>
                      {h.notes && <p className="text-gray-500">{h.notes}</p>}
                      <p className="text-xs text-gray-400">
                        {h.changed_by_detail ? `${h.changed_by_detail.first_name} ${h.changed_by_detail.last_name} - ` : 'System - '}
                        {new Date(h.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
                {(!job.status_history || job.status_history.length === 0) && (
                  <p className="text-sm text-gray-500">No status changes yet</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
