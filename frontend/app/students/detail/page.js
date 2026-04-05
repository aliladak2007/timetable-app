"use client";

import { useSearchParams } from "next/navigation";

import StudentDetailClient from "./student-detail-client";

export default function StudentDetailPage() {
  const searchParams = useSearchParams();
  const studentId = searchParams.get("id");

  return <StudentDetailClient studentId={studentId} />;
}
