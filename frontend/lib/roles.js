export const ROLES = {
  ADMIN: "admin",
  STAFF_SCHEDULER: "staff_scheduler",
  VIEWER: "viewer",
};

export const roleLabels = {
  [ROLES.ADMIN]: "Administrator",
  [ROLES.STAFF_SCHEDULER]: "Staff Scheduler",
  [ROLES.VIEWER]: "Viewer",
};

export function getRole(user) {
  return user?.role || ROLES.VIEWER;
}

export function roleCapabilities(user) {
  const role = getRole(user);
  const isAdmin = role === ROLES.ADMIN;
  const isScheduler = role === ROLES.STAFF_SCHEDULER;
  const isViewer = role === ROLES.VIEWER;
  return {
    role,
    isAdmin,
    isScheduler,
    isViewer,
    isScoped: !isAdmin,
    canManageUsers: isAdmin,
    canManageOps: isAdmin,
    canViewAudit: isAdmin,
    canEditTeachers: isAdmin || isScheduler,
    canCreateTeachers: isAdmin,
    canEditStudents: isAdmin || isScheduler,
    canCreateStudents: isAdmin || isScheduler,
    canUseMatching: isAdmin || isScheduler,
    canManageSessions: isAdmin || isScheduler,
    canCreateCalendarFeed: isAdmin,
    canExportCsv: true,
  };
}

export function navForRole(user) {
  const role = getRole(user);
  if (role === ROLES.ADMIN) {
    return [
      { href: "/", label: "Admin Dashboard" },
      { href: "/sessions", label: "Sessions" },
      { href: "/students", label: "Students" },
      { href: "/teachers", label: "Teachers" },
      { href: "/matches", label: "Match Queue" },
      { href: "/students/new", label: "Add Student" },
      { href: "/ops", label: "Operations" },
      { href: "/exports", label: "Exports" },
      { href: "/users", label: "Users & Access" },
    ];
  }
  if (role === ROLES.STAFF_SCHEDULER) {
    return [
      { href: "/", label: "My Dashboard" },
      { href: "/sessions", label: "Sessions" },
      { href: "/students", label: "Students" },
      { href: "/teachers", label: "My Profile" },
      { href: "/matches", label: "Match Queue" },
      { href: "/students/new", label: "Add Student" },
      { href: "/exports", label: "Exports" },
    ];
  }
  return [
    { href: "/", label: "My Dashboard" },
    { href: "/sessions", label: "Sessions" },
    { href: "/students", label: "Students" },
    { href: "/teachers", label: "My Profile" },
    { href: "/exports", label: "Exports" },
  ];
}
