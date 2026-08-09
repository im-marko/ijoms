'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api, { getApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import GoogleSignInButton from '@/components/GoogleSignInButton';
import { Briefcase, Sparkles } from 'lucide-react';

const DEMO_ACCOUNTS = [
  { label: 'Admin', email: 'director@ijoms.com' },
  { label: 'Operations Manager', email: 'opsmanager@ijoms.com' },
  { label: 'Technician', email: 'tech1@ijoms.com' },
];
const DEMO_PASSWORD = 'Test@1234';

export default function LoginPage() {
  const { login, loginWithTokens } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showDemo, setShowDemo] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch {
      setError('Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleCredential = async (credential: string) => {
    setError('');
    try {
      const res = await api.post('/auth/google/', { credential });
      if (res.data.needs_company) {
        sessionStorage.setItem('google_signup', JSON.stringify({
          credential,
          email: res.data.email,
          first_name: res.data.first_name,
          last_name: res.data.last_name,
        }));
        router.push('/register');
      } else {
        await loginWithTokens(res.data.access, res.data.refresh);
      }
    } catch (err) {
      setError(getApiError(err, 'Google sign-in failed.'));
    }
  };

  const fillDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword(DEMO_PASSWORD);
    setShowDemo(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
            <Briefcase className="h-6 w-6 text-blue-600" />
          </div>
          <CardTitle className="text-2xl">Sign in to Job Pilot</CardTitle>
          <CardDescription>Intelligent Job & Operations Management</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email" type="email" required
                value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password" type="password" required
                value={password} onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>

            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-gray-200" />
              <span className="text-xs uppercase text-gray-400">or</span>
              <div className="h-px flex-1 bg-gray-200" />
            </div>
            <GoogleSignInButton onCredential={handleGoogleCredential} />

            <div className="text-center">
              <button
                type="button"
                onClick={() => setShowDemo((s) => !s)}
                className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
              >
                <Sparkles className="h-3.5 w-3.5" />Try the demo
              </button>
            </div>
            {showDemo && (
              <div className="space-y-2 rounded-lg border bg-blue-50/50 p-3">
                <p className="text-xs text-gray-600">
                  Explore Demo Company with pre-seeded data. Password: <span className="font-mono">{DEMO_PASSWORD}</span>
                </p>
                {DEMO_ACCOUNTS.map((acc) => (
                  <div key={acc.email} className="flex items-center justify-between text-sm">
                    <span>
                      <span className="font-medium">{acc.label}</span>{' '}
                      <span className="font-mono text-xs text-gray-500">{acc.email}</span>
                    </span>
                    <Button type="button" variant="outline" size="sm" onClick={() => fillDemo(acc.email)}>
                      Use
                    </Button>
                  </div>
                ))}
              </div>
            )}

            <p className="text-center text-sm text-gray-500">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="text-blue-600 hover:underline">Register</Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
