/* Funcionários — ETAPA 5. Tabela + filtros (busca automática) + modal (criar/inativar). */
let editId = null, T_BUSCA = null, REQ = 0;

async function api(path, opts = {}) {
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = sessionStorage.getItem("erp_token");
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { ...opts, headers: h });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

function debounceBusca() { clearTimeout(T_BUSCA); T_BUSCA = setTimeout(carregar, 300); }

async function carregarJornadas() {
  try {
    const j = await api("/jornadas");
    document.getElementById("f_jornada").innerHTML =
      '<option value="">jornada padrão...</option>' + j.map((x) => `<option value="${x.id}">${x.codigo}</option>`).join("");
    await carregarSupervisores();
    try {
      const emps = await api("/empresas");
      document.getElementById("f_emp").innerHTML =
        '<option value="">empresa...</option>' + emps.map((x) => `<option value="${x.id}">${x.nome}</option>`).join("");
    } catch { /* sem acesso a empresas */ }
  } catch { /* sem Supabase: segue sem selects */ }
}

/* Supervisor responsável: apenas funcionários cujo cargo é de supervisão. */
async function carregarSupervisores() {
  const f = await api("/funcionarios?ativo=true&cargo=supervisor&limit=100");
  document.getElementById("f_sup").innerHTML =
    '<option value="">supervisor responsável...</option>' +
    f.items.map((x) => `<option value="${x.id}">${x.nome}${x.cargo ? " — " + x.cargo : ""}</option>`).join("");
}

async function carregar() {
  const meu = ++REQ;
  const p = new URLSearchParams();
  if (q.value.trim()) p.set("q", q.value.trim());
  if (ativo.value) p.set("ativo", ativo.value);
  if (setor.value.trim()) p.set("setor", setor.value.trim());
  const d = await api("/funcionarios?" + p);
  if (meu !== REQ) return; // ignora respostas fora de ordem
  tb.innerHTML = d.items.map((f) => `<tr>
    <td>${f.matricula}</td><td>${f.nome}${f.em_treinamento ? ' <span class="MEDIA">TREIN</span>' : ""}</td>
    <td>${f.cargo || "-"}</td><td>${f.area || "-"}</td>
    <td><span class="badge ${f.ativo ? "on" : "off"}">${f.ativo ? "ativo" : "inativo"}</span></td>
    <td><button onclick="editar('${f.id}')">Editar</button> ${f.ativo ? `<button onclick="inativar('${f.id}')">Inativar</button>` : ""}</td>
  </tr>`).join("") || '<tr><td colspan="6">Nenhum registro</td></tr>';
}

async function editar(id) {
  const f = await api("/funcionarios/" + id);
  editId = id; mt.textContent = "Editar funcionário";
  f_nome.value = f.nome || ""; f_cargo.value = f.cargo || ""; f_area.value = f.area || "";
  f_matricula.value = f.matricula || ""; f_setor.value = f.setor || "";
  f_admissao.value = f.admissao || ""; f_deslig.value = f.desligamento || "";
  f_obs.value = f.observacoes || ""; f_trein.checked = !!f.em_treinamento;
  f_jornada.value = f.jornada_id || ""; f_emp.value = f.empresa_id || "";
  try { await prepararSupervisorSelect(f.supervisor_id, id); } catch { f_sup.value = f.supervisor_id || ""; }
  modal.style.display = "block";
}

/* Marca o supervisor atual (mesmo que o cargo dele não seja de supervisão) e
   remove o próprio funcionário da lista para não auto-referenciar. */
async function prepararSupervisorSelect(supervisorId, selfId) {
  await carregarSupervisores();
  const sel = document.getElementById("f_sup");
  if (selfId) [...sel.options].forEach((o) => { if (o.value === selfId) o.remove(); });
  if (supervisorId && ![...sel.options].some((o) => o.value === supervisorId)) {
    try {
      const s = await api("/funcionarios/" + supervisorId);
      sel.insertAdjacentHTML("beforeend", `<option value="${s.id}">${s.nome} — atual</option>`);
    } catch { /* supervisor inacessível */ }
  }
  sel.value = supervisorId || "";
}

function abrirModal() {
  editId = null; mt.textContent = "Novo funcionário"; form.reset();
  carregarSupervisores().catch(() => {});
  modal.style.display = "block";
}
function fecharModal() { modal.style.display = "none"; }

form.onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    nome: f_nome.value, cargo: f_cargo.value || null, area: f_area.value || null,
    supervisor_id: f_sup.value || null, matricula: f_matricula.value || null,
    empresa_id: f_emp.value || null,
    admissao: f_admissao.value || null, setor: f_setor.value || null,
    desligamento: f_deslig.value || null, jornada_id: f_jornada.value || null,
    em_treinamento: f_trein.checked,
    observacoes: f_obs.value || null,
  };
  try {
    await api(editId ? "/funcionarios/" + editId : "/funcionarios",
      { method: editId ? "PATCH" : "POST", body: JSON.stringify(body) });
  } catch (err) { return alert(err.message); }
  fecharModal(); carregar();
};

async function inativar(id) {
  if (!confirm("Inativar (exclusão lógica)? Histórico é preservado.")) return;
  await api("/funcionarios/" + id, { method: "DELETE" });
  carregar();
}

carregarJornadas().then(carregar);
