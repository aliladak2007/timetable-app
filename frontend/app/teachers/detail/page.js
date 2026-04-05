"use client";

import { useSearchParams } from "next/navigation";

import TeacherDetailClient from "./teacher-detail-client";

export default function TeacherDetailPage() {
  const searchParams = useSearchParams();
  const teacherId = searchParams.get("id");

  return <TeacherDetailClient teacherId={teacherId} />;
}
