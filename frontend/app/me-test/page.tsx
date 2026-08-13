"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { getMe } from "@/lib/api";

export default function MeTestPage() {
  const { account, isAuthenticated } = useAuth();
  const [response, setResponse] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const requestStarted = useRef(false);

  const loadMe = useCallback(async () => {
    setError(null);
    try {
      setResponse(await getMe());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load /me.");
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      requestStarted.current = false;
      return;
    }
    if (requestStarted.current) return;
    requestStarted.current = true;

    void loadMe();
  }, [isAuthenticated, loadMe]);

  return (
    <main className="mx-auto min-h-dvh w-full max-w-3xl px-6 py-10">
      <Link href="/" className="text-sm text-teal-300 hover:text-teal-200">← Back to support agent</Link>
      <div className="mt-8 rounded-3xl border border-white/10 bg-ink-900/80 p-6 shadow-glow">
        <div className="text-xs uppercase tracking-[0.28em] text-teal-400">Authenticated test page</div>
        <h1 className="mt-2 text-2xl font-semibold text-white">FastAPI /me response</h1>
        {!isAuthenticated ? (
          <p className="mt-4 text-sm text-slate-300">Sign in from the home page before testing the authenticated request.</p>
        ) : error ? (
          <div className="mt-4 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-200">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => void loadMe()}
              className="mt-3 rounded-lg border border-red-200/30 px-3 py-1.5 text-xs text-red-100 hover:bg-red-200/10"
            >
              Retry
            </button>
          </div>
        ) : (
          <pre className="mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-200">
            {JSON.stringify(response ?? { loading: true, account: account?.username }, null, 2)}
          </pre>
        )}
      </div>
    </main>
  );
}
