"use client";

import Link from "next/link";

export function AccessDenied({ title = "Access restricted", description = "You do not have permission to access this area." }) {
  return (
    <div className="stack">
      <div className="panel">
        <h2>{title}</h2>
        <p className="muted">{description}</p>
        <Link href="/" className="button">
          Return to dashboard
        </Link>
      </div>
    </div>
  );
}
