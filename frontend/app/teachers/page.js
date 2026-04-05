"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "../../components/auth-provider";
import { PageHeader } from "../../components/page-header";
import { createTeacher, listTeachers } from "../../lib/api";
import { roleCapabilities } from "../../lib/roles";

const emptyForm = { full_name: "", email: "", subject_tags: "", active: true };

export default function TeachersPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [teachers, setTeachers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const loadTeachers = async () => {
    try {
      setTeachers(await listTeachers());
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadTeachers();
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (!form.full_name || !form.email) {
      setError("Teacher name and email are required.");
      return;
    }
    setSaving(true);
    try {
      await createTeacher(form);
      setForm(emptyForm);
      await loadTeachers();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="stack">
      <PageHeader
        title={caps.isScoped ? "My Teacher Profile" : "Teachers"}
        subtitle={
          caps.canEditTeachers
            ? caps.canCreateTeachers
              ? "Manage tutor profiles and open each teacher's weekly availability."
              : "Review and update your own teacher profile and weekly availability."
            : "Browse tutor profiles and availability."
        }
      />
      {error ? <div className="alert error">{error}</div> : null}
      <div className={caps.canCreateTeachers ? "two-column" : "stack"}>
        <section className="panel">
          <div className="panel-header">
            <h3>Teacher list</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Subjects</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {teachers.map((teacher) => (
                  <tr key={teacher.id}>
                    <td>{teacher.full_name}</td>
                    <td>{teacher.email}</td>
                    <td>{teacher.subject_tags}</td>
                    <td>
                      <Link href={`/teachers/detail?id=${teacher.id}`} className="button ghost">
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        {caps.canCreateTeachers ? (
          <section className="panel">
            <div className="panel-header">
              <h3>Add teacher</h3>
            </div>
            <form className="form-grid" onSubmit={submit}>
              <input
                placeholder="Full name"
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              />
              <input
                type="email"
                placeholder="Email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
              />
              <input
                placeholder="Subjects, comma separated"
                value={form.subject_tags}
                onChange={(event) => setForm({ ...form, subject_tags: event.target.value })}
              />
              <button type="submit" className="button" disabled={saving}>
                {saving ? "Saving..." : "Create teacher"}
              </button>
            </form>
          </section>
        ) : null}
      </div>
    </div>
  );
}
