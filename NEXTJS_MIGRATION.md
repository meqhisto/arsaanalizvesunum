# Next.js Frontend (v1.1.7)

This repository now includes a Next.js frontend under `frontend/` to progressively migrate the UI from Flask templates to a modern React-based app while keeping the existing Flask API.

## Development

1. Start the Flask backend on port 5000 (default):

```bash
python app.py
```

2. Start the Next.js dev server:

```bash
cd frontend
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000. Requests to `/api/*` are proxied to Flask (`API_PROXY_TARGET` in `next.config.ts`).

## Build

```bash
cd frontend
npm run build
npm run start
```

## Dashboard Summary API

- Backend endpoint: `GET /api/v1/dashboard/summary` (requires JWT)
- Provides totals for analyses, contacts, deals, open tasks, plus aggregated portfolio stats
- Next.js dashboard page consumes this via `/api/backend/v1/dashboard/summary`, which refreshes expired access tokens server-side when possible

## Structure

- `frontend/src/app` – Next.js App Router pages
- `frontend/src/app/api/backend/[...path]/route.ts` – Server-side proxy with automatic token refresh
- `frontend/src/lib/api.ts` – Axios client (client-side fetches, cookie/localStorage token helpers)
- `frontend/src/lib/dashboard.ts` – Helper to consume `/api/v1/dashboard/summary`
- `frontend/next.config.ts` – Rewrites `/api/*` to Flask (`API_PROXY_TARGET`)

## Next Steps

- Port login and authenticated flows to Next.js (consume existing JWT/session endpoints)
- Gradually migrate key views (dashboard, CRM, analysis)
- Replace legacy webpack build once feature parity is achieved
