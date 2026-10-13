/* Sidebar + topbar compartilhados — nav por módulos, empresa ativa, hamburger. */
const NAV = [
  ["dashboard.html", "Dashboard", "📊", "dashboard"],
  ["funcionarios.html", "Funcionários", "👥", "funcionarios"],
  ["jornadas.html", "Jornadas", "🕐", "jornadas"],
  ["presencas.html", "Presença", "✅", "presencas"],
  ["apropriacoes.html", "Apropriação", "🧾", "apropriacoes"],
  ["horas_extras.html", "Horas extras", "⏱️", "horas-extras"],
  ["pendencias.html", "Pendências", "⚠️", "pendencias"],
  ["tarefas.html", "Tarefas", "📌", "tarefas"],
  ["emails.html", "E-mails", "✉️", "emails"],
  ["absenteismo.html", "Absenteísmo", "🏥", "absenteismo"],
  ["relatorios.html", "Relatórios", "📄", "relatorios"],
  ["auditoria.html", "Auditoria", "🔍", "auditoria"],
  ["motor.html", "Motor", "⚙️", "motor"],
  ["ai.html", "Assistente", "🤖", "ai"],
  ["empresas.html", "Empresas", "🏢", "empresas"],
  ["usuarios.html", "Usuários", "🔑", "usuarios"],
];

/* Escopo de empresa: anexa ?empresa_id= a toda chamada de API. */
(function () {
  const orig = window.fetch;
  window.fetch = function (url, opts) {
    if (typeof url === "string") {
      const base = (typeof API_BASE !== "undefined") ? API_BASE : "";
      const emp = sessionStorage.getItem("erp_empresa");
      if (emp && base && url.startsWith(base) && !url.includes("empresa_id=")) {
        url += (url.includes("?") ? "&" : "?") + "empresa_id=" + encodeURIComponent(emp);
      }
    }
    return orig(url, opts);
  };
})();

function tokenEmail() {
  try {
    const t = sessionStorage.getItem("erp_token");
    if (!t) return null;
    const b64 = t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return (JSON.parse(atob(b64)).email) || null;
  } catch { return null; }
}

async function trocarSenha() {
  const atual = prompt("Senha atual:");
  if (!atual) return;
  const nova = prompt("Nova senha (mín. 6 caracteres):");
  if (!nova) return;
  if (nova !== prompt("Confirme a nova senha:")) return alert("Confirmação diferente.");
  const t = sessionStorage.getItem("erp_token");
  const r = await fetch(API_BASE + "/auth/trocar-senha", { method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + t },
    body: JSON.stringify({ senha_atual: atual, nova_senha: nova }) });
  alert(r.ok ? "Senha alterada." : await r.text());
}

function empresaNome(id) {
  try {
    return (JSON.parse(sessionStorage.getItem("erp_empresas") || "[]").find((e) => e.id === id) || {}).nome;
  } catch { return null; }
}

(async function initLayout() {
  const sb = document.getElementById("sidebar");
  if (!sb) return;
  const token = sessionStorage.getItem("erp_token");
  if (!token) { location.href = "login.html"; return; }
  let me = { perfil: "ADMIN", modulos: [] };
  try {
    const r = await fetch(API_BASE + "/auth/me", { headers: { Authorization: "Bearer " + token } });
    if (r.status === 401) { location.href = "login.html"; return; }
    if (r.ok) me = await r.json();
  } catch { /* segue com tudo visível */ }
  const mods = me.modulos || [];
  const pode = (m) => me.perfil === "ADMIN" || !mods.length || mods.includes(m);
  const page = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  sb.innerHTML =
    '<div class="logo">ERP<small>Estação de Trabalho</small></div><nav>' +
    NAV.filter(([, , , m]) => pode(m)).map(([h, l, i]) => `<a href="${h}" class="${h === page ? "active" : ""}"><span>${i}</span>${l}</a>`).join("") +
    `</nav><div class="who">${me.email || tokenEmail() || "usuário"}<br/>` +
    `<small>🏢 ${empresaNome(sessionStorage.getItem("erp_empresa")) || "todas"} · <a href="selecionar-empresa.html" style="color:#93c5fd">trocar</a></small><br/>` +
    `<button onclick="trocarSenha()">🔑 Trocar senha</button><button onclick="sessionStorage.removeItem('erp_token');sessionStorage.removeItem('erp_empresa');location.href='login.html'">Sair</button></div>`;

  const tb = document.getElementById("topbar");
  if (tb && !document.getElementById("hamburger")) {
    const b = document.createElement("button");
    b.id = "hamburger"; b.textContent = "☰"; b.setAttribute("aria-label", "menu");
    b.onclick = () => sb.classList.toggle("open");
    tb.prepend(b);
    const chip = document.createElement("span");
    chip.id = "userchip"; chip.textContent = empresaNome(sessionStorage.getItem("erp_empresa")) || me.perfil || "";
    tb.appendChild(chip);
    document.querySelectorAll("#topbar a").forEach((a) => { a.style.display = "none"; });
  }
  try {
    const re = await fetch(API_BASE + "/empresas", { headers: { Authorization: "Bearer " + token } });
    if (re.ok) sessionStorage.setItem("erp_empresas", JSON.stringify(await re.json()));
  } catch { /*_cache de nomes indisponível */ }
})();
