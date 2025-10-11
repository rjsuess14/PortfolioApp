# Portfolio App

A full-stack stock portfolio monitoring application built with SvelteKit, FastAPI, and Supabase.

## Features

- Track stock holdings, account performance, and portfolio value
- Connect brokerage accounts via Plaid (investments)
- AI summaries of filings/news via Claude
- Supabase Auth + RLS-secured database access
- Modern, responsive UI with TailwindCSS

## Tech Stack

- Frontend: SvelteKit + TailwindCSS
- Backend: FastAPI (Python)
- Database & Auth: Supabase (PostgreSQL + Auth)
- Account Integration: Plaid API
- AI Summaries: Claude API

## Monorepo Structure

```
PortfolioApp/
├── backend/                # FastAPI backend
│   └── database_schema.sql # Canonical DB schema (Supabase)
├── frontend/               # SvelteKit frontend
└── CLAUDE.md               # Detailed guidelines
```

Note: `backend/create_tables.sql` has been removed. Use `backend/database_schema.sql` as the single source of truth for the database schema and RLS policies.

## Setup

Prerequisites
- Node.js 18+
- Python 3.11+ and `uv`
- Supabase project (URL + anon key)
- Claude API key

Environment Variables

Backend (`backend/.env`)
```
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
CLAUDE_API_KEY=your-claude-api-key
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENV=sandbox
```

Frontend (`frontend/.env.local`)
```
PUBLIC_SUPABASE_URL=your-supabase-url
PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
PUBLIC_API_BASE_URL=http://localhost:8000
```

Install & Run (dev)
```
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && uv sync && uv run dev
```

## Routes

Frontend (SvelteKit)
- `/login` and `/signup` under `src/routes/(auth)`
- `/dashboard` under `src/routes/(app)`

Backend (FastAPI, prefix `/api/v1`)
- `POST /auth/login`, `POST /auth/register`, `POST /auth/logout`
- `GET /portfolio` returns accounts with nested holdings for the current user
- `GET /portfolio/accounts` returns accounts only
- `POST /plaid/link-token` creates a Plaid Link token
- `POST /plaid/exchange-token` exchanges the public token and stores an encrypted access token
- `GET /plaid/accounts` fetches from Plaid and persists accounts/holdings (used by frontend refresh)

Authorization
- All protected endpoints require `Authorization: Bearer <supabase_access_token>`
- RLS is enforced; the backend attaches the caller’s JWT to Supabase for inserts/selects

## Data Model

Canonical schema: `backend/database_schema.sql`

Key tables
- `portfolio_accounts(id, user_id, account_name, account_type, total_value, plaid_account_id, created_at, updated_at)`
- `holdings(id, account_id, symbol, shares, avg_cost, current_price, total_value, gain_loss, security_name, created_at, updated_at)`
- `plaid_access_tokens(id, user_id, item_id, access_token_encrypted, created_at, updated_at)`

RLS policies restrict all tables to the authenticated user (`auth.uid()`), so requests must carry a valid Supabase JWT.

## Plaid Sync

- Use `GET /api/v1/plaid/accounts` to fetch from Plaid and persist `portfolio_accounts` and `holdings`.
- The frontend “Refresh” action calls this endpoint before loading the portfolio.

## Housekeeping / Cleanup

- Removed unused folders: `backend/src/app/api/auth/`, `backend/src/app/models/`
- Removed duplicate/empty route trees: `frontend/src/routes/app/`, `frontend/src/routes/auth/`, and `frontend/src/routes/(app)/{dashboard}`
- Dropped unused frontend deps: `plaid`, `react-plaid-link` (Plaid Link is loaded via CDN in `PlaidLink.svelte`)
- Removed `backend/test_api.py` (use pytest suite in `backend/tests/`)
Refer to `CLAUDE.md` for deeper design docs and development conventions.
