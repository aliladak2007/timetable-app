export class ApiError extends Error {
  constructor(message, status, detail = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getStoredTokenFromStorage(storage) {
  return storage?.getItem("authToken") || "";
}

export function storeTokenInStorage(storage, token) {
  storage?.setItem("authToken", token);
}

export function clearTokenInStorage(storage) {
  storage?.removeItem("authToken");
}

export function buildAuthHeaders(token, extraHeaders = {}) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extraHeaders,
  };
}

export function shouldHydrateCurrentUser({ needsBootstrap, token }) {
  return !needsBootstrap && Boolean(token);
}

export function handleUnauthorizedResponse({ tokenPresent, clearToken, dispatchLogout }) {
  if (!tokenPresent) {
    return false;
  }
  clearToken();
  dispatchLogout();
  return true;
}
