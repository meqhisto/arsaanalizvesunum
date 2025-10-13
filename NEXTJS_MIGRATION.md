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

## Structure

- `frontend/src/app` – Next.js App Router pages
- `frontend/src/lib/api.ts` – Axios client (uses `NEXT_PUBLIC_API_BASE_URL`, defaults to `/api`)
- `frontend/next.config.ts` – Rewrites `/api/*` to Flask (`API_PROXY_TARGET`)

## Next Steps

- Port login and authenticated flows to Next.js (consume existing JWT/session endpoints)
- Gradually migrate key views (dashboard, CRM, analysis)
- Replace legacy webpack build once feature parity is achieved

