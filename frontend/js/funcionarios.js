/* Funcionários — ETAPA 5. Tabela + filtros + modal (criar/inativar). */
let editId = null;

async function api(path, opts = {}) {
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = sessionStorage.getItem("erp_token");
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { ...opts, headers: h });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

async function carregarJornadas() {
  try {
    const j = await api("/jornadas");
    document.getElementById("f_jornada").innerHTML =
      '<option value="">jornada padrão...</option>' + j.map((x) => `<option value="${x.id}">${x.codigo}</option>`).join("");
    const f = await api("/funcionarios?ativo=true&limit=100");
    document.getElementById("f_sup").innerHTML =
      '<option value="">supervisor responsável...</option>' + f.items.map((x) => `<option value="${x.id}">${x.nome}</option>`).join("");
  } catch { /* sem Supabase: segue sem selects */ }
}

async function carregar() {
  const p = new URLSearchParams();
  if (q.value) p.set("q", q.value);
  if (ativo.value) p.set("ativo", ativo.value);
  if (setor.value) p.set("setor", setor.value);
  const d = await api("/funcionarios?" + p);
  tb.innerHTML = d.items.map((f) => `<tr>
    <td>${f.matricula}</td><td>${f.nome}${f.em_treinamento ? ' <span class="MEDIA">TREIN</span>' : ""}</td>
    <td>${f.cargo || "-"}</td><td>${f.area || "-"}</td>
    <td><span class="badge ${f.ativo ? "on" : "off"}">${f.ativo ? "ativo" : "inativo"}</span></td>
    <td>${f.ativo ? `<button onclick="inativar('${f.id}')">Inativar</button>` : ""}</td>
  </tr>`).join("") || '<tr><td colspan="6">Nenhum registro</td></tr>';
}

function abrirModal() { editId = null; mt.textContent = "Novo funcionário"; form.reset(); modal.style.display = "block"; }
function fecharModal() { modal.style.display = "none"; }

form.onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    nome: f_nome.value, cargo: f_cargo.value || null, area: f_area.value || null,
    supervisor_id: f_sup.value || null, matricula: f_matricula.value || null,
    admissao: f_admissao.value || null, setor: f_setor.value || null,
    desligamento: f_deslig.value || null, jornada_id: f_jornada.value || null,
    em_treinamento: f_trein.checked,
    observacoes: f_obs.value || null,
  };
  await api("/funcionarios", { method: "POST", body: JSON.stringify(body) });
  fecharModal(); carregar();
};

async function inativar(id) {
  if (!confirm("Inativar (exclusão lógica)? Histórico é preservado.")) return;
  await api("/funcionarios/" + id, { method: "DELETE" });
  carregar();
}

carregarJornadas().then(carregar);
