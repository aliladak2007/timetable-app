"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "../../components/page-header";
import { useAuth } from "../../components/auth-provider";
import {
  createCalendarFeedToken,
  downloadAuthorizedFile,
  getCalendarDownloadUrl,
  getCalendarFeedUrl,
  getSessionsCsvUrl,
  listStudents,
  listTeachers,
} from "../../lib/api";
import { roleCapabilities } from "../../lib/roles";

export default function ExportsPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [csvUrl, setCsvUrl] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [teacherId, setTeacherId] = useState("");
  const [studentId, setStudentId] = useState("");

  useEffect(() => {
    Promise.all([getSessionsCsvUrl(), listTeachers(), listStudents()])
      .then(([csv, teacherData, studentData]) => {
        setCsvUrl(csv);
        setTeachers(teacherData);
        setStudents(studentData);
        if (teacherData.length) {
          setTeacherId(String(teacherData[0].id));
        }
        if (studentData.length) {
          setStudentId(String(studentData[0].id));
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  const createFeed = async () => {
    setError("");
    setNotice("");
    try {
      const result = await createCalendarFeedToken({
        owner_type: "centre",
        owner_id: null,
        label: "Centre calendar",
      });
      const feedUrl = await getCalendarFeedUrl(result.token);
      setNotice(`Private feed URL created: ${feedUrl}`);
    } catch (err) {
      setError(err.message);
    }
  };

  const teacherCalendar = async () => {
    if (!teacherId) {
      return;
    }
    const url = await getCalendarDownloadUrl("teacher", Number(teacherId));
    await downloadAuthorizedFile(url, `teacher-${teacherId}.ics`);
  };

  const studentCalendar = async () => {
    if (!studentId) {
      return;
    }
    const url = await getCalendarDownloadUrl("student", Number(studentId));
    await downloadAuthorizedFile(url, `student-${studentId}.ics`);
  };

  return (
    <div className="stack">
      <PageHeader
        title="Exports"
        subtitle={
          caps.isAdmin
            ? "Operational exports and calendar delivery tools."
            : "Exports limited to your assigned teacher scope."
        }
      />
      {error ? <div className="alert error">{error}</div> : null}
      {notice ? <div className="alert">{notice}</div> : null}
      <div className="two-column">
        <section className="panel stack">
          <h3>Schedule exports</h3>
          <p className="muted">Download recurring session data for reporting.</p>
          <button
            className="button"
            onClick={() => csvUrl && downloadAuthorizedFile(csvUrl, "sessions.csv")}
            disabled={!csvUrl}
          >
            Download sessions CSV
          </button>
        </section>
        <section className="panel stack">
          <h3>ICS calendar exports</h3>
          <p className="muted">Generate calendar files for manual import into phone and desktop calendar apps.</p>
          {teachers.length === 1 ? (
            <input value={teachers[0].full_name} readOnly />
          ) : (
            <select value={teacherId} onChange={(event) => setTeacherId(event.target.value)}>
              <option value="">Select teacher</option>
              {teachers.map((teacher) => (
                <option key={teacher.id} value={teacher.id}>
                  {teacher.full_name}
                </option>
              ))}
            </select>
          )}
          <button className="button secondary" onClick={teacherCalendar}>
            Download {teachers.length === 1 ? "my" : "teacher"} calendar
          </button>
          <select value={studentId} onChange={(event) => setStudentId(event.target.value)}>
            <option value="">Select student</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.full_name}
              </option>
            ))}
          </select>
          <button className="button secondary" onClick={studentCalendar}>
            Download student calendar
          </button>
          {caps.canCreateCalendarFeed ? (
            <button className="button ghost" onClick={createFeed}>
              Create private centre feed URL
            </button>
          ) : null}
        </section>
      </div>
    </div>
  );
}
