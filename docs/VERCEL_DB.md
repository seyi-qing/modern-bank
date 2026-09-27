# Fix login 401 on Vercel (persistent database)

## Why you see 401

The API is reachable. Login can return tokens, then `/auth/me` returns **401** because:

- Default DB is **SQLite in `/tmp`**
- Each serverless instance has its **own** empty disk
- Instance A seeds + logs you in; instance B has no user → **401**

## Fix: free Neon Postgres (5 minutes)

1. Go to [neon.tech](https://neon.tech) → sign up → **New project**
2. Copy the connection string (starts with `postgresql://...` or `postgres://...`)
3. Vercel → project **modern-bank-api** → **Settings → Environment Variables**:

```text
DATABASE_URL = postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

(Also keep `SECRET_KEY` and `CORS_ORIGINS` if already set.)

4. **Redeploy** modern-bank-api
5. Hit `/health` once (seed runs on startup)
6. Login again: `demo@modernbank.dev` / `Demo1234!`

## Frontend

Already set:

```text
NEXT_PUBLIC_API_URL=https://modern-bank-api.vercel.app/api/v1
```

Redeploy frontend after any API URL change.

## Verify

```bash
curl -X POST https://modern-bank-api.vercel.app/api/v1/auth/login/json \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@modernbank.dev","password":"Demo1234!"}'
```

Then use the `access_token` on `/api/v1/auth/me` with `Authorization: Bearer …`.
