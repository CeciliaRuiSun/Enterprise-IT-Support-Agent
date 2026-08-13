"use client";

import Link from "next/link";

import { useAuth } from "@/components/auth-provider";

export function AuthControls() {
  const { account, isAuthenticated, login, logout } = useAuth();

  if (!isAuthenticated) {
    return (
      <button
        type="button"
        onClick={() => void login()}
        className="rounded-xl border border-teal-400/30 bg-teal-400/10 px-4 py-2 text-sm font-semibold text-teal-200 transition hover:bg-teal-400/20"
      >
        Sign in with Microsoft
      </button>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="text-right">
        <div className="text-xs uppercase tracking-[0.16em] text-slate-500">Signed in</div>
        <div className="max-w-[220px] truncate text-sm text-slate-200">{account?.name ?? account?.username}</div>
      </div>
      <Link
        href="/me-test"
        className="rounded-xl border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:bg-white/10"
      >
        Test /me
      </Link>
      <button
        type="button"
        onClick={() => void logout()}
        className="rounded-xl border border-white/10 px-3 py-2 text-xs text-slate-300 transition hover:bg-white/10"
      >
        Sign out
      </button>
    </div>
  );
}
