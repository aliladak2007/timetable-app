import assert from "node:assert/strict";

import {
  buildAuthHeaders,
  clearTokenInStorage,
  getStoredTokenFromStorage,
  handleUnauthorizedResponse,
  shouldHydrateCurrentUser,
  storeTokenInStorage,
} from "../lib/auth-transport.mjs";


function createStorage() {
  const values = new Map();
  return {
    getItem(key) {
      return values.has(key) ? values.get(key) : null;
    },
    setItem(key, value) {
      values.set(key, value);
    },
    removeItem(key) {
      values.delete(key);
    },
  };
}


function run(name, fn) {
  try {
    fn();
    console.log(`PASS ${name}`);
  } catch (error) {
    console.error(`FAIL ${name}`);
    throw error;
  }
}


run("token persists under the expected authToken key", () => {
  const storage = createStorage();

  storeTokenInStorage(storage, "token-123");

  assert.equal(getStoredTokenFromStorage(storage), "token-123");

  clearTokenInStorage(storage);

  assert.equal(getStoredTokenFromStorage(storage), "");
});


run("/me requests include Authorization header after login token is stored", () => {
  const headers = buildAuthHeaders("token-123");

  assert.equal(headers.Authorization, "Bearer token-123");
  assert.equal(headers["Content-Type"], "application/json");
});


run("unauthorized responses without a token do not dispatch logout or retry state changes", () => {
  let cleared = 0;
  let dispatched = 0;

  const handled = handleUnauthorizedResponse({
    tokenPresent: false,
    clearToken: () => {
      cleared += 1;
    },
    dispatchLogout: () => {
      dispatched += 1;
    },
  });

  assert.equal(handled, false);
  assert.equal(cleared, 0);
  assert.equal(dispatched, 0);
});


run("unauthorized responses with a token clear auth state exactly once", () => {
  let cleared = 0;
  let dispatched = 0;

  const handled = handleUnauthorizedResponse({
    tokenPresent: true,
    clearToken: () => {
      cleared += 1;
    },
    dispatchLogout: () => {
      dispatched += 1;
    },
  });

  assert.equal(handled, true);
  assert.equal(cleared, 1);
  assert.equal(dispatched, 1);
});


run("auth hydration only calls /me when bootstrap is complete and a token exists", () => {
  assert.equal(shouldHydrateCurrentUser({ needsBootstrap: false, token: "token-123" }), true);
  assert.equal(shouldHydrateCurrentUser({ needsBootstrap: false, token: "" }), false);
  assert.equal(shouldHydrateCurrentUser({ needsBootstrap: true, token: "token-123" }), false);
});
