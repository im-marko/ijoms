'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Briefcase } from 'lucide-react';

const ROLES = [
  { value: 'technician', label: 'Technician' },
  { value: 'supervisor', label: 'Supervisor' },
  { value: 'operations_manager', label: 'Operations Manager' },
  { value: 'managing_director', label: 'Managing Director' },
  { value: 'finance_officer', label: 'Finance Officer' },
];

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: '', username: '', first_name: '', last_name: '',
    role: 'technician', phone: '', password: '', password_confirm: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/register/', form);
      router.push('/login');
    } catch (err: any) {
      const data = err.response?.data;
      const msg = data
        ? Object.values(data).flat().join(' ')
        : 'Registration failed.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
            <Briefcase className="h-6 w-6 text-blue-600" />
          </div>
          <CardTitle className="text-2xl">Create Account</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>First Name</Label>
                <Input required value={form.first_name} onChange={(e) => update('first_name', e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Last Name</Label>
                <Input required value={form.last_name} onChange={(e) => update('last_name', e.target.value)} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input type="email" required value={form.email} onChange={(e) => update('email', e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Username</Label>
              <Input required value={form.username} onChange={(e) => update('username', e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={form.role} onValueChange={(v) => v && update('role', v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ROLES.map((r) => (
                      <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input value={form.phone} onChange={(e) => update('phone', e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Password</Label>
                <Input type="password" required value={form.password} onChange={(e) => update('password', e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Confirm Password</Label>
                <Input type="password" required value={form.password_confirm} onChange={(e) => update('password_confirm', e.target.value)} />
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating...' : 'Create Account'}
            </Button>
            <p className="text-center text-sm text-gray-500">
              Already have an account?{' '}
              <Link href="/login" className="text-blue-600 hover:underline">Sign in</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
