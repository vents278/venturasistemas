/* Apropriação — ETAPA 8. Dia de um funcionário em N OS + saldo previsto x realizado. */
let OSS = [];

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

async function init() {
  const f = await api("/funcionarios?ativo=true&limit=100");
  func.innerHTML = f.items.map((x) => `<option value="${x.id}">${x.matricula} — ${x.nome}</option>`).join("");
  OSS = await api("/os");
  await carregar();
}

async function carregar() {
  const map = Object.fromEntries((await api(`/apropriacoes?funcionario_id=${func.value}&data=${data.value}`)).map((a) => [a.os_id, a.horas]));
  tb.innerHTML = OSS.map((o) => `<tr data-os="${o.id}"><td>${o.codigo}</td>
    <td><input type="number" min="0" max="24" step="0.5" value="${map[o.id] || ""}" placeholder="0" /></td></tr>`).join("");
  try {
    const s = await api(`/apropriacoes/saldo?funcionario_id=${func.value}&data=${data.value}`);
    saldo.textContent = `Carga: ${s.carga_prevista}h | Apropriado: ${s.total_apropriado}h | Saldo: ${s.saldo}h`;
  } catch { saldo.textContent = ""; }
}

async function salvar() {
  const itens = [...tb.rows].map((tr) => ({ os_id: tr.dataset.os, horas: parseFloat(tr.querySelector("input").value) || 0 }))
    .filter((x) => x.horas > 0);
  if (!itens.length) return alert("Informe ao menos uma OS com horas.");
  const r = await api("/apropriacoes/lote", { method: "POST", body: JSON.stringify({ funcionario_id: func.value, data: data.value, itens }) });
  alert(`Apropriado: ${r.total_apropriado}h / Carga: ${r.carga_prevista}h (saldo ${r.saldo}h)`);
  carregar();
}

init();
