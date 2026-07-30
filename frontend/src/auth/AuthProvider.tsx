import { createContext, useEffect, useState, type ReactNode } from "react";

import * as authApi from "@/api/auth";
import { registerAuthFailureHandler, setAccessToken } from "@/auth/tokenStore";
import type { User } from "@/types/user";

interface AuthContextValue {
  user: User | null;
  isBootstrapping: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    registerAuthFailureHandler(() => {
      setAccessToken(null);
      setUser(null);
    });

    // Re-establish a session from the httpOnly refresh cookie on page load.
    (async () => {
      try {
        const response = await authApi.refresh();
        setAccessToken(response.access_token);
        const me = await authApi.getMe();
        setUser(me);
      } catch {
        setAccessToken(null);
        setUser(null);
      } finally {
        setIsBootstrapping(false);
      }
    })();
  }, []);

  async function login(username: string, password: string): Promise<void> {
    const response = await authApi.login(username, password);
    setAccessToken(response.access_token);
    const me = await authApi.getMe();
    setUser(me);
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }

  return (
    <AuthContext.Provider value={{ user, isBootstrapping, login, logout }}>{children}</AuthContext.Provider>
  );
}
