# ModernBank – Digital Banking Prototype (v1.3)

Educational full-stack banking app: **Next.js** frontend + **FastAPI** backend.

> **Not a bank. Not FDIC.** Demo / learning only. Live funds need licenses + a BaaS/bank program.

## Repo status

Core backend (auth, config, routers, docker) and frontend scaffold are on this branch.
Some larger modules (full models, services, all dashboard pages) may still be landing in follow-up commits.
Full source is also available as `modern-bank.zip` from the original build session.

## Quick start (local)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (other terminal)
cd frontend
npm install
npm run dev
```

- API docs: http://localhost:8000/docs  
- App: http://localhost:3000  
- Demo user: `demo@modernbank.dev` / `Demo1234!`  
- Admin: `admin@modernbank.dev` / `Admin123!`

## Docker

```bash
docker compose up --build
```

## Deploy (Vercel)

1. Import this repo under team **seyi-qing**
2. Root Directory: `frontend`
3. Env: `NEXT_PUBLIC_API_URL` = your API base URL
4. Backend: deploy FastAPI separately (Railway/Render) or second Vercel project + Postgres

## License

MIT — learning and architecture only.
