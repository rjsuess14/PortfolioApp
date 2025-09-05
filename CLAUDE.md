# CLAUDE.md

## 📌 Project Overview

This is a full-stack stock portfolio monitoring application that allows users to:

- Track stock holdings, account performance and portfolio value
- View summaries of financial news and regulatory filings
- Authenticate securely with Supabase
- Access a responsive, modern frontend built with SvelteKit and TailwindCSS
- Interact with backend APIs built with FastAPI
- Connect brokerage and bank accounts via Plaid to retrieve holdings, balances, and investment details

## 🧱 Tech Stack

- **Frontend**: SvelteKit + TailwindCSS
- **Backend**: FastAPI (Python)
- **Database & Auth**: Supabase (PostgreSQL + Auth)
- **Account Connectivity**: Plaid API
- **AI**: Claude API for summarizing financial documents
- **Deployment**: Vercel (frontend), Render or Fly.io (backend)

## 🔧 Environment Setup

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.11+ and uv
- Supabase account and project
- Claude API key

### Initial Setup Commands
```bash
# Frontend
cd frontend && npm install
npm run dev

# Backend
cd backend && uv sync
uv run dev
```

### Environment Variables
```env
# Backend (.env)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
CLAUDE_API_KEY=your-claude-api-key
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENV=sandbox

# Frontend (.env.local)
PUBLIC_SUPABASE_URL=your-supabase-url
PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🧭 Design Sources

- Wireframes: https://www.figma.com/design/T0I4lLzY9ZDfM1JJEKY9zP/PortfolioApp?m=auto&t=LCtYAdZd898m55lu-6
- Core Screens:
  - Login: email and password, with a link to sign-up
  - Sign-Up: email and password, with a link to login
  - Dashboard: show the total value of the portfolio, total account value over time, the value of each linked account, and all current holdings.

## 🔀 Routing Conventions

### Frontend Routes

| Path              | Description                                    |
|-------------------|------------------------------------------------|
| `/login`          | User login                                     |
| `/signup`         | User sign-up                                   |
| `/dashboard`      | Portfolio overview, charts, accounts, holdings |

### Backend Endpoints

| Route                            | Method | Purpose                                     | Auth Required |
|----------------------------------|--------|---------------------------------------------|---------------|
| `/api/v1/auth/login`             | POST   | Handles user login via Supabase             | No            |
| `/api/v1/auth/register`          | POST   | Handles user registration                   | No            |
| `/api/v1/auth/logout`            | POST   | Handles user logout                         | Yes           |
| `/api/v1/portfolio`              | GET    | Returns user holdings and account values    | Yes           |
| `/api/v1/portfolio/accounts`     | GET    | Returns linked brokerage accounts           | Yes           |
| `/api/v1/portfolio/accounts`     | POST   | Links new brokerage account                 | Yes           |
| `/api/v1/investment/{symbol}`    | GET    | Returns specific stock metrics              | Yes           |
| `/api/v1/summary/{symbol}`       | GET    | Returns AI-generated summary                | Yes           |
| `/api/v1/news/{symbol}`          | GET    | Returns financial news for symbol           | Yes           |
| `/api/v1/plaid/link-token`       | POST   | Creates a Plaid link token for frontend use | Yes           |
| `/api/v1/plaid/exchange-token`   | POST   | Exchanges public token for access token     | Yes           |
| `/api/v1/plaid/accounts`         | GET    | Retrieves account and investment data       | Yes           |

## 🧑‍💻 Development Guidelines

### Frontend

- Use idiomatic SvelteKit conventions: `+page.svelte`, `+layout.svelte`, `+page.ts`.
- All styling must use TailwindCSS (utility-first CSS).
- Use shadcn-svelte for components.
- Fetch data using `load()` or `form actions`.
- Create reusable components under `src/lib/components/`.
  - Follow atomic design where possible: base, compound, and page-level components
  - Organize UI primitives (e.g. shadcn components) under `src/lib/components/ui/`

### Backend

- Set up a virtual environment and manage dependencies with uv.
- Use FastAPI with versioned routes (`/api/v1/...`)
- Validate inputs and outputs with Pydantic models.
- use 'ty' for type checking.
- Organize logic into `api/`, `models/`, `schemas/`, and `services/`.
- Use Supabase client (e.g. `supabase-py`) for auth and database access.

### Testing

- Backend: Use `pytest`
- Frontend: Use `Playwright` or `Vitest` for page-level tests
- Include test files in `backend/tests/` or `frontend/tests/`

## 📊 Data Models

### Database Schema (Supabase)
```sql
-- Users (handled by Supabase Auth)
-- profiles table extends auth.users

-- Portfolio Accounts
CREATE TABLE portfolio_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  account_name TEXT NOT NULL,
  account_type TEXT NOT NULL, -- 'brokerage', 'ira', '401k'
  total_value DECIMAL NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Holdings
CREATE TABLE holdings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID REFERENCES portfolio_accounts(id),
  symbol TEXT NOT NULL,
  shares DECIMAL NOT NULL,
  avg_cost DECIMAL NOT NULL,
  current_price DECIMAL NOT NULL,
  total_value DECIMAL NOT NULL,
  gain_loss DECIMAL NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Pydantic Models
```python
# schemas/portfolio.py
from decimal import Decimal
from typing import List
from uuid import UUID
from pydantic import BaseModel

class Holding(BaseModel):
    symbol: str
    shares: Decimal
    avg_cost: Decimal
    current_price: float
    total_value: float
    gain_loss: float

class PortfolioAccount(BaseModel):
    id: UUID
    account_name: str
    account_type: str
    total_value: float
    holdings: List[Holding]
```

## 🧩 Plaid Integration

This project uses [Plaid](https://plaid.com/docs/) to connect users' financial accounts and retrieve investment-related data.

### Features
- Generate a Plaid Link token to launch the account linking flow.
- Exchange a public token for a permanent access token securely via backend.
- Fetch account metadata, balances, and investment positions from Plaid.

### Relevant Plaid API Endpoints
- [`/link/token/create`](https://plaid.com/docs/api/tokens/#linktokencreate) — to generate a new link token for the frontend.
- [`/item/public_token/exchange`](https://plaid.com/docs/api/items/#itempublic_tokenexchange) — to exchange the public token after linking.
- [`/investments/holdings/get`](https://plaid.com/docs/api/products/investments/#investmentsholdingsget) — to retrieve holdings like stocks, ETFs, mutual funds.
- [`/accounts/get`](https://plaid.com/docs/api/accounts/#accountsget) — to retrieve account and balance data.

### Security
- Access tokens are stored securely on the server and never exposed to the frontend.
- All Plaid requests are authenticated and scoped per user.
- Sensitive data is encrypted at rest and in transit.

## 🧠 AI Summary Workflow

1. User navigates to `/stock/[symbol]`
2. Frontend calls `/api/v1/summary/{symbol}`
3. Backend fetches latest 8-K/10-Q via external API (e.g. SEC EDGAR or financial news provider)
4. Sends filing text to Claude API via `summarizer-agent`
5. Response stored in Supabase `summaries` table
6. Frontend renders summary and metadata (date, source)

### Supabase Schema: summaries
```sql
CREATE TABLE summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('filing', 'news')),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

- Summaries are cached per symbol to avoid unnecessary recomputation.
- Only the most recent summary per type is shown on the frontend.

## 📁 File Structure Summary
```
PortfolioApp/
├── CLAUDE.md
├── frontend/
│   └── src/routes/
│       ├── (auth)/login/
│       └── (app)/dashboard, portfolio, stock
│   └── src/lib/components/
│       ├── ui/  # shadcn components
│       ├── portfolio/
│       └── stock/
├── backend/
│   └── app/
│       ├── api/
│       ├── models/
│       ├── schemas/
│       └── services/
├── .github/workflows/
│   └── test.yml
└── README.md
```