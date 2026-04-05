"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "../../../components/auth-provider";
import { PageHeader } from "../../../components/page-header";
import { TimeWindowEditor } from "../../../components/time-window-editor";
import { WeeklyBoard } from "../../../components/weekly-board";
import {
  deleteTeacher,
  downloadAuthorizedFile,
  getCalendarDownloadUrl,
  getTeacher,
  replaceTeacherAvailability,
  updateTeacher,
} from "../../../lib/api";
import { roleCapabilities } from "../../../lib/roles";

export default function TeacherDetailClient({ teacherId }) {
  const router = useRouter();
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [teacher, setTeacher] = useState(null);
  const [form, setForm] = useState({ full_name: "", email: "", subject_tags: "", active: true });
  const [availability, setAvailability] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [calendarUrl, setCalendarUrl] = useState("");

  const loadTeacher = async () => {
    if (!teacherId) {
      setError("Teacher id is required.");
      return;
    }

    try {
      const data = await getTeacher(teacherId);
      setTeacher(data);
      setForm({
        full_name: data.full_name,
        email: data.email,
        subject_tags: data.subject_tags,
        active: data.active,
      });
      setAvailability(data.availability_slots);
      setCalendarUrl(await getCalendarDownloadUrl("teacher", data.id));
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadTeacher();
  }, [teacherId]);

  const saveProfile = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      await updateTeacher(teacherId, form);
      setNotice("Teacher profile updated.");
      await loadTeacher();
    } catch (err) {
      setError(err.message);
    }
  };

  const saveAvailability = async () => {
    setError("");
    setNotice("");
    try {
      await replaceTeacherAvailability(teacherId, availability);
      setNotice("Availability saved.");
      await loadTeacher();
    } catch (err) {
      setError(err.message);
    }
  };

  const removeTeacher = async () => {
    if (!window.confirm("Delete this teacher?")) {
      return;
    }
    try {
      await deleteTeacher(teacherId);
      router.push("/teachers");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="stack">
      <PageHeader
        title={teacher ? teacher.full_name : "Teacher"}
        subtitle={caps.canEditTeachers ? "Profile editing and weekly availability management." : "Read-only teacher profile and weekly availability."}
        actions={
          <div className="header-actions">
            {calendarUrl ? (
              <button className="button secondary" onClick={() => downloadAuthorizedFile(calendarUrl, `teacher-${teacherId}.ics`)}>
                Export calendar
              </button>
            ) : null}
            {caps.canEditTeachers ? (
              <button className="button danger" onClick={removeTeacher}>
                Delete teacher
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
          {caps.canEditTeachers ? (
            <form className="form-grid" onSubmit={saveProfile}>
              <input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
              <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
              <input
                value={form.subject_tags}
                onChange={(event) => setForm({ ...form, subject_tags: event.target.value })}
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
              <p className="muted">{form.email}</p>
              <p className="muted">{form.subject_tags}</p>
              <p className="muted">{form.active ? "Active" : "Inactive"}</p>
            </div>
          )}
        </section>
        <WeeklyBoard title="Current availability" items={availability} />
      </div>
      {caps.canEditTeachers ? (
        <>
          <TimeWindowEditor rows={availability} setRows={setAvailability} label="Edit weekly availability" />
          <div className="inline-actions">
            <button type="button" className="button" onClick={saveAvailability}>
              Save availability
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}
