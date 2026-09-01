"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { User, Company } from "@/types";
import { apiFetch, getApiUrl } from "@/lib/api";
import { useRouter } from "next/navigation";

interface AuthContextType {
  user: User | null;
  company: Company | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (name: string, email: string, pass: string, phone?: string, compName?: string) => Promise<void>;
  logout: () => void;
  updateUser: (updated: Partial<User>) => void;
  refreshCompany: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const savedToken = localStorage.getItem("converza_token");
    if (savedToken) {
      setToken(savedToken);
      fetchMe(savedToken);
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchMe = async (authToken: string) => {
    try {
      const userData = await apiFetch<User>("/auth/me", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setUser(userData);
      const companyData = await apiFetch<Company>("/company", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setCompany(companyData);
    } catch {
      localStorage.removeItem("converza_token");
      setToken(null);
      setUser(null);
      setCompany(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = useCallback(async (email: string, pass: string) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", pass);

    const baseUrl = getApiUrl();
    const res = await fetch(`${baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Falha ao realizar login.");
    }

    const data = await res.json();
    localStorage.setItem("converza_token", data.access_token);
    setToken(data.access_token);
    setUser(data.user);

    const comp = await apiFetch<Company>("/company", {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    setCompany(comp);

    if (!data.user.onboarding_completed) {
      router.push("/onboarding");
    } else {
      router.push("/dashboard");
    }
  }, [router]);

  const register = useCallback(async (
    name: string,
    email: string,
    pass: string,
    phone?: string,
    compName?: string
  ) => {
    const data = await apiFetch<{ access_token: string; user: User }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        name,
        email,
        password: pass,
        phone,
        company_name: compName,
      }),
    });

    localStorage.setItem("converza_token", data.access_token);
    setToken(data.access_token);
    setUser(data.user);

    const comp = await apiFetch<Company>("/company", {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    setCompany(comp);

    router.push("/onboarding");
  }, [router]);

  const logout = useCallback(() => {
    localStorage.removeItem("converza_token");
    setToken(null);
    setUser(null);
    setCompany(null);
    router.push("/login");
  }, [router]);

  const updateUser = useCallback((updated: Partial<User>) => {
    setUser((prev) => prev ? { ...prev, ...updated } : null);
  }, []);

  const refreshCompany = useCallback(async () => {
    try {
      const c = await apiFetch<Company>("/company");
      setCompany(c);
    } catch {
      // ignore
    }
  }, []);

  const value = useMemo(() => ({
    user,
    company,
    token,
    isLoading,
    login,
    register,
    logout,
    updateUser,
    refreshCompany,
  }), [user, company, token, isLoading, login, register, logout, updateUser, refreshCompany]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
