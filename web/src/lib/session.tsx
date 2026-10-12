"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { ApiError, request } from "@/lib/api";
import type { Me } from "@/lib/types";

type SessionState =
  | { status: "loading"; user: null }
  | { status: "signed_out"; user: null }
  | { status: "signed_in"; user: Me };

type SessionContextValue = SessionState & {
  refresh: () => Promise<void>;
  setUser: (user: Me | null) => void;
  signOut: () => Promise<void>;
};

const SIGNED_OUT: SessionState = { status: "signed_out", user: null };

/** The current session, or null when the API couldn't be reached. */
async function loadSession(): Promise<SessionState | null> {
  try {
    return { status: "signed_in", user: await request<Me>("/me") };
  } catch (error) {
    return error instanceof ApiError && error.status === 401 ? SIGNED_OUT : null;
  }
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({ status: "loading", user: null });

  const setUser = useCallback((user: Me | null) => {
    setState(user ? { status: "signed_in", user } : SIGNED_OUT);
  }, []);

  const refresh = useCallback(async () => {
    const next = await loadSession();
    // Keep a known user on a network blip; a first load that fails counts as signed out.
    setState((current) => next ?? (current.status === "loading" ? SIGNED_OUT : current));
  }, []);

  const signOut = useCallback(async () => {
    await request("/auth/logout", { method: "POST" });
    setUser(null);
  }, [setUser]);

  useEffect(() => {
    let active = true;
    void loadSession().then((next) => {
      if (active) setState(next ?? SIGNED_OUT);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <SessionContext.Provider value={{ ...state, refresh, setUser, signOut }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside <SessionProvider>");
  return value;
}
