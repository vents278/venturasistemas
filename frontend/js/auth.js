/* Auth no frontend — ETAPA 4. Token em sessionStorage (não localStorage). */
const Auth = {
  get token() { return sessionStorage.getItem("erp_token"); },
  logout() { sessionStorage.removeItem("erp_token"); location.href = "login.html"; },
  async login(email, senha) {
    const r = await fetch(API_BASE + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    if (!r.ok) throw new Error("Login inválido (" + r.status + ")");
    const data = await r.json();
    sessionStorage.setItem("erp_token", data.access_token);
    return data;
  },
  async me() {
    return apiGet("/auth/me");
  },
};
