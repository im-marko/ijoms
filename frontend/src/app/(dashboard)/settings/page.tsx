'use client';

import { useEffect, useState } from 'react';
import api, { getApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { User } from '@/types';
import { ROLE_LABELS } from '@/lib/roles';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { refreshUser } = useAuth();
  const [me, setMe] = useState<User | null>(null);
  const [profile, setProfile] = useState({ first_name: '', last_name: '', phone: '' });
  const [savingProfile, setSavingProfile] = useState(false);

  const [passwords, setPasswords] = useState({ old_password: '', new_password: '', confirm_password: '' });
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const res = await api.get<User>('/auth/me/');
        setMe(res.data);
        setProfile({
          first_name: res.data.first_name,
          last_name: res.data.last_name,
          phone: res.data.phone,
        });
      } catch (err) {
        toast.error(getApiError(err));
      }
    };
    fetchMe();
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      const res = await api.patch<User>('/auth/me/', profile);
      setMe(res.data);
      toast.success('Profile updated');
      await refreshUser();
    } catch (err) {
      toast.error(getApiError(err));
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwords.new_password !== passwords.confirm_password) {
      toast.error('New passwords do not match');
      return;
    }
    setChangingPassword(true);
    try {
      await api.post('/auth/change-password/', {
        old_password: passwords.old_password,
        new_password: passwords.new_password,
      });
      toast.success('Password changed successfully');
      setPasswords({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      toast.error(getApiError(err));
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {/* Profile */}
      <Card>
        <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSaveProfile} className="max-w-lg space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Company</Label>
                <Input disabled value={me?.company_name || '-'} />
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Input disabled value={me ? ROLE_LABELS[me.role] || me.role : ''} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input disabled value={me?.email || ''} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>First Name</Label>
                <Input required value={profile.first_name} onChange={(e) => setProfile({ ...profile, first_name: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Last Name</Label>
                <Input required value={profile.last_name} onChange={(e) => setProfile({ ...profile, last_name: e.target.value })} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Phone</Label>
              <Input value={profile.phone} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} />
            </div>
            <Button type="submit" disabled={savingProfile}>{savingProfile ? 'Saving...' : 'Save Changes'}</Button>
          </form>
        </CardContent>
      </Card>

      {/* Change password (hidden for Google-only accounts) */}
      {me?.has_usable_password === false ? (
        <Card>
          <CardHeader><CardTitle>Password</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">
              You sign in with Google, so there&apos;s no password to manage here.
            </p>
          </CardContent>
        </Card>
      ) : (
      <Card>
        <CardHeader><CardTitle>Change Password</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="max-w-lg space-y-4">
            <div className="space-y-2">
              <Label>Current Password</Label>
              <Input type="password" required value={passwords.old_password} onChange={(e) => setPasswords({ ...passwords, old_password: e.target.value })} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>New Password</Label>
                <Input type="password" required value={passwords.new_password} onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Confirm New Password</Label>
                <Input type="password" required value={passwords.confirm_password} onChange={(e) => setPasswords({ ...passwords, confirm_password: e.target.value })} />
              </div>
            </div>
            <Button type="submit" disabled={changingPassword}>{changingPassword ? 'Changing...' : 'Change Password'}</Button>
          </form>
        </CardContent>
      </Card>
      )}
    </div>
  );
}
