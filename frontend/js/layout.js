/* Sidebar + topbar compartilhados — injeta nav, usuário e hamburger. */
const NAV = [
  ["dashboard.html", "Dashboard", "📊"],
  ["funcionarios.html", "Funcionários", "👥"],
  ["jornadas.html", "Jornadas", "🕐"],
  ["presencas.html", "Presença", "✅"],
  ["apropriacoes.html", "Apropriação", "🧾"],
  ["horas_extras.html", "Horas extras", "⏱️"],
  ["pendencias.html", "Pendências", "⚠️"],
  ["tarefas.html", "Tarefas", "📌"],
  ["emails.html", "E-mails", "✉️"],
  ["absenteismo.html", "Absenteísmo", "🏥"],
  ["relatorios.html", "Relatórios", "📄"],
  ["auditoria.html", "Auditoria", "🔍"],
  ["motor.html", "Motor", "⚙️"],
  ["ai.html", "Assistente", "🤖"],
];

function tokenEmail() {
  try {
    const t = sessionStorage.getItem("erp_token");
    if (!t) return null;
    const b64 = t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return (JSON.parse(atob(b64)).email) || null;
  } catch { return null; }
}

(function initLayout() {
  const sb = document.getElementById("sidebar");
  if (!sb) return;
  if (!sessionStorage.getItem("erp_token")) { location.href = "login.html"; return; }
  const page = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  sb.innerHTML =
    '<div class="logo">ERP<small>Estação de Trabalho</small></div><nav>' +
    NAV.map(([h, l, i]) => `<a href="${h}" class="${h === page ? "active" : ""}"><span>${i}</span>${l}</a>`).join("") +
    `</nav><div class="who">${tokenEmail() || "usuário"}<br/><button onclick="sessionStorage.removeItem('erp_token');location.href='login.html'">Sair</button></div>`;

  const tb = document.getElementById("topbar");
  if (tb && !document.getElementById("hamburger")) {
    const b = document.createElement("button");
    b.id = "hamburger"; b.textContent = "☰"; b.setAttribute("aria-label", "menu");
    b.onclick = () => sb.classList.toggle("open");
    tb.prepend(b);
    const chip = document.createElement("span");
    chip.id = "userchip"; chip.textContent = tokenEmail() || "";
    tb.appendChild(chip);
    document.querySelectorAll("#topbar a").forEach((a) => { a.style.display = "none"; });
  }
})();
