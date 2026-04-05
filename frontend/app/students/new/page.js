"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AccessDenied } from "../../../components/access-denied";
import { useAuth } from "../../../components/auth-provider";
import { PageHeader } from "../../../components/page-header";
import { TimeWindowEditor } from "../../../components/time-window-editor";
import { listTeachers } from "../../../lib/api";
import { roleCapabilities } from "../../../lib/roles";

const initialStudent = {
  full_name: "",
  parent_name: "",
  contact_email: "",
  notes: "",
  teacher_id: "",
  duration_minutes: 60,
  subject: "",
};

export default function NewStudentWizardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [teachers, setTeachers] = useState([]);
  const [student, setStudent] = useState(initialStudent);
  const [preferences, setPreferences] = useState([{ weekday: 0, start_minute: 900, end_minute: 960, priority: 1 }]);
  const [blockedTimes, setBlockedTimes] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!caps.canCreateStudents) {
      return;
    }
    listTeachers()
      .then((teacherData) => {
        setTeachers(teacherData);
        if (teacherData.length === 1) {
          setStudent((current) => ({ ...current, teacher_id: teacherData[0].id }));
        }
      })
      .catch((err) => setError(err.message));
  }, [caps.canCreateStudents]);

  const startMatching = () => {
    setError("");
    if (!student.full_name || !student.contact_email || !student.teacher_id) {
      setError("Student name, contact email, and selected teacher are required.");
      return;
    }
    if (!preferences.length) {
      setError("Add at least one preferred time window.");
      return;
    }

    window.sessionStorage.setItem(
      "pendingStudentDraft",
      JSON.stringify({
        student,
        preferences,
        blockedTimes,
      }),
    );
    router.push("/matches");
  };

  if (!caps.canCreateStudents) {
    return (
      <AccessDenied
        title="Viewer mode: read-only"
        description="Only admin and scheduling users can create students and start matching workflows."
      />
    );
  }

  return (
    <div className="stack">
      <PageHeader
        title="Add New Student"
        subtitle="Capture profile details, preferred windows, and blocked times before running slot matching."
      />
      {error ? <div className="alert error">{error}</div> : null}
      <div className="two-column">
        <section className="panel">
          <div className="panel-header">
            <h3>Student profile</h3>
          </div>
          <div className="form-grid">
            <input
              placeholder="Student full name"
              value={student.full_name}
              onChange={(event) => setStudent({ ...student, full_name: event.target.value })}
            />
            <input
              placeholder="Parent name"
              value={student.parent_name}
              onChange={(event) => setStudent({ ...student, parent_name: event.target.value })}
            />
            <input
              type="email"
              placeholder="Contact email"
              value={student.contact_email}
              onChange={(event) => setStudent({ ...student, contact_email: event.target.value })}
            />
            {teachers.length === 1 ? (
              <input value={teachers[0].full_name} readOnly />
            ) : (
              <select
                value={student.teacher_id}
                onChange={(event) => setStudent({ ...student, teacher_id: Number(event.target.value) })}
              >
                <option value="">Select teacher</option>
                {teachers.map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.full_name}
                  </option>
                ))}
              </select>
            )}
            <input
              type="number"
              min="30"
              step="15"
              value={student.duration_minutes}
              onChange={(event) => setStudent({ ...student, duration_minutes: Number(event.target.value) })}
            />
            <input
              placeholder="Subject"
              value={student.subject}
              onChange={(event) => setStudent({ ...student, subject: event.target.value })}
            />
            <textarea
              rows="4"
              placeholder="Notes"
              value={student.notes}
              onChange={(event) => setStudent({ ...student, notes: event.target.value })}
            />
          </div>
        </section>
        <section className="panel">
          <div className="panel-header">
            <h3>Wizard output</h3>
          </div>
          <p className="muted">
            This flow uses the backend matching endpoint with the draft preferences and blocked times below, then lets
            you confirm one slot and create the recurring booking.
          </p>
          <button type="button" className="button" onClick={startMatching}>
            Find matching slots
          </button>
        </section>
      </div>
      <TimeWindowEditor rows={preferences} setRows={setPreferences} label="Preferred time windows" withPriority />
      <TimeWindowEditor rows={blockedTimes} setRows={setBlockedTimes} label="Blocked times" withReason />
    </div>
  );
}
