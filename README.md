# Jev AI Control Center

An internal AI usage monitoring **and model-routing** dashboard.

## What

Jev AI Control Center is a local proof-of-concept web app that tracks every AI request made
by our teams (OpenAI/ChatGPT and Anthropic/Claude), records token usage and estimated cost,
and — most importantly — runs every prompt through **Jev**, a decision layer that classifies
task complexity and recommends the right model tier before the request is ever sent.

Jev is **not** a token-monitoring platform. Token/cost tracking is a side effect of routing
through Jev; the actual product is the routing decision itself:

- **Complexity**: LOW / MEDIUM / HIGH / CRITICAL
- **Route**: CHEAP / STANDARD / ADVANCED / ADVANCED + HUMAN REVIEW
- **Human review required?** Yes/No

## Why

As AI usage scales across departments, two problems appear:
1. Nobody has visibility into what is actually being spent, by whom, on what.
2. Every request gets sent to the most expensive model "just in case," burning budget on
   tasks that a cheap model could have handled — or worse, a CRITICAL task (security,
   compliance, production migrations) gets handled without any human oversight.

Jev solves both: it right-sizes the model per request and gives finance/ops a single
dashboard for spend, budget, and routing behavior.

## Where

Runs entirely locally for this POC (Flask + SQLite). It is designed to later sit as a proxy
layer in front of any team's AI integrations — a Slack bot, an internal tool, a CI pipeline —
wherever a prompt needs to be classified and routed before it hits a paid model.

## When

Jev routing should be used any time a prompt is about to be sent to a paid LLM API and the
team wants cost control and/or a mandatory human-review gate for high-stakes requests
(security, compliance, production changes, anything touching credentials/PII).

## Who

- **R&D, Web Development, Game Development, Android, Automation** — day-to-day coding/debugging
  tasks that benefit from tiered routing (don't burn an advanced model on a one-line fix).
- **Content Team, Video Team, 2D/3D Team** — content generation tasks, mostly MEDIUM complexity.
- **UI/UX** — design/copy tasks.
- **Finance/Ops/Leadership** — budget visibility and department/project cost accountability.

## How the request flow works

```
User enters a prompt
  -> Select Department
  -> Select Project
  -> Select Provider (OpenAI or Claude)
  -> Jev Decision Layer analyses the task
  -> Classify complexity (LOW/MEDIUM/HIGH/CRITICAL)
  -> Choose model tier (CHEAP/STANDARD/ADVANCED [+ HUMAN REVIEW])
  -> Send request to the chosen provider's configured model for that tier
  -> Receive response, capture input/output/total tokens + response time
  -> Calculate estimated cost (config/pricing.py rates)
  -> Save everything to SQLite (request, tokens, cost, Jev decision)
  -> Dashboard updates immediately
```

## Project Structure

```
jev_ai_control_center/
  app.py                     Flask routes / orchestration
  requirements.txt
  .env.example
  README.md
  config/
    pricing.py               Per-provider/tier $ rates per 1M tokens
    settings.py               Env var loading, defaults, department/project seeds
  services/
    jev.py                    Jev decision layer (demo heuristic + real-API hook)
    openai_provider.py        OpenAI call + demo fallback
    anthropic_provider.py     Claude call + demo fallback
    router.py                 Tier -> configured model name resolution
    cost_calculator.py        Token counts -> estimated cost
  database/
    db.py                     SQLite schema, seeding, all queries
  templates/                  Jinja2 templates (Bootstrap 5)
  static/css/style.css
  static/js/dashboard.js
  data/jev_ai.db              SQLite database file (created on first run)
```

## Database schema (SQLite)

`users`, `departments`, `projects`, `ai_requests`, `token_usage`, `cost_usage`,
`jev_decisions`, `budgets` — see `database/db.py` for full column definitions.

## How to install

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
copy .env.example .env
```

## How to run

```bash
python app.py
```

Then open **http://127.0.0.1:5055**

## How demo mode works

The app runs **fully without any API keys**. When `TYPESAFE_API_KEY`, `OPENAI_API_KEY`, or
`ANTHROPIC_API_KEY` are left blank in `.env`:

- **Jev** falls back to a local keyword/length heuristic (`services/jev.py`) to classify
  complexity, and every decision is tagged `"Demo Decision"` in the UI.
- **OpenAI/Claude calls** return a simulated response with realistic random token counts
  instead of calling the real API (`services/openai_provider.py`, `services/anthropic_provider.py`).
- **Cost** is calculated normally from the simulated token counts using `config/pricing.py`.
- **All of this is written to real SQLite records** — the dashboard, history, filters, and
  budget tracking are fully functional in demo mode.

## How to enable real API integrations

Fill in the relevant keys in `.env`:

```
TYPESAFE_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Restart the app. Each provider is checked independently — you can enable OpenAI only,
Claude only, both, or neither. If a real call fails for any reason (bad key, rate limit,
network error), the app automatically falls back to that provider's demo response and logs
the error — the dashboard never breaks because of a provider outage.

The Jev real-API integration point (`services/jev._real_jev_decision`) is stubbed and ready
to wire up once a live Jev/Typesafe endpoint exists; until then it always falls back to demo
decisions when `TYPESAFE_API_KEY` is set but the call isn't implemented.

## What is currently demo

- Jev decisions (local heuristic — no live Jev/Typesafe endpoint exists yet)
- AI responses and token counts, unless you configure `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`

## What becomes real after adding API keys

- OpenAI and/or Claude calls hit the real API, return real completions, and capture real
  token usage and response time directly from each provider's SDK.
- Cost is calculated from real token counts using the same configurable pricing table.
- Jev decisions remain demo-mode until a real Jev/Typesafe API is implemented in
  `services/jev.py`.

## Limitations (POC scope)

- No authentication/authorization — anyone with access to the running instance can submit
  requests and change the budget.
- Single shared company-wide budget; no per-department budget enforcement yet (schema
  supports it via `budgets.department`, but the UI only manages the company-wide row).
- Jev's real-API integration is a stub — there is no live Jev/Typesafe service to call today.
- SQLite is fine for a local POC; a multi-user production deployment would need a proper
  server-based database and a WSGI server (not Flask's dev server).

## Recommended next development step

Wire up department-level budgets in the dashboard (the schema already supports it), add a
simple login/role system so "human review required" requests can be assigned to a reviewer,
and implement the real Jev/Typesafe API call once that service is available.
