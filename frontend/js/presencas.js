/* Grade de presença — célula clicável resolve o dia (presença + obs + ordens). */
let STATUS = [], OSS = [], JORNADAS = [], GRADE = null, CEL = null;
const DW = ["D", "S", "T", "Q", "Q", "S", "S"];

async function api(path, opts = {}) {
  const h = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = sessionStorage.getItem("erp_token");
  if (t) h.Authorization = "Bearer " + t;
  const r = await fetch(API_BASE + path, { ...opts, headers: h });
  if (r.status === 401) { location.href = "login.html"; throw new Error("Não autenticado"); }
  if (!r.ok) throw new Error(await r.text());
  return r.status === 204 ? null : r.json();
}

function mesRange() {
  const [y, m] = mes.value.split("-").map(Number);
  const de = `${mes.value}-01`;
  const fim = new Date(y, m, 0).getDate();
  return { de, ate: `${mes.value}-${String(fim).padStart(2, "0")}` };
}
function mudarMes(d) {
  const [y, m] = mes.value.split("-").map(Number);
  const dt = new Date(y, m - 1 + d, 1);
  mes.value = `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}`;
  carregar();
}

async function carregar() {
  if (!STATUS.length) STATUS = await api("/presencas/status-presenca");
  if (!OSS.length) {
    OSS = await api("/os");
    JORNADAS = await api("/jornadas");
    const FUNC = await api("/funcionarios?ativo=true&limit=100");
    const supIds = [...new Set(FUNC.items.map((f) => f.supervisor_id).filter(Boolean))];
    sup.innerHTML = '<option value="">supervisor: todos</option>' + supIds.map((id) => {
      const s = FUNC.items.find((f) => f.id === id);
      return `<option value="${id}">${s ? s.nome : id}</option>`;
    }).join("");
  }
  const { de, ate } = mesRange();
  const p = new URLSearchParams({ de, ate });
  if (q.value) p.set("q", q.value);
  if (area.value) p.set("area", area.value);
  if (sup.value) p.set("supervisor_id", sup.value);
  if (setor.value) p.set("setor", setor.value);
  GRADE = await api("/presencas/grade?" + p);
  const dias = GRADE.dias;
  gh.innerHTML = `<tr><th class="sticky">Funcionário</th>` + dias.map((d) => {
    const dt = new Date(d + "T12:00:00"), wk = dt.getDay() === 0 || dt.getDay() === 6;
    return `<th class="${wk ? "wknd" : ""}">${String(dt.getDate()).padStart(2, "0")}<br/>${DW[dt.getDay()]}</th>`;
  }).join("") + "</tr>";
  gb.innerHTML = GRADE.linhas.map((l) => `<tr><td class="sticky"><strong>${l.funcionario.nome}</strong><br/><small style="color:var(--muted)">${l.funcionario.matricula || ""} · ${l.funcionario.setor || "-"}</small></td>` +
    dias.map((d) => {
      const c = l.dias[d];
      const inner = c && c.status
        ? `<div class="cel ${c.status}">${c.status.slice(0, 4)}<small>${c.total || ""}${c.total ? "h" : ""}</small></div>`
        : `<div class="cel vazia">+</div>`;
      return `<td><div onclick='abrirDia(${JSON.stringify(l.funcionario.id)},${JSON.stringify(d)})'>${inner}</div></td>`;
    }).join("") + "</tr>").join("");
}

async function abrirDia(fid, data) {
  const lin = GRADE.linhas.find((l) => l.funcionario.id === fid);
  const c = (lin.dias[data]) || { status: "PRESENTE", obs: "", jornada_id: lin.funcionario.jornada_id, apropriacoes: [] };
  CEL = { fid, data, nome: lin.funcionario.nome };
  mt.textContent = `${lin.funcionario.nome} — ${data.split("-").reverse().join("/")}`;
  f_status.innerHTML = STATUS.map((s) => `<option value="${s.codigo}" ${c.status === s.codigo ? "selected" : ""}>${s.codigo}</option>`).join("");
  f_jornada_dia.innerHTML = '<option value="">padrão do funcionário</option>' + JORNADAS.map((j) => `<option value="${j.id}" ${c.jornada_id === j.id ? "selected" : ""}>${j.codigo}</option>`).join("");
  f_obs.value = c.obs || "";
  linhas.innerHTML = "";
  (c.apropriacoes || []).forEach((a) => addLinha(a.os_id, a.horas));
  if (!c.apropriacoes || !c.apropriacoes.length) addLinha();
  await atualizarSaldo();
  modal.style.display = "block";
}
function fecharModal() { modal.style.display = "none"; }

function addLinha(osId, horas) {
  const div = document.createElement("div");
  div.className = "lrow";
  div.innerHTML = `<select>${OSS.map((o) => `<option value="${o.id}" ${o.id === osId ? "selected" : ""}>${o.codigo}</option>`).join("")}</select>
    <input type="number" min="0" max="24" step="0.5" placeholder="h" value="${horas || ""}" />
    <button type="button" onclick="this.parentElement.remove();atualizarSaldo()">✕</button>`;
  div.querySelector("input").oninput = atualizarSaldo;
  linhas.appendChild(div);
}
function lerLinhas() {
  return [...linhas.querySelectorAll(".lrow")].map((r) => ({
    os_id: r.querySelector("select").value, horas: parseFloat(r.querySelector("input").value) || 0,
  })).filter((x) => x.horas > 0);
}
async function atualizarSaldo() {
  try {
    const s = await api(`/apropriacoes/saldo?funcionario_id=${CEL.fid}&data=${CEL.data}`);
    const t = lerLinhas().reduce((a, x) => a + x.horas, 0);
    saldo.textContent = `Carga: ${s.carga_prevista}h | Lançado: ${s.total_apropriado}h | Nesta edição: ${t}h`;
  } catch { saldo.textContent = ""; }
}

form.onsubmit = async (e) => {
  e.preventDefault();
  await api("/presencas", { method: "POST", body: JSON.stringify({ funcionario_id: CEL.fid, data: CEL.data, status_codigo: f_status.value, jornada_id: f_jornada_dia.value || null, obs: f_obs.value || null }) });
  const itens = lerLinhas();
  if (itens.length) await api("/apropriacoes/lote", { method: "POST", body: JSON.stringify({ funcionario_id: CEL.fid, data: CEL.data, itens }) });
  fecharModal(); carregar();
};

async function gerarDia() {
  if (!dia.value) return alert("Escolha a data.");
  const r = await api("/presencas/lancamento-diario", { method: "POST", body: JSON.stringify({ data: dia.value }) });
  alert(`Presenças: ${r.presentes} | Treinamento auto: ${r.treinamento} | Já existiam: ${r.ja_existiam}`);
  carregar();
}

mes.value = new Date().toISOString().slice(0, 7);
carregar();
