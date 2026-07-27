'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <AlertTriangle className="h-12 w-12 text-red-500" />
      <h2 className="mt-4 text-lg font-semibold text-gray-900">Something went wrong</h2>
      <p className="mt-1 text-sm text-gray-500">{error.message || 'An unexpected error occurred.'}</p>
      <Button className="mt-6" onClick={() => unstable_retry()}>Try again</Button>
    </div>
  );
}
