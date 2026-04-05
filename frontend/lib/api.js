import {
  ApiError,
  buildAuthHeaders,
  clearTokenInStorage,
  getStoredTokenFromStorage,
  handleUnauthorizedResponse,
  shouldHydrateCurrentUser,
  storeTokenInStorage,
} from "./auth-transport.mjs";

const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

let runtimeConfigPromise;

function getStoredToken() {
  if (typeof window === "undefined") {
    return "";
  }
  return getStoredTokenFromStorage(window.sessionStorage);
}

export function clearStoredToken() {
  if (typeof window === "undefined") {
    return;
  }
  clearTokenInStorage(window.sessionStorage);
}

export function storeToken(token) {
  if (typeof window === "undefined") {
    return;
  }
  storeTokenInStorage(window.sessionStorage, token);
}

export function hasStoredToken() {
  return Boolean(getStoredToken());
}

async function getDesktopRuntimeConfig() {
  if (typeof window === "undefined") {
    return null;
  }

  if (!runtimeConfigPromise) {
    runtimeConfigPromise = Promise.resolve()
      .then(() => {
        const invoke = window.__TAURI_INTERNALS__?.invoke;
        if (!invoke) {
          return null;
        }
        return invoke("get_runtime_config");
      })
      .catch(() => null);
  }

  return runtimeConfigPromise;
}

async function getApiBase() {
  const runtimeConfig = await getDesktopRuntimeConfig();
  return runtimeConfig?.apiBaseUrl || DEFAULT_API_BASE;
}

export const weekdayLabels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export async function getSessionsCsvUrl() {
  const apiBase = await getApiBase();
  return `${apiBase}/exports/sessions.csv`;
}

export async function getCalendarDownloadUrl(ownerType, ownerId) {
  const apiBase = await getApiBase();
  return `${apiBase}/exports/calendar/${ownerType}/${ownerId}.ics`;
}

export async function getCalendarFeedUrl(token) {
  const apiBase = await getApiBase();
  return `${apiBase}/exports/calendar-feed/${token}.ics`;
}

export async function downloadAuthorizedFile(url, filename) {
  const token = getStoredToken();
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error("Download failed");
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

async function request(path, options = {}) {
  const apiBase = await getApiBase();
  const token = getStoredToken();
  const response = await fetch(`${apiBase}${path}`, {
    headers: buildAuthHeaders(token, options.headers || {}),
    cache: "no-store",
    ...options,
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const data = await response.json();
      if (Array.isArray(data.detail)) {
        message = data.detail.join(" ");
      } else if (typeof data.detail === "string") {
        message = data.detail;
      }
    } catch {}

    if (response.status === 401 && typeof window !== "undefined") {
      handleUnauthorizedResponse({
        tokenPresent: Boolean(token),
        clearToken: clearStoredToken,
        dispatchLogout: () => window.dispatchEvent(new Event("auth:logout")),
      });
    }

    throw new ApiError(message, response.status, null);
  }

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export function getBootstrapStatus() {
  return request("/auth/bootstrap-status");
}

export function bootstrapAdmin(payload) {
  return request("/auth/bootstrap-admin", { method: "POST", body: JSON.stringify(payload) });
}

export function login(payload) {
  return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function getCurrentUser() {
  return request("/auth/me");
}

export { buildAuthHeaders, shouldHydrateCurrentUser };

export function changePassword(payload) {
  return request("/auth/me/change-password", { method: "POST", body: JSON.stringify(payload) });
}

export function listUsers() {
  return request("/auth/users");
}

export function createUser(payload) {
  return request("/auth/users", { method: "POST", body: JSON.stringify(payload) });
}

export function updateUser(id, payload) {
  return request(`/auth/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function forceLogoutUser(id) {
  return request(`/auth/users/${id}/force-logout`, { method: "POST" });
}

export function listTeachers() {
  return request("/teachers");
}

export function getTeacher(id) {
  return request(`/teachers/${id}`);
}

export function createTeacher(payload) {
  return request("/teachers", { method: "POST", body: JSON.stringify(payload) });
}

export function updateTeacher(id, payload) {
  return request(`/teachers/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function replaceTeacherAvailability(id, payload) {
  return request(`/teachers/${id}/availability`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteTeacher(id) {
  return request(`/teachers/${id}`, { method: "DELETE" });
}

export function listStudents() {
  return request("/students");
}

export function getStudent(id) {
  return request(`/students/${id}`);
}

export function createStudent(payload) {
  return request("/students", { method: "POST", body: JSON.stringify(payload) });
}

export function updateStudent(id, payload) {
  return request(`/students/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function replaceStudentPreferences(id, payload) {
  return request(`/students/${id}/preferences`, { method: "PUT", body: JSON.stringify(payload) });
}

export function replaceStudentBlockedTimes(id, payload) {
  return request(`/students/${id}/blocked-times`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteStudent(id) {
  return request(`/students/${id}`, { method: "DELETE" });
}

export function listSessions() {
  return request("/sessions");
}

export function createSession(payload) {
  return request("/sessions", { method: "POST", body: JSON.stringify(payload) });
}

export function updateSession(id, payload) {
  return request(`/sessions/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function suggestMatches(payload) {
  return request("/matches/suggest", { method: "POST", body: JSON.stringify(payload) });
}

export function getDashboardSummary() {
  return request("/dashboard/summary");
}

export function queryOccurrences(payload) {
  return request("/schedule/occurrences/query", { method: "POST", body: JSON.stringify(payload) });
}

export function saveOccurrenceException(sessionId, payload) {
  return request(`/schedule/sessions/${sessionId}/exceptions`, { method: "POST", body: JSON.stringify(payload) });
}

export function deleteOccurrenceException(sessionId, occurrenceDate) {
  return request(`/schedule/sessions/${sessionId}/exceptions/${occurrenceDate}`, { method: "DELETE" });
}

export function listClosures() {
  return request("/schedule/closures");
}

export function createClosure(payload) {
  return request("/schedule/closures", { method: "POST", body: JSON.stringify(payload) });
}

export function deleteClosure(id) {
  return request(`/schedule/closures/${id}`, { method: "DELETE" });
}

export function listTeacherLeave() {
  return request("/schedule/teacher-leave");
}

export function createTeacherLeave(payload) {
  return request("/schedule/teacher-leave", { method: "POST", body: JSON.stringify(payload) });
}

export function deleteTeacherLeave(id) {
  return request(`/schedule/teacher-leave/${id}`, { method: "DELETE" });
}

export function listStudentAbsences() {
  return request("/schedule/student-absences");
}

export function createStudentAbsence(payload) {
  return request("/schedule/student-absences", { method: "POST", body: JSON.stringify(payload) });
}

export function deleteStudentAbsence(id) {
  return request(`/schedule/student-absences/${id}`, { method: "DELETE" });
}

export function listAuditLogs() {
  return request("/audit-logs");
}

export function createCalendarFeedToken(payload) {
  return request("/exports/calendar-feeds", { method: "POST", body: JSON.stringify(payload) });
}

export function formatTime(minute) {
  const hours = Math.floor(minute / 60);
  const mins = minute % 60;
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

export function formatWindow(item) {
  return `${weekdayLabels[item.weekday]} ${formatTime(item.start_minute)}-${formatTime(item.end_minute)}`;
}

export function emptyWeeklyRows(extra = {}) {
  return weekdayLabels.map((_, weekday) => ({
    weekday,
    start_minute: 900,
    end_minute: 960,
    ...extra,
  }));
}
