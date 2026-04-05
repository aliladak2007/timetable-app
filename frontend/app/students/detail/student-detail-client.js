"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "../../../components/auth-provider";
import { PageHeader } from "../../../components/page-header";
import { TimeWindowEditor } from "../../../components/time-window-editor";
import { WeeklyBoard } from "../../../components/weekly-board";
import {
  deleteStudent,
  downloadAuthorizedFile,
  getCalendarDownloadUrl,
  getStudent,
  replaceStudentBlockedTimes,
  replaceStudentPreferences,
  updateStudent,
} from "../../../lib/api";
import { roleCapabilities } from "../../../lib/roles";

export default function StudentDetailClient({ studentId }) {
  const router = useRouter();
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [student, setStudent] = useState(null);
  const [form, setForm] = useState({
    full_name: "",
    parent_name: "",
    contact_email: "",
    active: true,
    notes: "",
  });
  const [preferences, setPreferences] = useState([]);
  const [blockedTimes, setBlockedTimes] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [calendarUrl, setCalendarUrl] = useState("");

  const loadStudent = async () => {
    if (!studentId) {
      setError("Student id is required.");
      return;
    }

    try {
      const data = await getStudent(studentId);
      setStudent(data);
      setForm({
        full_name: data.full_name,
        parent_name: data.parent_name,
        contact_email: data.contact_email,
        active: data.active,
        notes: data.notes || "",
      });
      setPreferences(data.preferences);
      setBlockedTimes(data.blocked_times);
      setCalendarUrl(await getCalendarDownloadUrl("student", data.id));
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadStudent();
  }, [studentId]);

  const saveProfile = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      await updateStudent(studentId, form);
      setNotice("Student profile updated.");
      await loadStudent();
    } catch (err) {
      setError(err.message);
    }
  };

  const saveConstraints = async () => {
    setError("");
    setNotice("");
    try {
      await replaceStudentPreferences(studentId, preferences);
      await replaceStudentBlockedTimes(studentId, blockedTimes);
      setNotice("Student constraints saved.");
      await loadStudent();
    } catch (err) {
      setError(err.message);
    }
  };

  const removeStudent = async () => {
    if (!window.confirm("Delete this student?")) {
      return;
    }
    try {
      await deleteStudent(studentId);
      router.push("/students");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="stack">
      <PageHeader
        title={student ? student.full_name : "Student"}
        subtitle={caps.canEditStudents ? "Edit profile details, preferred slots, and blocked times." : "Read-only student profile, preferences, and blocked times."}
        actions={
          <div className="header-actions">
            {calendarUrl ? (
              <button className="button secondary" onClick={() => downloadAuthorizedFile(calendarUrl, `student-${studentId}.ics`)}>
                Export calendar
              </button>
            ) : null}
            {caps.canEditStudents ? (
              <button className="button danger" onClick={removeStudent}>
                Delete student
              </button>
            ) : null}
          </div>
        }
      />
      {error ? <div className="alert error">{error}</div> : null}
      {notice ? <div className="alert">{notice}</div> : null}
      <div className="two-column">
        <section className="panel">
          <div className="panel-header">
            <h3>Profile</h3>
          </div>
          {caps.canEditStudents ? (
            <form className="form-grid" onSubmit={saveProfile}>
              <input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
              <input
                value={form.parent_name}
                onChange={(event) => setForm({ ...form, parent_name: event.target.value })}
              />
              <input
                value={form.contact_email}
                onChange={(event) => setForm({ ...form, contact_email: event.target.value })}
              />
              <textarea
                rows="4"
                value={form.notes}
                onChange={(event) => setForm({ ...form, notes: event.target.value })}
              />
              <label>
                <input
                  type="checkbox"
                  checked={form.active}
                  onChange={(event) => setForm({ ...form, active: event.target.checked })}
                />{" "}
                Active
              </label>
              <button type="submit" className="button">
                Save profile
              </button>
            </form>
          ) : (
            <div className="stack">
              <p><strong>{form.full_name}</strong></p>
              <p className="muted">{form.contact_email}</p>
              <p className="muted">Parent: {form.parent_name || "Not provided"}</p>
              <p className="muted">{form.notes || "No notes"}</p>
            </div>
          )}
        </section>
        <div className="stack">
          <WeeklyBoard title="Preferred windows" items={preferences} />
          <WeeklyBoard title="Blocked times" items={blockedTimes} />
        </div>
      </div>
      {caps.canEditStudents ? (
        <>
          <TimeWindowEditor rows={preferences} setRows={setPreferences} label="Edit preferences" withPriority />
          <TimeWindowEditor rows={blockedTimes} setRows={setBlockedTimes} label="Edit blocked times" withReason />
          <div className="inline-actions">
            <button type="button" className="button" onClick={saveConstraints}>
              Save constraints
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}
