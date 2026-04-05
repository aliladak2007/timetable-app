"use client";

import { useState } from "react";

import { useAuth } from "./auth-provider";

function BootstrapScreen() {
  const { bootstrapUser } = useAuth();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const onSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await bootstrapUser(form);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={onSubmit}>
        <p className="eyebrow">First Run Setup</p>
        <h1>Create the first admin</h1>
        <p className="muted">No default credentials are shipped. This admin account bootstraps the app securely.</p>
        {error ? <div className="alert error">{error}</div> : null}
        <input placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        <input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input
          placeholder="Strong password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <button className="button" disabled={saving}>
          {saving ? "Creating..." : "Create admin"}
        </button>
      </form>
    </div>
  );
}

function LoginScreen() {
  const { loginUser, authError } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const onSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await loginUser(form);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={onSubmit}>
        <p className="eyebrow">Secure Login</p>
        <h1>Timetabling Assistant</h1>
        <p className="muted">Sign in to manage recurring schedules, exceptions, and calendar exports.</p>
        {authError ? <div className="alert error">{authError}</div> : null}
        {error ? <div className="alert error">{error}</div> : null}
        <input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <button className="button" disabled={saving}>
          {saving ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}

export function AuthGate({ children }) {
  const { user, loading, needsBootstrap } = useAuth();

  if (loading) {
    return <div className="auth-screen"><div className="auth-card">Loading secure workspace...</div></div>;
  }

  if (needsBootstrap) {
    return <BootstrapScreen />;
  }

  if (!user) {
    return <LoginScreen />;
  }

  return children;
}
