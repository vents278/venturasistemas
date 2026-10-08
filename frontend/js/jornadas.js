/* Jornadas — ETAPA 6. Leitura + detalhe de horários. Escrita via /docs (GESTOR). */
const DIAS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];

async function api(path, opts = {}) {
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = sessionStorage.getItem("erp_token");
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { ...opts, headers: h });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

async function carregar() {
  const j = await api("/jornadas?com_horarios=true");
  document.getElementById("lista").innerHTML = j.map((x) => `
    <div class="card"><strong>${x.codigo}</strong> — ${x.nome}
    <table><thead><tr><th>dia</th><th>início</th><th>fim</th><th>carga</th><th>meia-noite</th></tr></thead>
    <tbody>${(x.jornada_horarios || []).map((hh) => `<tr><td>${DIAS[hh.dia_semana]}</td>
      <td>${hh.inicio}</td><td>${hh.fim}</td><td>${hh.carga_horas}h</td>
      <td>${hh.atravessa_meia_noite ? "sim" : "não"}</td></tr>`).join("")}</tbody></table></div>`).join("");
}
carregar();
