"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "../components/auth-provider";
import { PageHeader } from "../components/page-header";
import { formatTime, getDashboardSummary, weekdayLabels } from "../lib/api";
import { roleCapabilities } from "../lib/roles";

function formatOccurrence(occurrence) {
  return `${occurrence.effective_date} ${formatTime(occurrence.start_minute)}-${formatTime(occurrence.end_minute)}`;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardSummary().then(setSummary).catch((err) => setError(err.message));
  }, []);

  const title = caps.isAdmin ? "Admin Dashboard" : "My Dashboard";
  const subtitle = caps.isAdmin
    ? "Governance and operations view across schedule quality, user load, and upcoming risk."
    : caps.isScheduler
      ? "Your teaching load, upcoming lessons, and schedule issues within your assigned scope."
      : "Your read-only timetable view with upcoming activity and schedule alerts.";

  return (
    <div className="stack">
      <PageHeader
        title={title}
        subtitle={subtitle}
        actions={
          <div className="header-actions">
            {caps.canCreateStudents ? (
              <Link href="/students/new" className="button">
                Add new student
              </Link>
            ) : null}
            {caps.canManageOps ? (
              <Link href="/ops" className="button secondary">
                Manage exceptions
              </Link>
            ) : null}
            {!caps.canManageOps ? (
              <Link href="/sessions" className="button secondary">
                View sessions
              </Link>
            ) : null}
          </div>
        }
      />
      {error ? <div className="alert error">{error}</div> : null}
      <section className="stats-grid">
        {caps.isAdmin ? (
          <div className="stat-card">
            <p className="eyebrow">Teachers</p>
            <strong>{summary?.teacher_count ?? "-"}</strong>
            <p className="muted">Active tutor profiles</p>
          </div>
        ) : null}
        <div className="stat-card">
          <p className="eyebrow">{caps.isAdmin ? "Students" : "My Students"}</p>
          <strong>{summary?.student_count ?? "-"}</strong>
          <p className="muted">{caps.isAdmin ? "Students on file" : "Students currently linked to your sessions"}</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">{caps.isAdmin ? "Recurring Sessions" : "My Sessions"}</p>
          <strong>{summary?.recurring_session_count ?? "-"}</strong>
          <p className="muted">{caps.isAdmin ? "Base weekly schedule templates" : "Recurring templates assigned to you"}</p>
        </div>
        {!caps.isAdmin ? (
          <div className="stat-card">
            <p className="eyebrow">Next 7 Days</p>
            <strong>{summary?.upcoming_occurrences?.length ?? 0}</strong>
            <p className="muted">Upcoming scheduled or rescheduled lessons</p>
          </div>
        ) : null}
      </section>
      <section className="two-column">
        <div className="panel">
          <div className="panel-header">
            <h3>Upcoming sessions</h3>
          </div>
          <div className="stack">
            {(summary?.upcoming_occurrences || []).map((occurrence) => (
              <div key={`${occurrence.session_id}-${occurrence.occurrence_date}`} className="list-card">
                <strong>{occurrence.subject || "Lesson"}</strong>
                <p className="muted">{formatOccurrence(occurrence)}</p>
                <p className="muted">{weekdayLabels[occurrence.weekday]}</p>
              </div>
            ))}
            {!summary?.upcoming_occurrences?.length ? <p className="muted">No upcoming sessions found.</p> : null}
          </div>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h3>{caps.isViewer ? "Alerts" : "Conflict watchlist"}</h3>
          </div>
          <div className="stack">
            {(summary?.conflict_occurrences || []).map((occurrence) => (
              <div key={`${occurrence.session_id}-${occurrence.occurrence_date}-conflict`} className="list-card">
                <strong>{occurrence.subject || "Lesson"}</strong>
                <p className="muted">{formatOccurrence(occurrence)}</p>
                <p className="muted">{occurrence.impact_reasons.join(" | ")}</p>
              </div>
            ))}
            {!summary?.conflict_occurrences?.length ? <p className="muted">No upcoming conflicts detected.</p> : null}
          </div>
        </div>
      </section>
      {caps.isAdmin ? (
        <section className="two-column">
          <div className="panel">
            <div className="panel-header">
              <h3>{caps.isScheduler ? "Unassigned students queue" : "Unassigned students"}</h3>
            </div>
            <div className="stack">
              {(summary?.unassigned_students || []).map((student) => (
                <div key={student.id} className="list-card">
                  <strong>{student.full_name}</strong>
                  <Link href={`/students/detail?id=${student.id}`} className="button ghost">
                    Open student
                  </Link>
                </div>
              ))}
              {!summary?.unassigned_students?.length ? <p className="muted">All active students have recurring sessions.</p> : null}
            </div>
          </div>
          <div className="panel">
            <div className="panel-header">
              <h3>Upcoming closures</h3>
            </div>
            <div className="stack">
              {(summary?.closures || []).map((closure) => (
                <div key={closure.id} className="list-card">
                  <strong>{closure.name}</strong>
                  <p className="muted">
                    {closure.start_date} to {closure.end_date}
                  </p>
                </div>
              ))}
              {!summary?.closures?.length ? <p className="muted">No future holidays or closures recorded.</p> : null}
            </div>
          </div>
        </section>
      ) : null}
    </div>
  );
}
