'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { Job, JobCategory, PaginatedResponse } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Search } from 'lucide-react';
import { toast } from 'sonner';

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};
const STATUS_COLORS: Record<string, string> = {
  open: 'bg-blue-100 text-blue-700',
  assigned: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-purple-100 text-purple-700',
  escalated: 'bg-red-100 text-red-700',
  closed: 'bg-green-100 text-green-700',
};

export default function JobsPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [categories, setCategories] = useState<JobCategory[]>([]);
  const [technicians, setTechnicians] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', category: '', priority: 'medium',
    assigned_to: '', customer_name: '', customer_contact: '', customer_email: '',
  });

  const canCreate = user && ['operations_manager', 'supervisor'].includes(user.role);

  const fetchJobs = async () => {
    const params: any = { page, search };
    if (statusFilter !== 'all') params.status = statusFilter;
    if (priorityFilter !== 'all') params.priority = priorityFilter;
    try {
      const res = await api.get<PaginatedResponse<Job>>('/jobs/', { params });
      setJobs(res.data.results);
      setTotal(res.data.count);
    } catch {}
  };

  useEffect(() => {
    fetchJobs();
  }, [page, statusFilter, priorityFilter]);

  useEffect(() => {
    api.get('/jobs/categories/').then((r) => setCategories(r.data.results || r.data)).catch(() => {});
    api.get('/auth/technicians/').then((r) => setTechnicians(r.data.results || r.data)).catch(() => {});
  }, []);

  const handleSearch = () => { setPage(1); fetchJobs(); };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = { ...form };
      if (payload.category) payload.category = parseInt(payload.category);
      if (payload.assigned_to) payload.assigned_to = parseInt(payload.assigned_to);
      else delete payload.assigned_to;
      await api.post('/jobs/create/', payload);
      toast.success('Job created successfully');
      setDialogOpen(false);
      setForm({ title: '', description: '', category: '', priority: 'medium', assigned_to: '', customer_name: '', customer_contact: '', customer_email: '' });
      fetchJobs();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create job');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        {canCreate && (
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger render={<Button><Plus className="mr-2 h-4 w-4" />New Job</Button>} />
            <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
              <DialogHeader><DialogTitle>Create New Job</DialogTitle></DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label>Title</Label>
                  <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Select value={form.category} onValueChange={(v) => v && setForm({ ...form, category: v })}>
                      <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                      <SelectContent>
                        {categories.map((c) => <SelectItem key={c.id} value={String(c.id)}>{c.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
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
                </div>
                <div className="space-y-2">
                  <Label>Assign To</Label>
                  <Select value={form.assigned_to} onValueChange={(v) => v && setForm({ ...form, assigned_to: v })}>
                    <SelectTrigger><SelectValue placeholder="Unassigned" /></SelectTrigger>
                    <SelectContent>
                      {technicians.map((t) => <SelectItem key={t.id} value={String(t.id)}>{t.first_name} {t.last_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Customer Name</Label>
                  <Input required value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Customer Contact</Label>
                    <Input value={form.customer_contact} onChange={(e) => setForm({ ...form, customer_contact: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Customer Email</Label>
                    <Input type="email" value={form.customer_email} onChange={(e) => setForm({ ...form, customer_email: e.target.value })} />
                  </div>
                </div>
                <Button type="submit" className="w-full">Create Job</Button>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-4 pt-6">
          <div className="flex items-center gap-2">
            <Input placeholder="Search jobs..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-64" onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
            <Button variant="outline" size="sm" onClick={handleSearch}><Search className="h-4 w-4" /></Button>
          </div>
          <Select value={statusFilter} onValueChange={(v) => { if (v) { setStatusFilter(v); setPage(1); } }}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="assigned">Assigned</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="escalated">Escalated</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={priorityFilter} onValueChange={(v) => { if (v) { setPriorityFilter(v); setPage(1); } }}>
            <SelectTrigger className="w-40"><SelectValue placeholder="Priority" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priority</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
          <span className="text-sm text-gray-500">{total} jobs found</span>
        </CardContent>
      </Card>

      {/* Jobs table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>SLA</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.id} className="cursor-pointer hover:bg-gray-50">
                  <TableCell>
                    <Link href={`/jobs/${job.id}`} className="text-blue-600 hover:underline font-mono text-sm">
                      {job.reference_number}
                    </Link>
                  </TableCell>
                  <TableCell className="font-medium">{job.title}</TableCell>
                  <TableCell><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_COLORS[job.priority]}`}>{job.priority}</span></TableCell>
                  <TableCell><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[job.status]}`}>{job.status.replace('_', ' ')}</span></TableCell>
                  <TableCell className="text-sm">{job.assigned_to_name || '-'}</TableCell>
                  <TableCell className="text-sm">{job.customer_name}</TableCell>
                  <TableCell>
                    {job.is_sla_breached ? (
                      <Badge variant="destructive" className="text-xs">Breached</Badge>
                    ) : job.sla_deadline ? (
                      <span className="text-xs text-gray-500">{new Date(job.sla_deadline).toLocaleDateString()}</span>
                    ) : '-'}
                  </TableCell>
                  <TableCell className="text-xs text-gray-500">{new Date(job.created_at).toLocaleDateString()}</TableCell>
                </TableRow>
              ))}
              {jobs.length === 0 && (
                <TableRow><TableCell colSpan={8} className="py-8 text-center text-gray-500">No jobs found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
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
