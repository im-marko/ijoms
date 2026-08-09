'use client';

import { useEffect, useState } from 'react';
import api, { getApiError } from '@/lib/api';
import { Company, User, UserRole, PaginatedResponse } from '@/types';
import { ALL_ROLES, ROLE_LABELS } from '@/lib/roles';
import RequireRole from '@/components/RequireRole';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Copy, KeyRound, Pencil, Plus, RefreshCw, Search, Ticket } from 'lucide-react';
import { toast } from 'sonner';

const ROLE_BADGE_COLORS: Record<UserRole, string> = {
  admin: 'bg-purple-100 text-purple-700',
  operations_manager: 'bg-blue-100 text-blue-700',
  supervisor: 'bg-yellow-100 text-yellow-700',
  technician: 'bg-green-100 text-green-700',
  finance_officer: 'bg-orange-100 text-orange-700',
};

const EMPTY_CREATE_FORM = {
  email: '', first_name: '', last_name: '',
  role: 'technician' as UserRole, phone: '', password: '',
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [activeFilter, setActiveFilter] = useState('all');

  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState(EMPTY_CREATE_FORM);

  const [editUser, setEditUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({
    first_name: '', last_name: '', role: 'technician' as UserRole, phone: '', is_active: true,
  });

  const [resetUser, setResetUser] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState('');

  const [company, setCompany] = useState<Company | null>(null);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    api.get<Company>('/auth/company/')
      .then((res) => setCompany(res.data))
      .catch((err) => toast.error(getApiError(err, 'Failed to load company info')));
  }, []);

  const copyInvite = () => {
    if (!company?.invite_code) return;
    navigator.clipboard.writeText(company.invite_code);
    toast.success('Invite code copied');
  };

  const regenerateInvite = async () => {
    if (!window.confirm('Regenerate the invite code? The current code will stop working immediately.')) return;
    setRegenerating(true);
    try {
      const res = await api.post('/auth/company/regenerate-invite/');
      setCompany((c) => (c ? { ...c, invite_code: res.data.invite_code } : c));
      toast.success('Invite code regenerated');
    } catch (err) {
      toast.error(getApiError(err, 'Failed to regenerate invite code'));
    } finally {
      setRegenerating(false);
    }
  };

  const fetchUsers = async () => {
    const params: Record<string, string | number> = { page, search };
    if (roleFilter !== 'all') params.role = roleFilter;
    if (activeFilter !== 'all') params.is_active = activeFilter;
    try {
      const res = await api.get<PaginatedResponse<User>>('/auth/users/', { params });
      setUsers(res.data.results);
      setTotal(res.data.count);
    } catch (err) {
      toast.error(getApiError(err));
    }
  };

  useEffect(() => { fetchUsers(); }, [page, roleFilter, activeFilter]);

  const handleSearch = () => { setPage(1); fetchUsers(); };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/auth/users/', createForm);
      toast.success('User created successfully');
      setCreateOpen(false);
      setCreateForm(EMPTY_CREATE_FORM);
      fetchUsers();
    } catch (err) {
      toast.error(getApiError(err));
    }
  };

  const openEdit = (u: User) => {
    setEditUser(u);
    setEditForm({
      first_name: u.first_name, last_name: u.last_name,
      role: u.role, phone: u.phone, is_active: u.is_active,
    });
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;
    try {
      await api.patch(`/auth/users/${editUser.id}/`, editForm);
      toast.success('User updated successfully');
      setEditUser(null);
      fetchUsers();
    } catch (err) {
      toast.error(getApiError(err));
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetUser) return;
    try {
      await api.post(`/auth/users/${resetUser.id}/set-password/`, { new_password: newPassword });
      toast.success('Password reset successfully');
      setResetUser(null);
      setNewPassword('');
    } catch (err) {
      toast.error(getApiError(err));
    }
  };

  return (
    <RequireRole roles={['admin']}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Users</h1>
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger render={<Button><Plus className="mr-2 h-4 w-4" />Add User</Button>} />
            <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
              <DialogHeader><DialogTitle>Add New User</DialogTitle></DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input type="email" required value={createForm.email} onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>First Name</Label>
                    <Input required value={createForm.first_name} onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Last Name</Label>
                    <Input required value={createForm.last_name} onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Role</Label>
                    <Select value={createForm.role} onValueChange={(v) => v && setCreateForm({ ...createForm, role: v as UserRole })} items={ALL_ROLES.map((r) => ({ value: r, label: ROLE_LABELS[r] }))}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {ALL_ROLES.map((r) => <SelectItem key={r} value={r}>{ROLE_LABELS[r]}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Phone</Label>
                    <Input value={createForm.phone} onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input type="password" required value={createForm.password} onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })} />
                </div>
                <Button type="submit" className="w-full">Create User</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Invite code */}
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
                <Ticket className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Company invite code</p>
                <p className="text-xs text-gray-500">
                  Share this code so new members can join {company?.name ?? 'your company'} as technicians.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-md border bg-gray-50 px-3 py-1.5 font-mono text-sm font-semibold tracking-wider">
                {company?.invite_code ?? '...'}
              </span>
              <Button variant="outline" size="sm" onClick={copyInvite} disabled={!company?.invite_code}>
                <Copy className="mr-1 h-3 w-3" />Copy
              </Button>
              <Button variant="outline" size="sm" onClick={regenerateInvite} disabled={regenerating}>
                <RefreshCw className={`mr-1 h-3 w-3 ${regenerating ? 'animate-spin' : ''}`} />Regenerate
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Filters */}
        <Card>
          <CardContent className="flex flex-wrap items-center gap-4 pt-6">
            <div className="flex items-center gap-2">
              <Input placeholder="Search users..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-64" onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
              <Button variant="outline" size="sm" onClick={handleSearch}><Search className="h-4 w-4" /></Button>
            </div>
            <Select value={roleFilter} onValueChange={(v) => { if (v) { setRoleFilter(String(v)); setPage(1); } }} items={[{ value: 'all', label: 'All Roles' }, ...ALL_ROLES.map((r) => ({ value: r, label: ROLE_LABELS[r] }))]}>
              <SelectTrigger className="w-48"><SelectValue placeholder="Role" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                {ALL_ROLES.map((r) => <SelectItem key={r} value={r}>{ROLE_LABELS[r]}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={activeFilter} onValueChange={(v) => { if (v) { setActiveFilter(String(v)); setPage(1); } }} items={[{ value: 'all', label: 'All Status' }, { value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive' }]}>
              <SelectTrigger className="w-36"><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="true">Active</SelectItem>
                <SelectItem value="false">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-sm text-gray-500">{total} users found</span>
          </CardContent>
        </Card>

        {/* Users table */}
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Username</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-medium">{u.first_name} {u.last_name}</TableCell>
                    <TableCell className="text-sm">{u.email}</TableCell>
                    <TableCell className="text-sm">{u.username}</TableCell>
                    <TableCell>
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${ROLE_BADGE_COLORS[u.role] || 'bg-gray-100 text-gray-700'}`}>
                        {ROLE_LABELS[u.role] || u.role}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">{u.phone || '-'}</TableCell>
                    <TableCell>
                      {u.is_active ? (
                        <Badge className="bg-green-100 text-green-700 text-xs">Active</Badge>
                      ) : (
                        <Badge variant="destructive" className="text-xs">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={() => openEdit(u)}>
                          <Pencil className="mr-1 h-3 w-3" />Edit
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => { setResetUser(u); setNewPassword(''); }}>
                          <KeyRound className="mr-1 h-3 w-3" />Reset Password
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {users.length === 0 && (
                  <TableRow><TableCell colSpan={7} className="py-8 text-center text-gray-500">No users found</TableCell></TableRow>
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

        {/* Edit dialog */}
        <Dialog open={!!editUser} onOpenChange={(open) => !open && setEditUser(null)}>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Edit User{editUser ? ` — ${editUser.first_name} ${editUser.last_name}` : ''}</DialogTitle></DialogHeader>
            <form onSubmit={handleEdit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>First Name</Label>
                  <Input required value={editForm.first_name} onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Last Name</Label>
                  <Input required value={editForm.last_name} onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select value={editForm.role} onValueChange={(v) => v && setEditForm({ ...editForm, role: v as UserRole })} items={ALL_ROLES.map((r) => ({ value: r, label: ROLE_LABELS[r] }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ALL_ROLES.map((r) => <SelectItem key={r} value={r}>{ROLE_LABELS[r]}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={editForm.is_active ? 'true' : 'false'} onValueChange={(v) => v && setEditForm({ ...editForm, is_active: v === 'true' })} items={[{ value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive' }]}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">Active</SelectItem>
                    <SelectItem value="false">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button type="submit" className="w-full">Save Changes</Button>
            </form>
          </DialogContent>
        </Dialog>

        {/* Reset password dialog */}
        <Dialog open={!!resetUser} onOpenChange={(open) => !open && setResetUser(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader><DialogTitle>Reset Password{resetUser ? ` — ${resetUser.first_name} ${resetUser.last_name}` : ''}</DialogTitle></DialogHeader>
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="space-y-2">
                <Label>New Password</Label>
                <Input type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              </div>
              <Button type="submit" className="w-full">Reset Password</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </RequireRole>
  );
}
