"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../../components/auth-provider";
import { PageHeader } from "../../components/page-header";
import { WeeklyBoard } from "../../components/weekly-board";
import {
  createCalendarFeedToken,
  deleteOccurrenceException,
  downloadAuthorizedFile,
  formatTime,
  getCalendarFeedUrl,
  getSessionsCsvUrl,
  listSessions,
  listStudents,
  listTeachers,
  queryOccurrences,
  saveOccurrenceException,
  weekdayLabels,
} from "../../lib/api";
import { roleCapabilities } from "../../lib/roles";

const today = new Date().toISOString().slice(0, 10);
const twoWeeksFromToday = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

export default function SessionsPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [sessions, setSessions] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [occurrences, setOccurrences] = useState([]);
  const [csvUrl, setCsvUrl] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadAll = async () => {
    try {
      const [sessionData, teacherData, studentData, occurrenceData] = await Promise.all([
        listSessions(),
        listTeachers(),
        listStudents(),
        queryOccurrences({ date_from: today, date_to: twoWeeksFromToday }),
      ]);
      setSessions(sessionData);
      setTeachers(teacherData);
      setStudents(studentData);
      setOccurrences(occurrenceData);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadAll();
    getSessionsCsvUrl().then(setCsvUrl).catch(() => {});
  }, []);

  const teacherMap = useMemo(() => Object.fromEntries(teachers.map((item) => [item.id, item.full_name])), [teachers]);
  const studentMap = useMemo(() => Object.fromEntries(students.map((item) => [item.id, item.full_name])), [students]);

  const weeklyItems = sessions.map((session) => ({
    ...session,
    subject: `${teacherMap[session.teacher_id] || "Teacher"} / ${studentMap[session.student_id] || "Student"}`,
  }));

  const markOccurrence = async (occurrence, status) => {
    setError("");
    setNotice("");
    try {
      await saveOccurrenceException(occurrence.session_id, {
        occurrence_date: occurrence.occurrence_date,
        status,
        notes: "",
      });
      setNotice(`Occurrence marked as ${status}.`);
      await loadAll();
    } catch (err) {
      setError(err.message);
    }
  };

  const rescheduleOccurrence = async (occurrence) => {
    const rescheduledDate = window.prompt("Reschedule to date (YYYY-MM-DD)", occurrence.occurrence_date);
    if (!rescheduledDate) {
      return;
    }
    const startTime = window.prompt("New start time (HH:MM)", formatTime(occurrence.start_minute));
    const endTime = window.prompt("New end time (HH:MM)", formatTime(occurrence.end_minute));
    if (!startTime || !endTime) {
      return;
    }

    const [startHour, startMinute] = startTime.split(":").map(Number);
    const [endHour, endMinute] = endTime.split(":").map(Number);
    try {
      await saveOccurrenceException(occurrence.session_id, {
        occurrence_date: occurrence.occurrence_date,
        status: "rescheduled",
        rescheduled_date: rescheduledDate,
        rescheduled_start_minute: startHour * 60 + startMinute,
        rescheduled_end_minute: endHour * 60 + endMinute,
        notes: "",
      });
      setNotice("Occurrence rescheduled.");
      await loadAll();
    } catch (err) {
      setError(err.message);
    }
  };

  const createFeed = async () => {
    try {
      const result = await createCalendarFeedToken({ owner_type: "centre", owner_id: null, label: "Centre calendar" });
      const feedUrl = await getCalendarFeedUrl(result.token);
      setNotice(`Private calendar feed created: ${feedUrl}`);
    } catch (err) {
      setError(err.message);
    }
  };

  const resetOccurrence = async (occurrence) => {
    try {
      await deleteOccurrenceException(occurrence.session_id, occurrence.occurrence_date);
      setNotice("Occurrence override removed.");
      await loadAll();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="stack">
      <PageHeader
        title="Sessions"
        subtitle={caps.canManageSessions ? "Recurring templates, next-two-weeks occurrences, and operational controls." : "Read-only recurring schedule and upcoming occurrences."}
        actions={
          <div className="header-actions">
            {caps.canExportCsv ? (
              <button
                className="button secondary"
                onClick={() => csvUrl && downloadAuthorizedFile(csvUrl, "sessions.csv")}
                disabled={!csvUrl}
              >
                Export CSV
              </button>
            ) : null}
            {caps.canCreateCalendarFeed ? (
              <button className="button ghost" onClick={createFeed}>
                Create centre calendar feed
              </button>
            ) : null}
          </div>
        }
      />
      {error ? <div className="alert error">{error}</div> : null}
      {notice ? <div className="alert">{notice}</div> : null}
      <WeeklyBoard title="Weekly recurring schedule" items={weeklyItems} emptyLabel="Free" />
      <section className="panel">
        <div className="panel-header">
          <h3>Next 14 days</h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Teacher</th>
                <th>Student</th>
                <th>Time</th>
                <th>Status</th>
                <th>Why flagged</th>
                {caps.canManageSessions ? <th>Actions</th> : null}
              </tr>
            </thead>
            <tbody>
              {occurrences.map((occurrence) => (
                <tr key={`${occurrence.session_id}-${occurrence.occurrence_date}`}>
                  <td>{occurrence.effective_date}</td>
                  <td>{teacherMap[occurrence.teacher_id]}</td>
                  <td>{studentMap[occurrence.student_id]}</td>
                  <td>
                    {weekdayLabels[occurrence.weekday]} {formatTime(occurrence.start_minute)}-{formatTime(occurrence.end_minute)}
                  </td>
                  <td>{occurrence.occurrence_status}</td>
                  <td>{occurrence.impact_reasons.join(" | ") || "-"}</td>
                  {caps.canManageSessions ? (
                    <td>
                      <div className="inline-actions">
                        <button className="button ghost" onClick={() => markOccurrence(occurrence, "cancelled")}>
                          Cancel
                        </button>
                        <button className="button ghost" onClick={() => markOccurrence(occurrence, "completed")}>
                          Complete
                        </button>
                        <button className="button ghost" onClick={() => markOccurrence(occurrence, "missed")}>
                          Missed
                        </button>
                        <button className="button ghost" onClick={() => rescheduleOccurrence(occurrence)}>
                          Reschedule
                        </button>
                        {["cancelled", "completed", "missed", "rescheduled"].includes(occurrence.occurrence_status) ? (
                          <button className="button ghost" onClick={() => resetOccurrence(occurrence)}>
                            Reset
                          </button>
                        ) : null}
                      </div>
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
