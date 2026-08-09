'use client';

import { useCallback, useEffect, useRef } from 'react';
import Script from 'next/script';

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

export default function GoogleSignInButton({
  onCredential,
  text = 'signin_with',
}: {
  onCredential: (credential: string) => void;
  text?: 'signin_with' | 'signup_with' | 'continue_with';
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onCredentialRef = useRef(onCredential);

  useEffect(() => {
    onCredentialRef.current = onCredential;
  }, [onCredential]);

  const renderGoogleButton = useCallback(() => {
    if (!window.google || !containerRef.current || !CLIENT_ID) return;
    window.google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: (response) => onCredentialRef.current(response.credential),
    });
    containerRef.current.innerHTML = '';
    window.google.accounts.id.renderButton(containerRef.current, {
      theme: 'outline',
      size: 'large',
      width: 320,
      text,
    });
  }, [text]);

  // Handles remounts where the GIS script is already loaded (onReady does not
  // re-fire for cached scripts on every navigation in all cases).
  useEffect(() => {
    renderGoogleButton();
  }, [renderGoogleButton]);

  if (!CLIENT_ID) return null;

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onReady={renderGoogleButton}
      />
      <div ref={containerRef} className="flex justify-center" />
    </>
  );
}
