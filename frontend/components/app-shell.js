"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./auth-provider";
import { navForRole, roleLabels } from "../lib/roles";

export function AppShell({ children }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const links = navForRole(user);

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Timetabling</p>
          <h1>{roleLabels[user?.role] || "Workspace"}</h1>
          <p className="muted">{user?.full_name}</p>
          <p className="muted">{roleLabels[user?.role] || user?.role}</p>
        </div>
        <nav className="nav-list">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={pathname === link.href ? "nav-link active" : "nav-link"}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <button className="button ghost sidebar-logout" onClick={logout}>
          Sign out
        </button>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
