"use client";

import {
  AccountInfo,
  InteractionRequiredAuthError,
  PublicClientApplication,
  type IPublicClientApplication
} from "@azure/msal-browser";
import { MsalProvider, useMsal } from "@azure/msal-react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { registerAccessTokenProvider } from "@/lib/api";
import { entraConfigError, loginRequest, msalConfig } from "@/lib/auth-config";

type AuthContextValue = {
  account: AccountInfo | null;
  isAuthenticated: boolean;
  isReady: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: (forceRefresh?: boolean) => Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function EntraAuthProvider({ children }: { children: React.ReactNode }) {
  const [instance, setInstance] = useState<IPublicClientApplication | null>(null);
  const [initializationError, setInitializationError] = useState<string | null>(null);

  useEffect(() => {
    if (entraConfigError.length) return;

    let cancelled = false;
    const client = new PublicClientApplication(msalConfig);

    void (async () => {
      try {
        await client.initialize();
        const redirectResult = await client.handleRedirectPromise();
        if (redirectResult?.account) {
          client.setActiveAccount(redirectResult.account);
        } else if (!client.getActiveAccount()) {
          const existingAccount = client.getAllAccounts()[0];
          if (existingAccount) client.setActiveAccount(existingAccount);
        }
        if (!cancelled) setInstance(client);
      } catch (error) {
        if (!cancelled) {
          setInitializationError(error instanceof Error ? error.message : "Unable to initialize Microsoft sign-in.");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  if (entraConfigError.length) {
    return (
      <div className="flex min-h-dvh items-center justify-center px-6 text-center text-sm text-slate-300">
        Configure {entraConfigError.join(", ")} in frontend/.env before using Microsoft sign-in.
      </div>
    );
  }

  if (initializationError) {
    return <div className="flex min-h-dvh items-center justify-center px-6 text-sm text-red-200">{initializationError}</div>;
  }

  if (!instance) {
    return <div className="flex min-h-dvh items-center justify-center px-6 text-sm text-slate-300">Loading Microsoft sign-in...</div>;
  }

  return (
    <MsalProvider instance={instance}>
      <AuthenticatedSession instance={instance}>{children}</AuthenticatedSession>
    </MsalProvider>
  );
}

function AuthenticatedSession({
  instance,
  children
}: {
  instance: IPublicClientApplication;
  children: React.ReactNode;
}) {
  const { accounts } = useMsal();
  const [account, setAccount] = useState<AccountInfo | null>(instance.getActiveAccount() ?? accounts[0] ?? null);

  useEffect(() => {
    const nextAccount = instance.getActiveAccount() ?? accounts[0] ?? null;
    if (nextAccount && !instance.getActiveAccount()) instance.setActiveAccount(nextAccount);
    setAccount(nextAccount);
  }, [accounts, instance]);

  const getAccessToken = async (forceRefresh = false) => {
    const activeAccount = instance.getActiveAccount() ?? accounts[0] ?? null;
    if (!activeAccount) return null;

    try {
      const result = await instance.acquireTokenSilent({
        ...loginRequest,
        account: activeAccount,
        forceRefresh
      });
      return result.accessToken;
    } catch (error) {
      if (!(error instanceof InteractionRequiredAuthError)) throw error;
      const result = await instance.acquireTokenPopup(loginRequest);
      if (result.account) instance.setActiveAccount(result.account);
      return result.accessToken;
    }
  };

  useEffect(() => registerAccessTokenProvider(getAccessToken), [accounts, instance]);

  const value = useMemo<AuthContextValue>(
    () => ({
      account,
      isAuthenticated: Boolean(account),
      isReady: true,
      getAccessToken,
      login: async () => {
        await instance.loginRedirect(loginRequest);
      },
      logout: async () => {
        await instance.logoutRedirect({ account: instance.getActiveAccount() ?? undefined });
      }
    }),
    [account, accounts, instance]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside EntraAuthProvider");
  return context;
}
