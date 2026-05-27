/**
 * api.js – thin wrapper around the Shelf Tracker REST API.
 * Stores the JWT in localStorage and attaches it to every request.
 */

const API = (() => {
  const BASE = "/api";

  function getToken()      { return localStorage.getItem("st_token"); }
  function setToken(t)     { localStorage.setItem("st_token", t); }
  function getUsername()   { return localStorage.getItem("st_username"); }
  function setUsername(u)  { localStorage.setItem("st_username", u); }

  function logout() {
    localStorage.removeItem("st_token");
    localStorage.removeItem("st_username");
    window.location.href = "/";
  }

  async function req(method, path, body = null) {
    const token = getToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const opts = { method, headers };
    if (body !== null) opts.body = JSON.stringify(body);

    const res = await fetch(BASE + path, opts);

    if (res.status === 401) { logout(); return; }
    if (res.status === 204) return null;

    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await res.json()
      : { detail: await res.text() };
    if (!res.ok) {
      const detail = data.detail;
      const message = Array.isArray(detail)
        ? detail.map(e => e.msg.replace(/^Value error, /, "")).join(" · ")
        : (detail || "Something went wrong");
      throw new Error(message);
    }
    return data;
  }

  return {
    getToken, setToken, getUsername, setUsername, logout,

    // Auth
    signup:  (d) => req("POST", "/auth/signup", d),
    login:   (d) => req("POST", "/auth/login", d),
    me:      ()  => req("GET",  "/users/me"),

    // Books
    books:       (status) => req("GET",  `/books${status ? `?status=${status}` : ""}`),
    book:        (id)     => req("GET",  `/books/${id}`),
    addBook:     (d)      => req("POST", "/books", d),
    updateBook:  (id, d)  => req("PUT",  `/books/${id}`, d),
    deleteBook:  (id)     => req("DELETE", `/books/${id}`),

    // Reviews
    getReview:  (id)    => req("GET",  `/books/${id}/review`),
    saveReview: (id, d) => req("POST", `/books/${id}/review`, d),

    // Stats & AI
    stats:           () => req("GET",  "/stats"),
    recommendations: () => req("POST", "/recommendations"),
  };
})();

/** Show a toast notification */
function toast(msg, type = "info") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add("show"));
  setTimeout(() => {
    el.classList.remove("show");
    setTimeout(() => el.remove(), 400);
  }, 3000);
}

/** Redirect to login if not authenticated */
function requireAuth() {
  if (!API.getToken()) window.location.href = "/";
}
