"use client";

import { createContext, useContext, useEffect, useRef, useState } from "react";

import {
  bootstrapAdmin,
  clearStoredToken,
  getBootstrapStatus,
  getCurrentUser,
  hasStoredToken,
  login,
  shouldHydrateCurrentUser,
  storeToken,
} from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [needsBootstrap, setNeedsBootstrap] = useState(false);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const loadingRef = useRef(false);

  const loadState = async () => {
    if (loadingRef.current) {
      return;
    }
    loadingRef.current = true;
    setLoading(true);
    setAuthError("");
    try {
      const bootstrap = await getBootstrapStatus();
      setNeedsBootstrap(bootstrap.needs_bootstrap);
      if (shouldHydrateCurrentUser({ needsBootstrap: bootstrap.needs_bootstrap, token: hasStoredToken() })) {
        setUser(await getCurrentUser());
      } else {
        setUser(null);
      }
    } catch (err) {
      clearStoredToken();
      setUser(null);
      if (err?.status === 403) {
        setAuthError(err.message);
      }
      if (process.env.NODE_ENV !== "production") {
        console.error("Auth hydration failed", err);
      }
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  };

  useEffect(() => {
    loadState();
    const handleLogout = () => {
      clearStoredToken();
      setUser(null);
      setAuthError("");
      setLoading(false);
    };
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, []);

  const loginUser = async (payload) => {
    setAuthError("");
    const result = await login(payload);
    storeToken(result.access_token);
    setNeedsBootstrap(false);
    setUser(result.user);
    return result.user;
  };

  const bootstrapUser = async (payload) => {
    setAuthError("");
    await bootstrapAdmin(payload);
    setNeedsBootstrap(false);
    await loginUser({ email: payload.email, password: payload.password });
  };

  const logout = () => {
    clearStoredToken();
    setUser(null);
    setAuthError("");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        needsBootstrap,
        authError,
        loginUser,
        bootstrapUser,
        logout,
        refreshUser: loadState,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
