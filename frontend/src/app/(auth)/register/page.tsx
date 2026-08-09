'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import api, { getApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import GoogleSignInButton from '@/components/GoogleSignInButton';
import { Briefcase, Building2, KeyRound } from 'lucide-react';

type Mode = 'create' | 'join';

interface GoogleStash {
  credential: string;
  email: string;
  first_name: string;
  last_name: string;
}

const EMPTY_FORM = {
  email: '', first_name: '', last_name: '', phone: '',
  password: '', password_confirm: '',
};

export default function RegisterPage() {
  const { loginWithTokens } = useAuth();
  const [mode, setMode] = useState<Mode>('create');
  const [companyName, setCompanyName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [form, setForm] = useState(EMPTY_FORM);
  const [googleStash, setGoogleStash] = useState<GoogleStash | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem('google_signup');
    if (raw) {
      try {
        setGoogleStash(JSON.parse(raw));
      } catch {
        sessionStorage.removeItem('google_signup');
      }
    }
  }, []);

  const update = (field: keyof typeof EMPTY_FORM, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const finishWithTokens = async (access: string, refresh: string) => {
    sessionStorage.removeItem('google_signup');
    await loginWithTokens(access, refresh);
  };

  const handleGoogleCredential = async (credential: string) => {
    setError('');
    try {
      const res = await api.post('/auth/google/', { credential });
      if (res.data.needs_company) {
        const stash: GoogleStash = {
          credential,
          email: res.data.email,
          first_name: res.data.first_name,
          last_name: res.data.last_name,
        };
        sessionStorage.setItem('google_signup', JSON.stringify(stash));
        setGoogleStash(stash);
      } else {
        await finishWithTokens(res.data.access, res.data.refresh);
      }
    } catch (err) {
      setError(getApiError(err, 'Google sign-in failed.'));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (googleStash) {
        // Re-submit the Google credential with the company choice.
        const payload =
          mode === 'create'
            ? { credential: googleStash.credential, company_name: companyName }
            : { credential: googleStash.credential, invite_code: inviteCode };
        const res = await api.post('/auth/google/', payload);
        if (res.data.needs_company) {
          setError('Please provide a company name or invite code.');
        } else {
          await finishWithTokens(res.data.access, res.data.refresh);
        }
      } else if (mode === 'create') {
        const res = await api.post('/auth/signup-company/', {
          company_name: companyName, ...form,
        });
        await finishWithTokens(res.data.access, res.data.refresh);
      } else {
        const res = await api.post('/auth/join/', {
          invite_code: inviteCode, ...form,
        });
        await finishWithTokens(res.data.access, res.data.refresh);
      }
    } catch (err) {
      const message = getApiError(err, 'Registration failed.');
      // An expired Google credential comes back as a 401.
      if (googleStash && message.includes('Google')) {
        sessionStorage.removeItem('google_signup');
        setGoogleStash(null);
        setError('Your Google session expired — please sign in with Google again.');
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const cancelGoogle = () => {
    sessionStorage.removeItem('google_signup');
    setGoogleStash(null);
    setError('');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-8">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
            <Briefcase className="h-6 w-6 text-blue-600" />
          </div>
          <CardTitle className="text-2xl">
            {googleStash ? `Almost there, ${googleStash.first_name || googleStash.email}` : 'Get Started'}
          </CardTitle>
          {googleStash && (
            <p className="text-sm text-gray-500">
              Signed in with Google as {googleStash.email}. Create your company or join one.
            </p>
          )}
        </CardHeader>
        <CardContent>
          {/* Mode toggle */}
          <div className="mb-6 grid grid-cols-2 gap-2 rounded-lg bg-gray-100 p-1">
            <button
              type="button"
              onClick={() => setMode('create')}
              className={`flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                mode === 'create' ? 'bg-white shadow text-blue-700' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Building2 className="h-4 w-4" />Create a company
            </button>
            <button
              type="button"
              onClick={() => setMode('join')}
              className={`flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                mode === 'join' ? 'bg-white shadow text-blue-700' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <KeyRound className="h-4 w-4" />Join with a code
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
            )}

            {mode === 'create' ? (
              <div className="space-y-2">
                <Label>Company Name</Label>
                <Input required value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Acme Field Services" />
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Invite Code</Label>
                <Input required value={inviteCode} onChange={(e) => setInviteCode(e.target.value.toUpperCase())} placeholder="ACME-7K2P" className="font-mono uppercase" />
                <p className="text-xs text-gray-500">Ask your company admin for the invite code.</p>
              </div>
            )}

            {!googleStash && (
              <>
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
                  <Label>Phone</Label>
                  <Input value={form.phone} onChange={(e) => update('phone', e.target.value)} />
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
              </>
            )}

            {mode === 'join' && !googleStash && (
              <p className="text-xs text-gray-500">
                You&apos;ll join as a Technician. Your company admin can change your role afterwards.
              </p>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading
                ? 'Working...'
                : mode === 'create' ? 'Create Company' : 'Join Company'}
            </Button>

            {googleStash ? (
              <p className="text-center text-sm text-gray-500">
                Not you?{' '}
                <button type="button" onClick={cancelGoogle} className="text-blue-600 hover:underline">
                  Start over
                </button>
              </p>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-gray-200" />
                  <span className="text-xs uppercase text-gray-400">or</span>
                  <div className="h-px flex-1 bg-gray-200" />
                </div>
                <GoogleSignInButton onCredential={handleGoogleCredential} text="signup_with" />
                <p className="text-center text-sm text-gray-500">
                  Already have an account?{' '}
                  <Link href="/login" className="text-blue-600 hover:underline">Sign in</Link>
                </p>
              </>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
