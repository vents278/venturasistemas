/* Presença — ETAPA 7. Grade diária: funcionários ativos x status do dia, salva em /lote. */
let STATUS = [];

async function api(path, opts = {}) {
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = sessionStorage.getItem("erp_token");
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { ...opts, headers: h });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

data.valueAsDate = new Date();

async function carregar() {
  STATUS = await api("/presencas/status-presenca");
  const funcs = await api("/funcionarios?ativo=true&limit=100");
  const pres = await api("/presencas?data=" + data.value);
  const map = Object.fromEntries(pres.map((p) => [p.funcionario_id, p.status_codigo]));
  tb.innerHTML = funcs.items.map((f) => `<tr data-fid="${f.id}">
    <td>${f.matricula}</td><td>${f.nome}</td>
    <td><select>${STATUS.map((s) => `<option value="${s.codigo}" ${map[f.id] === s.codigo ? "selected" : ""}>${s.codigo}</option>`).join("")}</select></td>
  </tr>`).join("");
}

async function salvar() {
  const itens = [...tb.rows].map((tr) => ({
    funcionario_id: tr.dataset.fid, status_codigo: tr.querySelector("select").value,
  }));
  const r = await api("/presencas/lote", { method: "POST", body: JSON.stringify({ data: data.value, itens }) });
  alert(`OK: ${r.ok}` + (r.erros.length ? ` | Erros: ${r.erros.length} (${r.erros[0].erro})` : ""));
}

carregar();
