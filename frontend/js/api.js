/* Em dev (localhost) fala com uvicorn na 8000; publicado, usa /api do mesmo domínio. */
const API_BASE =
  location.hostname === "127.0.0.1" || location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : location.origin + "/api";

async function apiGet(path) {
  const headers = {};
  const t = sessionStorage.getItem("erp_token");
  if (t) headers.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { headers });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error("API " + r.status);
  return r.json();
}
