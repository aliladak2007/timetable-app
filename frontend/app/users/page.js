"use client";

import { useEffect, useState } from "react";

import { AccessDenied } from "../../components/access-denied";
import { useAuth } from "../../components/auth-provider";
import { PageHeader } from "../../components/page-header";
import { createUser, forceLogoutUser, listTeachers, listUsers, updateUser } from "../../lib/api";
import { roleCapabilities } from "../../lib/roles";

const emptyForm = {
  full_name: "",
  email: "",
  password: "",
  role: "staff_scheduler",
  linked_teacher_id: "",
  active: true,
};

export default function UsersPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [users, setUsers] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [drafts, setDrafts] = useState({});
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try {
      const [userData, teacherData] = await Promise.all([listUsers(), listTeachers()]);
      setUsers(userData);
      setTeachers(teacherData);
      setDrafts(
        Object.fromEntries(
          userData.map((item) => [
            item.id,
            {
              role: item.role,
              linked_teacher_id: item.linked_teacher_id ? String(item.linked_teacher_id) : "",
            },
          ]),
        ),
      );
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (!caps.canManageUsers) {
      return;
    }
    load();
  }, [caps.canManageUsers]);

  if (!caps.canManageUsers) {
    return (
      <AccessDenied
        title="Admin access required"
        description="User and access management is available only to administrator accounts."
      />
    );
  }

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    if (form.role !== "admin" && !form.linked_teacher_id) {
      setError("Select a linked teacher for non-admin users.");
      return;
    }
    try {
      await createUser({
        ...form,
        linked_teacher_id: form.role === "admin" ? null : Number(form.linked_teacher_id),
      });
      setForm(emptyForm);
      setNotice("User created.");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleUser = async (user) => {
    try {
      await updateUser(user.id, { active: !user.active });
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const revokeUser = async (user) => {
    try {
      await forceLogoutUser(user.id);
      setNotice(`Forced logout for ${user.email}.`);
    } catch (err) {
      setError(err.message);
    }
  };

  const saveAccess = async (user) => {
    const draft = drafts[user.id];
    if (draft.role !== "admin" && !draft.linked_teacher_id) {
      setError("Select a linked teacher for non-admin users.");
      return;
    }
    try {
      await updateUser(user.id, {
        role: draft.role,
        linked_teacher_id: draft.role === "admin" ? null : Number(draft.linked_teacher_id),
      });
      setNotice(`Updated access for ${user.email}.`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="stack">
      <PageHeader title="Users" subtitle="Create additional staff accounts, change roles, and invalidate sessions." />
      {error ? <div className="alert error">{error}</div> : null}
      {notice ? <div className="alert">{notice}</div> : null}
      <div className="two-column">
        <section className="panel">
          <div className="panel-header">
            <h3>Existing users</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Linked teacher</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.full_name}</td>
                    <td>{user.email}</td>
                    <td>
                      <select
                        value={drafts[user.id]?.role || user.role}
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [user.id]: {
                              ...current[user.id],
                              role: event.target.value,
                              linked_teacher_id:
                                event.target.value === "admin" ? "" : current[user.id]?.linked_teacher_id || "",
                            },
                          }))
                        }
                      >
                        <option value="admin">Admin</option>
                        <option value="staff_scheduler">Staff scheduler</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </td>
                    <td>
                      {drafts[user.id]?.role === "admin" ? (
                        <span className="muted">Global access</span>
                      ) : (
                        <select
                          value={drafts[user.id]?.linked_teacher_id || ""}
                          onChange={(event) =>
                            setDrafts((current) => ({
                              ...current,
                              [user.id]: {
                                ...current[user.id],
                                linked_teacher_id: event.target.value,
                              },
                            }))
                          }
                        >
                          <option value="">Select teacher</option>
                          {teachers.map((teacher) => (
                            <option key={teacher.id} value={teacher.id}>
                              {teacher.full_name}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td>{user.active ? "Active" : "Disabled"}</td>
                    <td>
                      <div className="inline-actions">
                        <button className="button ghost" onClick={() => saveAccess(user)}>
                          Save access
                        </button>
                        <button className="button ghost" onClick={() => toggleUser(user)}>
                          {user.active ? "Disable" : "Enable"}
                        </button>
                        <button className="button ghost" onClick={() => revokeUser(user)}>
                          Force logout
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section className="panel">
          <div className="panel-header">
            <h3>Create user</h3>
          </div>
          <form className="form-grid" onSubmit={submit}>
            <input placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <input
              placeholder="Strong password"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="admin">Admin</option>
              <option value="staff_scheduler">Staff scheduler</option>
              <option value="viewer">Viewer</option>
            </select>
            {form.role === "admin" ? (
              <input value="Global access" readOnly />
            ) : (
              <select
                value={form.linked_teacher_id}
                onChange={(e) => setForm({ ...form, linked_teacher_id: e.target.value })}
              >
                <option value="">Select teacher</option>
                {teachers.map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.full_name}
                  </option>
                ))}
              </select>
            )}
            <button type="submit" className="button">
              Create user
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}
