"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AccessDenied } from "../../../components/access-denied";
import { useAuth } from "../../../components/auth-provider";
import { PageHeader } from "../../../components/page-header";
import {
  createSession,
  createStudent,
  formatWindow,
  replaceStudentBlockedTimes,
  replaceStudentPreferences,
} from "../../../lib/api";
import { roleCapabilities } from "../../../lib/roles";

export default function ConfirmBookingPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [draft, setDraft] = useState(null);
  const [choice, setChoice] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!caps.canUseMatching) {
      return;
    }
    const rawDraft = window.sessionStorage.getItem("pendingStudentDraft");
    const rawChoice = window.sessionStorage.getItem("pendingBookingChoice");
    if (rawDraft) {
      setDraft(JSON.parse(rawDraft));
    }
    if (rawChoice) {
      setChoice(JSON.parse(rawChoice));
    }
  }, [caps.canUseMatching]);

  const confirmBooking = async () => {
    if (!draft || !choice) {
      return;
    }
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const student = await createStudent({
        full_name: draft.student.full_name,
        parent_name: draft.student.parent_name,
        contact_email: draft.student.contact_email,
        notes: draft.student.notes,
        active: true,
      });

      await createSession({
        teacher_id: draft.student.teacher_id,
        student_id: student.id,
        weekday: choice.weekday,
        start_minute: choice.start_minute,
        end_minute: choice.end_minute,
        duration_minutes: draft.student.duration_minutes,
        subject: draft.student.subject,
        status: "active",
        start_date: new Date().toISOString().slice(0, 10),
      });
      await replaceStudentPreferences(student.id, draft.preferences);
      await replaceStudentBlockedTimes(student.id, draft.blockedTimes);

      window.sessionStorage.removeItem("pendingStudentDraft");
      window.sessionStorage.removeItem("pendingBookingChoice");
      setSuccess("Student created and recurring booking confirmed.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!caps.canUseMatching) {
    return (
      <AccessDenied
        title="Viewer mode: read-only"
        description="Booking confirmation is available only for admin and staff scheduler roles."
      />
    );
  }

  if (!draft || !choice) {
    return (
      <div className="stack">
        <PageHeader title="Confirm Booking" subtitle="No pending booking was found." />
        <div className="alert">Return to the new-student flow and choose a match first.</div>
      </div>
    );
  }

  return (
    <div className="stack">
      <PageHeader title="Confirm Booking" subtitle="Final review before creating the student and recurring session." />
      {error ? <div className="alert error">{error}</div> : null}
      {success ? (
        <div className="alert">
          {success} <Link href="/sessions">Open sessions</Link>
        </div>
      ) : null}
      <section className="two-column">
        <div className="panel">
          <div className="panel-header">
            <h3>Student details</h3>
          </div>
          <p><strong>{draft.student.full_name}</strong></p>
          <p className="muted">{draft.student.contact_email}</p>
          <p className="muted">Parent: {draft.student.parent_name || "Not provided"}</p>
          <p className="muted">Subject: {draft.student.subject || "Not set"}</p>
        </div>
        <div className="panel">
          <div className="panel-header">
            <h3>Chosen slot</h3>
          </div>
          <p><strong>{formatWindow(choice)}</strong></p>
          <div className="tag-list">
            {choice.reasons.map((reason) => (
              <span key={reason} className="tag">
                {reason}
              </span>
            ))}
          </div>
        </div>
      </section>
      <div className="button-row">
        <button className="button" onClick={confirmBooking} disabled={saving || Boolean(success)}>
          {saving ? "Confirming..." : "Create student and booking"}
        </button>
        <Link href="/matches" className="button secondary">
          Back to matches
        </Link>
      </div>
    </div>
  );
}
