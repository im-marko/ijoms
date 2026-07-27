'use client';

import { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { UserRole } from '@/types';

/**
 * Client-side route guard. Tokens live in localStorage, so authorization
 * can't be checked in middleware — this pairs with the backend's 403s.
 */
export default function RequireRole({
  roles,
  children,
}: {
  roles: UserRole[];
  children: ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const allowed = !!user && roles.includes(user.role);

  useEffect(() => {
    if (!loading && user && !allowed) {
      router.replace('/dashboard');
    }
  }, [loading, user, allowed, router]);

  if (loading || !user || !allowed) return null;
  return <>{children}</>;
}
