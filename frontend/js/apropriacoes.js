/* Apropriações: OS + apropriar (pesquisa) + consultas + indicadores. */
let OS_SEL = null, ADIC = [], CF_SEL = null, T1 = null;

async function api(path, opts = {}) {
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = sessionStorage.getItem("erp_token");
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { ...opts, headers: h });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}
function debounce(fn, key) {
  clearTimeout(T1);
  T1 = setTimeout(fn, 350);
}
const debounceOS = () => debounce(pesquisarOS);
const debounceFunc = () => debounce(pesquisarFunc);
const debounceCFunc = () => debounce(pesquisarCFunc);

/* ---------- 1. OS ---------- */
async function criarOS() {
  if (!os_num.value.trim()) return alert("Número obrigatório.");
  try {
    OS_SEL = await api("/os", { method: "POST", body: JSON.stringify({ codigo: os_num.value, descricao: os_desc.value || null, data_execucao: os_data.value || null }) });
  } catch (e) { return alert(e.message); }
  os_num.value = ""; os_desc.value = "";
  await refreshOSOptions(); pesquisarOS(); detalheOS();
}
async function refreshOSOptions() {
  const list = await api("/os");
  ap_os.innerHTML = '<option value="">ordem...</option>' + list.map((o) => `<option value="${o.id}" ${OS_SEL && OS_SEL.id === o.id ? "selected" : ""}>${o.codigo}</option>`).join("");
  if (OS_SEL) ap_os.value = OS_SEL.id;
}
async function pesquisarOS() {
  const p = new URLSearchParams();
  if (os_q.value.trim()) p.set("q", os_q.value.trim());
  const list = await api("/os?" + p);
  os_lista.innerHTML = list.slice(0, 20).map((o) => `<div class="res" onclick='selOS(${JSON.stringify(o.id)})'><strong>${o.codigo}</strong> <small>${o.status} · ${o.descricao || ""}</small></div>`).join("") || "Nenhuma OS.";
}
async function selOS(id) {
  OS_SEL = (await api("/os")).find((o) => o.id === id) || { id };
  await refreshOSOptions(); detalheOS();
}
async function detalheOS() {
  if (!OS_SEL) return;
  const p = new URLSearchParams();
  if (os_de.value) p.set("de", os_de.value);
  if (os_ate.value) p.set("ate", os_ate.value);
  const d = await api(`/os/${OS_SEL.id}?` + p);
  if (!d.funcionarios) { os_det.innerHTML = "Sem apropriações no período."; return; }
  os_det.innerHTML = `<p><strong>${d.os.codigo}</strong> — ${d.os.descricao || ""}<br/>
    <small>Situação: ${d.os.status} · Execução: ${d.os.data_execucao || "-"} · Datas: ${(d.datas_execucao || []).join(", ") || "-"}</small></p>
    <p><strong>${d.qtd_funcionarios}</strong> funcionários · HH ${d.resumo.total} (normal ${d.resumo.normais} + extra ${d.resumo.extras})</p>
    <table class="mini"><thead><tr><th>Funcionário</th><th>Cargo</th><th>Normal</th><th>Extra</th><th>Total</th></tr></thead><tbody>` +
    d.funcionarios.map((f) => `<tr><td>${f.nome}</td><td>${f.cargo || "-"}</td><td>${f.normais}</td><td>${f.extra}</td><td>${f.total}</td></tr>`).join("") + "</tbody></table>";
}

/* ---------- 2. Apropriar ---------- */
async function pesquisarFunc() {
  const q = ap_q.value.trim();
  if (q.length < 2) { func_res.innerHTML = "<small>Digite ao menos 2 letras.</small>"; return; }
  const d = await api("/funcionarios?q=" + encodeURIComponent(q) + "&ativo=true&limit=8");
  func_res.innerHTML = d.items.map((f) => `<div class="res"><strong>${f.nome}</strong> <small>${f.matricula} · ${f.cargo || "-"}</small>
    <button onclick='addFunc(${JSON.stringify(f.id)},${JSON.stringify(f.nome)})'>Adicionar</button></div>`).join("") || "Sem resultados.";
}
function addFunc(id, nome) {
  if (ADIC.find((a) => a.id === id)) return alert("Funcionário já adicionado.");
  ADIC.push({ id, nome, horas: "" });
  renderAdic(); previa();
}
function renderAdic() {
  adicionados.innerHTML = ADIC.map((a, i) => `<div class="addrow"><span style="flex:1">${a.nome}</span>
    <input type="number" min="0" max="24" step="0.5" placeholder="h" value="${a.horas}" oninput="ADIC[${i}].horas=this.value;previa()" />
    <button onclick="ADIC.splice(${i},1);renderAdic();previa()">✕</button></div>`).join("") || "<small>Ninguém adicionado.</small>";
}
async function previa() {
  const itens = ADIC.filter((a) => parseFloat(a.horas) > 0);
  if (!itens.length || !ap_data.value) { previa.innerHTML = ""; return; }
  let html = "";
  for (const a of itens) {
    try {
      const s = await api(`/apropriacoes/saldo?funcionario_id=${a.id}&data=${ap_data.value}`);
      const novo = s.total_apropriado + parseFloat(a.horas);
      const norm = Math.min(novo, s.carga_prevista), ext = +(novo - norm).toFixed(2);
      html += `<div>${a.nome}: carga ${s.carga_prevista}h + ${a.horas}h → normal ${norm}h, extra ${ext}h ${ext > 0 ? "☑ contém extras" : ""}</div>`;
    } catch { html += `<div>${a.nome}: (sem carga)</div>`; }
  }
  previa.innerHTML = html;
}
async function salvarApropriacao() {
  if (!ap_os.value) return alert("Selecione a ordem.");
  if (!ap_data.value) return alert("Informe a data.");
  const itens = ADIC.filter((a) => parseFloat(a.horas) > 0).map((a) => ({ funcionario_id: a.id, horas: parseFloat(a.horas) }));
  if (!itens.length) return alert("Informe horas.");
  if (previa.textContent.includes("contém extras") && !confirm("Há horas extras. Confirmar o salvamento?")) return;
  try {
    const r = await api("/apropriacoes/lote-os", { method: "POST", body: JSON.stringify({ data: ap_data.value, os_id: ap_os.value, itens }) });
    alert(`OK: ${r.ok}` + (r.erros.length ? ` | Erros: ${r.erros.map((e) => e.erro).join("; ")}` : ""));
  } catch (e) { return alert(e.message); }
  ADIC = []; renderAdic(); previa();
}

/* ---------- 3. Consulta funcionário ---------- */
async function pesquisarCFunc() {
  const q = cf_q.value.trim();
  if (q.length < 2) { cf_res.innerHTML = ""; return; }
  const d = await api("/funcionarios?q=" + encodeURIComponent(q) + "&ativo=true&limit=8");
  cf_res.innerHTML = d.items.map((f) => `<div class="res" onclick='selCFunc(${JSON.stringify(f.id)})'><strong>${f.nome}</strong> <small>${f.matricula} · ${f.cargo || "-"}</small></div>`).join("");
}
async function selCFunc(id) {
  CF_SEL = (await api("/funcionarios?q=&limit=100")).items.find((f) => f.id === id);
  cf_dados.innerHTML = `<p><strong>${CF_SEL.nome}</strong> <small>${CF_SEL.matricula} · ${CF_SEL.cargo || "-"} · ${CF_SEL.area || "-"}</small></p>`;
  consultaFunc();
}
async function consultaFunc() {
  if (!CF_SEL) return alert("Selecione o funcionário.");
  const p = new URLSearchParams({ funcionario_id: CF_SEL.id });
  if (cf_de.value) p.set("de", cf_de.value);
  if (cf_ate.value) p.set("ate", cf_ate.value);
  if (cf_os.value.trim()) p.set("os_codigo", cf_os.value.trim());
  if (cf_extras.checked) p.set("so_extras", "true");
  const d = await api("/apropriacoes/consulta?" + p);
  cf_table.innerHTML = `<table class="mini"><thead><tr><th>Data</th><th>OS</th><th>Descrição</th><th>Normal</th><th>Extra</th><th>Total</th><th></th></tr></thead><tbody>` +
    d.linhas.map((l) => `<tr><td>${l.data}</td><td>${l.os_codigo}</td><td>${l.descricao || ""}</td><td>${l.normal}</td><td>${l.extra}</td><td>${l.total}</td>
    <td><button onclick="editarAp('${l.id}')">Editar</button> <button onclick="excluirAp('${l.id}')">✕</button></td></tr>`).join("") + "</tbody></table>" +
    `<p><strong>${d.resumo.dias}</strong> dias · <strong>${d.resumo.ordens_distintas}</strong> ordens · Normal ${d.resumo.normais}h · Extra ${d.resumo.extras}h · Total ${d.resumo.total}h · Incompletos: ${d.resumo.dias_incompletos}</p>`;
}
async function editarAp(id) {
  const h = prompt("Novas horas:");
  if (h === null) return;
  await api("/apropriacoes/" + id, { method: "PATCH", body: JSON.stringify({ horas: parseFloat(h) }) });
  consultaFunc();
}
async function excluirAp(id) {
  if (!confirm("Excluir lançamento?")) return;
  await api("/apropriacoes/" + id, { method: "DELETE" });
  consultaFunc();
}

/* ---------- 4. Indicadores ---------- */
async function indicadores() {
  const p = new URLSearchParams();
  if (in_de.value) p.set("de", in_de.value);
  if (in_ate.value) p.set("ate", in_ate.value);
  const [ap, he, pd] = await Promise.all([
    api("/apropriacoes?" + p), api("/horas-extras?" + p),
    api("/pendencias?status=ABERTA"),
  ]);
  const tot = (arr, k) => +arr.reduce((a, x) => a + parseFloat(x[k] || 0), 0).toFixed(2);
  kpis.innerHTML =
    `<div class="kpi"><b>${tot(ap, "horas")}</b>HH apropriado</div>` +
    `<div class="kpi"><b>${tot(he, "qtd_horas")}</b>HE (h)</div>` +
    `<div class="kpi"><b>${pd.filter((x) => x.tipo !== "EMAIL_HE_PENDENTE").length}</b>pend. apropriação</div>` +
    `<div class="kpi"><b>${pd.filter((x) => x.tipo === "EMAIL_HE_PENDENTE").length}</b>e-mails pendentes</div>`;
}

ap_data.valueAsDate = new Date();
refreshOSOptions().then(pesquisarOS);
