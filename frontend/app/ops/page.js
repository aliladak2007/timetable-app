"use client";

import { useEffect, useState } from "react";

import { AccessDenied } from "../../components/access-denied";
import { useAuth } from "../../components/auth-provider";
import { PageHeader } from "../../components/page-header";
import {
  createClosure,
  createStudentAbsence,
  createTeacherLeave,
  deleteClosure,
  deleteStudentAbsence,
  deleteTeacherLeave,
  listAuditLogs,
  listClosures,
  listStudentAbsences,
  listStudents,
  listTeacherLeave,
  listTeachers,
} from "../../lib/api";
import { roleCapabilities } from "../../lib/roles";

const emptyRange = { start_date: "", end_date: "", start_minute: "", end_minute: "", reason: "", notes: "" };

export default function OpsPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [closures, setClosures] = useState([]);
  const [teacherLeave, setTeacherLeave] = useState([]);
  const [studentAbsences, setStudentAbsences] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [closureForm, setClosureForm] = useState({ name: "", closure_type: "holiday", start_date: "", end_date: "", notes: "" });
  const [teacherLeaveForm, setTeacherLeaveForm] = useState({ teacher_id: "", ...emptyRange });
  const [studentAbsenceForm, setStudentAbsenceForm] = useState({ student_id: "", ...emptyRange });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try {
      const [teacherData, studentData, closureData, teacherLeaveData, studentAbsenceData] = await Promise.all([
        listTeachers(),
        listStudents(),
        listClosures(),
        listTeacherLeave(),
        listStudentAbsences(),
      ]);
      setTeachers(teacherData);
      setStudents(studentData);
      setClosures(closureData);
      setTeacherLeave(teacherLeaveData);
      setStudentAbsences(studentAbsenceData);
      if (caps.canViewAudit) {
        setAuditLogs(await listAuditLogs());
      } else {
        setAuditLogs([]);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (!caps.canManageOps) {
      return;
    }
    load();
  }, [caps.canManageOps, caps.canViewAudit]);

  if (!caps.canManageOps) {
    return (
      <AccessDenied
        title="Viewer mode: read-only"
        description="Operational exception management is available to admin and staff scheduler roles."
      />
    );
  }

  const submit = async (action, successMessage) => {
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(successMessage);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="stack">
      <PageHeader
        title={caps.isAdmin ? "Operations" : "Scheduling Exceptions"}
        subtitle={caps.isAdmin ? "Manage closures, leave, absences, and audit context." : "Manage closures, leave, and absences for daily scheduling operations."}
      />
      {error ? <div className="alert error">{error}</div> : null}
      {notice ? <div className="alert">{notice}</div> : null}
      <section className="three-column">
        <div className="panel stack">
          <h3>Add closure or holiday</h3>
          <input placeholder="Name" value={closureForm.name} onChange={(e) => setClosureForm({ ...closureForm, name: e.target.value })} />
          <select value={closureForm.closure_type} onChange={(e) => setClosureForm({ ...closureForm, closure_type: e.target.value })}>
            <option value="holiday">Holiday</option>
            <option value="closure">Closure</option>
          </select>
          <input type="date" value={closureForm.start_date} onChange={(e) => setClosureForm({ ...closureForm, start_date: e.target.value })} />
          <input type="date" value={closureForm.end_date} onChange={(e) => setClosureForm({ ...closureForm, end_date: e.target.value })} />
          <textarea rows="3" value={closureForm.notes} onChange={(e) => setClosureForm({ ...closureForm, notes: e.target.value })} />
          <button
            className="button"
            onClick={() => submit(() => createClosure(closureForm), "Closure saved.")}
          >
            Save closure
          </button>
        </div>
        <div className="panel stack">
          <h3>Add teacher leave</h3>
          <select value={teacherLeaveForm.teacher_id} onChange={(e) => setTeacherLeaveForm({ ...teacherLeaveForm, teacher_id: Number(e.target.value) })}>
            <option value="">Select teacher</option>
            {teachers.map((teacher) => (
              <option key={teacher.id} value={teacher.id}>
                {teacher.full_name}
              </option>
            ))}
          </select>
          <input type="date" value={teacherLeaveForm.start_date} onChange={(e) => setTeacherLeaveForm({ ...teacherLeaveForm, start_date: e.target.value })} />
          <input type="date" value={teacherLeaveForm.end_date} onChange={(e) => setTeacherLeaveForm({ ...teacherLeaveForm, end_date: e.target.value })} />
          <input placeholder="Reason" value={teacherLeaveForm.reason} onChange={(e) => setTeacherLeaveForm({ ...teacherLeaveForm, reason: e.target.value })} />
          <button
            className="button"
            onClick={() => submit(() => createTeacherLeave({ ...teacherLeaveForm, start_minute: null, end_minute: null }), "Teacher leave saved.")}
          >
            Save leave
          </button>
        </div>
        <div className="panel stack">
          <h3>Add student absence</h3>
          <select value={studentAbsenceForm.student_id} onChange={(e) => setStudentAbsenceForm({ ...studentAbsenceForm, student_id: Number(e.target.value) })}>
            <option value="">Select student</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.full_name}
              </option>
            ))}
          </select>
          <input type="date" value={studentAbsenceForm.start_date} onChange={(e) => setStudentAbsenceForm({ ...studentAbsenceForm, start_date: e.target.value })} />
          <input type="date" value={studentAbsenceForm.end_date} onChange={(e) => setStudentAbsenceForm({ ...studentAbsenceForm, end_date: e.target.value })} />
          <input placeholder="Reason" value={studentAbsenceForm.reason} onChange={(e) => setStudentAbsenceForm({ ...studentAbsenceForm, reason: e.target.value })} />
          <button
            className="button"
            onClick={() => submit(() => createStudentAbsence({ ...studentAbsenceForm, start_minute: null, end_minute: null }), "Student absence saved.")}
          >
            Save absence
          </button>
        </div>
      </section>
      <section className="two-column">
        <div className="panel">
          <h3>Current operational blocks</h3>
          <div className="stack">
            {closures.map((item) => (
              <div key={`closure-${item.id}`} className="list-card">
                <strong>{item.name}</strong>
                <p className="muted">{item.start_date} to {item.end_date}</p>
                <button className="button ghost" onClick={() => submit(() => deleteClosure(item.id), "Closure deleted.")}>
                  Delete
                </button>
              </div>
            ))}
            {teacherLeave.map((item) => (
              <div key={`teacher-leave-${item.id}`} className="list-card">
                <strong>Teacher leave #{item.id}</strong>
                <p className="muted">{item.start_date} to {item.end_date}</p>
                <button className="button ghost" onClick={() => submit(() => deleteTeacherLeave(item.id), "Teacher leave deleted.")}>
                  Delete
                </button>
              </div>
            ))}
            {studentAbsences.map((item) => (
              <div key={`student-absence-${item.id}`} className="list-card">
                <strong>Student absence #{item.id}</strong>
                <p className="muted">{item.start_date} to {item.end_date}</p>
                <button className="button ghost" onClick={() => submit(() => deleteStudentAbsence(item.id), "Student absence deleted.")}>
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>
        {caps.canViewAudit ? (
          <div className="panel">
            <h3>Recent audit log</h3>
            <div className="stack">
              {auditLogs.slice(0, 20).map((item) => (
                <div key={item.id} className="list-card">
                  <strong>{item.action}</strong>
                  <p className="muted">{item.summary}</p>
                  <p className="muted">{item.actor_email || "system"}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}
