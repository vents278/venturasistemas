/* Programação de preventivas — cadastro, funcionários programados e checklist de OS. */
let LISTA = [], DET = null, OS_ABERTA = {}, T_FADD = null, EDIT_ID = null, FUNCS = [];

const ST_LABEL = {
  PROGRAMADA: "Programada", EM_ANDAMENTO: "Em andamento", AGUARDANDO_OS: "Aguardando OS",
  PARCIALMENTE_CONCLUIDA: "Parcialmente concluída", CONCLUIDA: "Concluída", CANCELADA: "Cancelada",
};
const SIT_LABEL = {
  NAO_PROGRAMADO: "Não programado", PROGRAMADO: "Programado", NAO_COMPARECEU: "Não compareceu",
  AGUARDANDO_OS: "Aguardando lançamento de OS", OS_PENDENTE: "OS pendente",
  PARCIALMENTE_REGULARIZADO: "Parcialmente regularizado", REGULARIZADO: "Regularizado",
};

async function api(path, opts = {}) {
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = sessionStorage.getItem("erp_token");
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { ...opts, headers: h });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmtData = (d) => (d ? d.split("-").reverse().join("/") : "-");
const fmtHora = (t) => (t ? String(t).slice(0, 5) : "-");

function filtros() {
  const p = new URLSearchParams();
  if (de.value) p.set("de", de.value);
  if (ate.value) p.set("ate", ate.value);
  if (area.value.trim()) p.set("area", area.value.trim());
  if (fstatus.value) p.set("status", fstatus.value);
  if (funcionario.value.trim()) p.set("funcionario", funcionario.value.trim());
  if (cargo.value.trim()) p.set("cargo", cargo.value.trim());
  if (os_codigo.value.trim()) p.set("os_codigo", os_codigo.value.trim());
  if (situacao.value) p.set("situacao", situacao.value);
  return p;
}

async function carregar() {
  const p = filtros();
  const [lista, ind] = await Promise.all([
    api("/preventivas?" + p), api("/preventivas/indicadores?" + p),
  ]);
  LISTA = lista;
  renderCards(ind);
  renderTabela(lista);
}

function renderCards(i) {
  const cards = [
    ["Total preventivas", i.total_preventivas], ["Em andamento", i.em_andamento],
    ["Aguardando OS", i.aguardando_os], ["Funcionários programados", i.funcionarios_programados],
    ["Compareceram", i.funcionarios_compareceram], ["OS cadastradas", i.os_total],
    ["OS recebidas", i.os_recebidas], ["OS pendentes", i.os_pendentes],
  ];
  document.getElementById("cards").innerHTML = cards
    .map(([l, v]) => `<div class="card"><span>${l}</span><b>${v}</b></div>`).join("");
}

function renderTabela(l) {
  tb.innerHTML = l.map((p) => {
    const pend = p.os_pendentes > 0 ? `<span class="badge-pend">${p.os_pendentes}</span>` : `<span class="badge-ok">0</span>`;
    return `<tr>
      <td>${fmtData(p.data)}</td>
      <td>${esc(p.area)}</td>
      <td><strong>${esc(p.descricao)}</strong>${p.equipamento ? `<br/><small class="muted">${esc(p.equipamento)}</small>` : ""}<br/><small class="muted">${fmtHora(p.hora_inicio)}–${fmtHora(p.hora_fim)}</small></td>
      <td>${p.programados}</td>
      <td>${p.presentes}</td>
      <td>${pend}</td>
      <td><span class="st st-${p.status}">${ST_LABEL[p.status] || p.status}</span></td>
      <td><button onclick='abrirDetalhe(${JSON.stringify(p.id)})'>Abrir</button> <button onclick='abrirEditar(${JSON.stringify(p.id)})'>Editar</button></td>
    </tr>`;
  }).join("") || '<tr><td colspan="8">Nenhuma preventiva no filtro.</td></tr>';
}

/* ---------- cadastro (cabeçalho) ---------- */
async function carregarFuncionarios() {
  try {
    const r = await api("/funcionarios?ativo=true&limit=100");
    FUNCS = r.items || [];
    p_resp.innerHTML = '<option value="">-</option>' + FUNCS.map((f) => `<option value="${f.id}">${esc(f.nome)}</option>`).join("");
  } catch { /* sem acesso */ }
}

function abrirNova() {
  EDIT_ID = null;
  form.reset();
  p_status.value = "PROGRAMADA";
  p_data.value = new Date().toISOString().slice(0, 10);
  document.getElementById("modalTitle").textContent = "Nova preventiva";
  modal.style.display = "block";
}

function abrirEditar(id) {
  const p = LISTA.find((x) => x.id === id);
  if (!p) return;
  EDIT_ID = id;
  p_data.value = p.data || ""; p_area.value = p.area || ""; p_equip.value = p.equipamento || "";
  p_desc.value = p.descricao || ""; p_obs.value = p.observacoes || "";
  p_ini.value = (p.hora_inicio || "").slice(0, 5); p_fim.value = (p.hora_fim || "").slice(0, 5);
  p_status.value = p.status || "PROGRAMADA"; p_resp.value = p.responsavel_id || "";
  document.getElementById("modalTitle").textContent = "Editar preventiva";
  modal.style.display = "block";
}

function fecharModal() { modal.style.display = "none"; }

form.onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    data: p_data.value, area: p_area.value.trim(), equipamento: p_equip.value.trim() || null,
    descricao: p_desc.value.trim(), observacoes: p_obs.value.trim() || null,
    hora_inicio: p_ini.value || null, hora_fim: p_fim.value || null,
    status: p_status.value, responsavel_id: p_resp.value || null,
  };
  try {
    if (EDIT_ID) await api("/preventivas/" + EDIT_ID, { method: "PATCH", body: JSON.stringify(body) });
    else await api("/preventivas", { method: "POST", body: JSON.stringify(body) });
  } catch (err) { return alert(err.message); }
  fecharModal(); carregar();
};

/* ---------- detalhe + checklist ---------- */
async function abrirDetalhe(id) {
  DET = await api("/preventivas/" + id);
  OS_ABERTA = {};
  renderDetalhe();
  det.style.display = "block";
}
function fecharDet() { det.style.display = "none"; }
function recarregarDetalhe(d) { DET = d; renderDetalhe(); carregar(); }

function renderDetalhe() {
  const p = DET.preventiva, ag = DET.agregados;
  const stalePend = ag.os_pendentes > 0 || ag.funcionarios_pendentes > 0;
  detBody.innerHTML = `
    <div class="dethead">
      <div class="info">
        <h2>${esc(p.descricao)}</h2>
        <small>${fmtData(p.data)} · Área: ${esc(p.area)} ${p.equipamento ? "· " + esc(p.equipamento) : ""} ·
          ${fmtHora(p.hora_inicio)}–${fmtHora(p.hora_fim)} · Responsável: ${esc(p.responsavel_nome || "-")}</small>
        <div style="margin-top:6px"><span class="st st-${p.status_calc}">${ST_LABEL[p.status_calc] || p.status_calc}</span></div>
      </div>
      <div style="text-align:right">
        <div class="muted">Programados ${ag.programados} · Presentes ${ag.presentes}</div>
        <div style="margin:4px 0">${ag.os_pendentes > 0
          ? `<span class="badge-pend">${ag.os_pendentes} OS pendente(s)</span>`
          : `<span class="badge-ok">OS regularizadas</span>`}</div>
        <button onclick="fecharDet()">Fechar</button>
      </div>
    </div>
    ${p.observacoes ? `<p class="muted">${esc(p.observacoes)}</p>` : ""}
    ${stalePend ? "" : `<p class="badge-ok">Todos os funcionários regularizados.</p>`}

    <div class="sec">
      <h3>Funcionários Programados</h3>
      <div class="bar">
        <input id="f_add_q" placeholder="pesquisar funcionário (nome/matrícula)..." oninput="debounceAdd()" style="flex:1" />
      </div>
      <div id="f_add_res"></div>
      <div class="tablewrap">
        <table class="mini">
          <thead><tr><th>Funcionário</th><th>Matrícula</th><th>Cargo</th><th>Programado</th><th>Compareceu</th><th>OS recebida</th><th>Nº OS</th><th>Status</th><th>Ações</th></tr></thead>
          <tbody>${DET.funcionarios.map(renderLinhaFunc).join("") || '<tr><td colspan="9">Nenhum funcionário programado.</td></tr>'}</tbody>
        </table>
      </div>
    </div>`;
}

function renderLinhaFunc(l) {
  const f = l.funcionario;
  const aberta = !!OS_ABERTA[l.id];
  return `<tr>
    <td><strong>${esc(f.nome)}</strong><br/><small class="muted">${esc(f.escala || "-")}</small></td>
    <td>${esc(f.matricula || "-")}</td>
    <td>${esc(f.cargo || "-")}</td>
    <td><input type="checkbox" style="width:auto" ${l.programado ? "checked" : ""} onchange='setCheck(${JSON.stringify(l.id)},"programado",this.checked)' /></td>
    <td><input type="checkbox" style="width:auto" ${l.compareceu ? "checked" : ""} onchange='setCheck(${JSON.stringify(l.id)},"compareceu",this.checked)' /></td>
    <td><input type="checkbox" style="width:auto" disabled ${l.os_recebida_geral ? "checked" : ""} title="Marcado apenas quando todas as OS estão recebidas" /></td>
    <td>${l.os_recebidas}/${l.os_total}</td>
    <td><span class="sit sit-${l.status}">${SIT_LABEL[l.status] || l.status}</span></td>
    <td>
      <button onclick='toggleOS(${JSON.stringify(l.id)})'>${aberta ? "Ocultar OS" : "Gerenciar OS"}</button>
      <button class="btn-danger" onclick='removerFunc(${JSON.stringify(l.id)})'>Remover</button>
    </td>
  </tr>
  ${aberta ? `<tr><td colspan="9">${renderOS(l)}</td></tr>` : ""}`;
}

function renderOS(l) {
  const fid = l.id;
  const rowOS = (o) => `<div class="osline" id="osrow-${o.id}">
    <input value="${esc(o.os_codigo)}" data-f="os_codigo" />
    <input value="${esc(o.descricao || "")}" placeholder="descrição" data-f="descricao" />
    <input type="date" value="${o.data_execucao || ""}" data-f="data_execucao" />
    <input type="number" min="0" max="24" step="0.5" value="${o.horas}" data-f="horas" />
    <label style="display:flex;gap:4px;align-items:center;font-size:.75rem">
      <input type="checkbox" style="width:auto" ${o.recebida ? "checked" : ""} onchange='toggleOSRecebida(${JSON.stringify(fid)},${JSON.stringify(o.id)},this.checked)' /> recebida
    </label>
    <span>
      <button onclick='salvarOS(${JSON.stringify(fid)},${JSON.stringify(o.id)})'>Salvar</button>
      <button class="btn-danger" onclick='removerOS(${JSON.stringify(fid)},${JSON.stringify(o.id)})'>✕</button>
    </span>
    <small class="muted" style="grid-column:1/-1">${o.recebida ? "Recebida em " + fmtData(o.data_recebimento) : "Aguardando recebimento"}${o.os_id ? " · vinculada ao ERP" : " · sem vínculo no cadastro"}</small>
  </div>`;
  const confirmado = l.os_completa;
  return `<div class="oswrap">
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
      <strong>Horários</strong>
      <label class="muted">Prev. <input type="time" id="hp1-${fid}" value="${(l.hora_prev_inicio || "").slice(0, 5)}" /></label>
      <label class="muted"><input type="time" id="hp2-${fid}" value="${(l.hora_prev_fim || "").slice(0, 5)}" /></label>
      <label class="muted">Efet. <input type="time" id="he1-${fid}" value="${(l.hora_efet_inicio || "").slice(0, 5)}" /></label>
      <label class="muted"><input type="time" id="he2-${fid}" value="${(l.hora_efet_fim || "").slice(0, 5)}" /></label>
      <button onclick='salvarHorarios(${JSON.stringify(fid)})'>Salvar horários</button>
    </div>
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px">
      <label style="font-size:.8rem"><input type="checkbox" style="width:auto" ${confirmado ? "checked" : ""} onchange='setCheck(${JSON.stringify(fid)},"os_completa",this.checked)' /> Lançamento de OS confirmado como completo</label>
      ${confirmado ? '<span class="badge-ok">confirmado</span>' : '<span class="badge-pend">pendente de confirmação</span>'}
    </div>
    <h4 style="margin:6px 0;font-size:.82rem">Ordens de Serviço (${l.os_total})</h4>
    ${l.os.map(rowOS).join("") || '<p class="muted">Nenhuma OS lançada.</p>'}
    <div class="osline" style="margin-top:8px">
      <input id="ncod-${fid}" placeholder="nº OS" />
      <input id="ndesc-${fid}" placeholder="descrição" />
      <input id="ndata-${fid}" type="date" />
      <input id="nhrs-${fid}" type="number" min="0" max="24" step="0.5" placeholder="h" />
      <label style="display:flex;gap:4px;align-items:center;font-size:.75rem"><input type="checkbox" style="width:auto" id="nrec-${fid}" /> recebida</label>
      <button class="btn-primary" onclick='adicionarOS(${JSON.stringify(fid)})'>+ Adicionar OS</button>
    </div>
  </div>`;
}

function toggleOS(pfid) { OS_ABERTA[pfid] = !OS_ABERTA[pfid]; renderDetalhe(); }

async function setCheck(pfid, campo, valor) {
  const body = {}; body[campo] = valor;
  try { recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios/${pfid}`, { method: "PATCH", body: JSON.stringify(body) })); }
  catch (e) { alert(e.message); }
}

async function salvarHorarios(pfid) {
  const body = {
    hora_prev_inicio: document.getElementById("hp1-" + pfid).value || null,
    hora_prev_fim: document.getElementById("hp2-" + pfid).value || null,
    hora_efet_inicio: document.getElementById("he1-" + pfid).value || null,
    hora_efet_fim: document.getElementById("he2-" + pfid).value || null,
  };
  try { recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios/${pfid}`, { method: "PATCH", body: JSON.stringify(body) })); }
  catch (e) { alert(e.message); }
}

async function removerFunc(pfid) {
  if (!confirm("Remover funcionário da programação? As OS lançadas também serão removidas.")) return;
  try { recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios/${pfid}`, { method: "DELETE" })); }
  catch (e) { alert(e.message); }
}

/* ---------- OS ---------- */
async function adicionarOS(pfid) {
  const codigo = document.getElementById("ncod-" + pfid).value.trim();
  if (!codigo) return alert("Informe o número da OS.");
  const body = {
    os_codigo: codigo,
    descricao: document.getElementById("ndesc-" + pfid).value.trim() || null,
    data_execucao: document.getElementById("ndata-" + pfid).value || null,
    horas: parseFloat(document.getElementById("nhrs-" + pfid).value) || 0,
    recebida: document.getElementById("nrec-" + pfid).checked,
  };
  try { recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios/${pfid}/os`, { method: "POST", body: JSON.stringify(body) })); }
  catch (e) { alert(e.message); }
}

function _lerOSRow(osrowId) {
  const row = document.getElementById("osrow-" + osrowId);
  const v = (f) => row.querySelector(`[data-f="${f}"]`).value;
  return { os_codigo: v("os_codigo").trim(), descricao: v("descricao").trim() || null,
           data_execucao: v("data_execucao") || null, horas: parseFloat(v("horas")) || 0 };
}
async function salvarOS(pfid, osrowId) {
  try { recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios/${pfid}/os/${osrowId}`, { method: "PATCH", body: JSON.stringify(_lerOSRow(osrowId)) })); }
  catch (e) { alert(e.message); }
}
async function toggleOSRecebida(pfid, osrowId, valor) {
  try { recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios/${pfid}/os/${osrowId}`, { method: "PATCH", body: JSON.stringify({ recebida: valor }) })); }
  catch (e) { alert(e.message); }
}
async function removerOS(pfid, osrowId) {
  if (!confirm("Remover esta OS?")) return;
  try { recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios/${pfid}/os/${osrowId}`, { method: "DELETE" })); }
  catch (e) { alert(e.message); }
}

/* ---------- busca de funcionários para adicionar ---------- */
function debounceAdd() { clearTimeout(T_FADD); T_FADD = setTimeout(buscarFunc, 350); }
async function buscarFunc() {
  const termo = document.getElementById("f_add_q").value.trim();
  const box = document.getElementById("f_add_res");
  if (termo.length < 2) { box.innerHTML = ""; return; }
  let list = [];
  try { list = (await api("/funcionarios?ativo=true&limit=20&q=" + encodeURIComponent(termo))).items || []; } catch { /* ignore */ }
  box.innerHTML = list.map((f) => `<div class="res"><strong>${esc(f.nome)}</strong>
     <small class="muted">${esc(f.matricula || "")} · ${esc(f.cargo || "")}</small>
     <button style="margin-left:auto" onclick='addFunc(${JSON.stringify(f.id)})'>Adicionar</button></div>`).join("")
     || '<div class="res muted">Nenhum funcionário encontrado.</div>';
}
async function addFunc(fid) {
  try {
    recarregarDetalhe(await api(`/preventivas/${DET.preventiva.id}/funcionarios`, { method: "POST", body: JSON.stringify({ funcionario_id: fid }) }));
    document.getElementById("f_add_res").innerHTML = "";
    document.getElementById("f_add_q").value = "";
  } catch (e) { alert(e.message); }
}

/* ---------- relatórios ---------- */
function baixarRelatorio() {
  const p = new URLSearchParams();
  if (de.value) p.set("de", de.value); if (ate.value) p.set("ate", ate.value);
  if (area.value.trim()) p.set("area", area.value.trim());
  if (fstatus.value) p.set("status", fstatus.value);
  if (cargo.value.trim()) p.set("cargo", cargo.value.trim());
  if (os_codigo.value.trim()) p.set("os_codigo", os_codigo.value.trim());
  if (situacao.value) p.set("situacao", situacao.value);
  const t = sessionStorage.getItem("erp_token");
  fetch(`${API_BASE}/relatorios/${rel_tipo.value}.${rel_formato.value}?` + p, { headers: t ? { Authorization: "Bearer " + t } : {} })
    .then(async (r) => {
      if (!r.ok) return alert("Falha: " + (await r.text()));
      const blob = await r.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = `${rel_tipo.value}.${rel_formato.value}`; a.click();
    });
}

carregarFuncionarios()
  .then(carregar)
  .catch((e) => { tb.innerHTML = `<tr><td colspan="8">Erro ao carregar: ${esc(e.message)}</td></tr>`; });
