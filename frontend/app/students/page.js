"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "../../components/auth-provider";
import { PageHeader } from "../../components/page-header";
import { listStudents } from "../../lib/api";
import { roleCapabilities } from "../../lib/roles";

export default function StudentsPage() {
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [students, setStudents] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    listStudents().then(setStudents).catch((err) => setError(err.message));
  }, []);

  return (
    <div className="stack">
      <PageHeader
        title="Students"
        subtitle={caps.canCreateStudents ? "Review students and move directly into scheduling workflows." : "Read-only student directory and assigned contact details."}
        actions={caps.canCreateStudents ? <Link href="/students/new" className="button">Add new student</Link> : null}
      />
      {error ? <div className="alert error">{error}</div> : null}
      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Parent</th>
                <th>Email</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td>{student.full_name}</td>
                  <td>{student.parent_name}</td>
                  <td>{student.contact_email}</td>
                  <td>
                    <Link href={`/students/detail?id=${student.id}`} className="button ghost">
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
