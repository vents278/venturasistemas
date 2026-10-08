# ERP — Estação de Trabalho

ETAPA 2 — Configuração do projeto (scaffold).

## Estrutura

- `backend/` FastAPI modular (routers → services → engine → repositories).
- `frontend/` HTML/CSS/JS puro, desacoplado via REST.
- `supabase/` migrations SQL + seed (ETAPA 3).
- `.env.example` modelo de variáveis (nunca commitar `.env`).

## Como executar (ETAPA 2)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Saúde: http://127.0.0.1:8000/health

## Como testar

```powershell
cd backend
pytest -q
```

## Convenção

Regra de negócio só em `services/` + `engine/`. Router nunca calcula.
Pendência (automática) ≠ Tarefa (manual).
