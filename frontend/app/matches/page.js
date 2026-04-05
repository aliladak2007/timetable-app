"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AccessDenied } from "../../components/access-denied";
import { useAuth } from "../../components/auth-provider";
import { PageHeader } from "../../components/page-header";
import { formatWindow, getTeacher, suggestMatches } from "../../lib/api";
import { roleCapabilities } from "../../lib/roles";

export default function MatchesPage() {
  const router = useRouter();
  const { user } = useAuth();
  const caps = roleCapabilities(user);
  const [draft, setDraft] = useState(null);
  const [teacher, setTeacher] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [rejections, setRejections] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!caps.canUseMatching) {
      setLoading(false);
      return;
    }
    const raw = window.sessionStorage.getItem("pendingStudentDraft");
    if (!raw) {
      setLoading(false);
      return;
    }

    const parsed = JSON.parse(raw);
    setDraft(parsed);

    Promise.all([
      getTeacher(parsed.student.teacher_id),
      suggestMatches({
        teacher_id: parsed.student.teacher_id,
        duration_minutes: parsed.student.duration_minutes,
        student_preferences: parsed.preferences,
        student_blocked_times: parsed.blockedTimes,
      }),
    ])
      .then(([teacherData, result]) => {
        setTeacher(teacherData);
        setSuggestions(result.suggestions);
        setRejections(result.rejected_slots || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [caps.canUseMatching]);

  const chooseSuggestion = (suggestion) => {
    window.sessionStorage.setItem("pendingBookingChoice", JSON.stringify(suggestion));
    router.push("/bookings/confirm");
  };

  if (!caps.canUseMatching) {
    return (
      <AccessDenied
        title="Viewer mode: read-only"
        description="Matching and booking actions are available for admin and staff scheduler roles."
      />
    );
  }

  return (
    <div className="stack">
      <PageHeader
        title="Match Suggestions"
        subtitle="Review ranked weekly slots returned by the backend matching engine."
      />
      {error ? <div className="alert error">{error}</div> : null}
      {!draft && !loading ? <div className="alert">No draft student flow found. Start from Add New Student.</div> : null}
      {draft ? (
        <section className="panel">
          <div className="split-header">
            <div>
              <h3>{draft.student.full_name}</h3>
              <p className="muted">
                Teacher: {teacher?.full_name || "Loading..."} | Duration: {draft.student.duration_minutes} minutes
              </p>
            </div>
          </div>
        </section>
      ) : null}
      <section className="stack">
        {loading ? <div className="alert">Loading suggestions...</div> : null}
        {!loading && draft && !suggestions.length ? (
          <div className="alert error">No valid recurring slots matched the current constraints.</div>
        ) : null}
        {suggestions.map((suggestion, index) => (
          <div key={`${suggestion.weekday}-${suggestion.start_minute}`} className="panel">
            <div className="split-header">
              <div>
                <p className="eyebrow">Suggestion {index + 1}</p>
                <h3>{formatWindow(suggestion)}</h3>
                <div className="tag-list">
                  <span className="tag">Score {suggestion.score}</span>
                  {suggestion.reasons.map((reason) => (
                    <span key={reason} className="tag">
                      {reason}
                    </span>
                  ))}
                </div>
                <p className="muted">
                  Breakdown: preference {suggestion.score_breakdown.preference_fit}, teacher compactness{" "}
                  {suggestion.score_breakdown.teacher_compactness}, student compactness{" "}
                  {suggestion.score_breakdown.student_compactness}, earlier-slot bonus{" "}
                  {suggestion.score_breakdown.earlier_slot_bonus}
                </p>
              </div>
              <button className="button" onClick={() => chooseSuggestion(suggestion)}>
                Confirm this slot
              </button>
            </div>
          </div>
        ))}
      </section>
      {rejections.length ? (
        <section className="panel">
          <div className="panel-header">
            <h3>Rejected slots</h3>
          </div>
          <div className="stack">
            {rejections.map((slot) => (
              <div key={`${slot.weekday}-${slot.start_minute}-${slot.end_minute}`} className="list-card">
                <strong>{formatWindow(slot)}</strong>
                <p className="muted">{slot.reasons.join(" | ")}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
