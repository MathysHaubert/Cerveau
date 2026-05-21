# 🧠 Cerveau — AI Job Application Tracker via Messaging

```
You:  Morning. What's waiting for me?

🤖  ⏰ 2 follow-ups overdue

    • Stripe (Backend Engineer) — 9 days no reply
    • Figma (Product Designer) — 7 days no reply

    Type "follow up Stripe" to generate a draft.

---

You:  Follow up Stripe

🤖  ✅ Draft ready in Gmail
    Subject: "Following up — Backend Engineer @ Stripe"
    → https://mail.google.com/mail/u/0/#drafts/...

    Stripe marked as followed up.
```

![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Docker](https://img.shields.io/badge/docker-compose-blue?logo=docker&logoColor=white)

> Track job applications, get follow-up reminders, and generate AI-written follow-up emails — all from your messaging app. No new apps, no dashboards.

```
You → Telegram / WhatsApp / Signal / ... → OpenClaw AI → FastAPI → Google Sheets
                                                                  → Gmail (drafts)
```

---

## What it does

- **Add applications** by chatting naturally from any supported messaging app: *"Add application at Stripe, Backend Engineer, contact alice@stripe.com"*
- **See your pipeline** at a glance: how many applications per stage, who's waiting
- **Get daily reminders** at 9am for applications that haven't had a reply in 7+ days
- **Generate follow-up emails** with Claude AI based on your notes from the sheet — saved as Gmail drafts, never sent automatically

Everything lives in a Google Sheet you own. No database to manage, no proprietary format.

---

## Demo

<!-- GIF DEMO HERE — record a short Telegram session showing pipeline + draft creation -->
<!-- Suggested tool: https://github.com/charmbracelet/vhs or OBS → gifski -->

```
You: Where am I in my job search?

🤖 📊 Pipeline — 2025-05-21

✉️ Sent (3): Datadog, Stripe, Notion
🔄 Followed up (1): Figma
🤝 Interview (2): Anthropic, Linear
❌ Rejected (1): Google

---

You: Follow up on Figma

🤖 Draft created ✅
→ Open in Gmail: https://mail.google.com/...
```

---

## Stack

| Layer | Tech |
|---|---|
| Interface | Any messaging app via [OpenClaw](https://github.com/openclaw/openclaw) (Telegram, WhatsApp, Signal…) |
| Backend | FastAPI (Python) |
| Database | Google Sheets (gspread) |
| Email | Gmail API (OAuth, drafts only) |
| AI | Claude Haiku (optional, for email generation) |
| Deploy | Docker Compose |

---

## Use only what you need

This project is modular — use all of it or just the parts you need.

| You want | What to use |
|---|---|
| Full setup (API + messaging) | This repo + Docker Compose |
| Just the API (bring your own frontend) | `api/` folder only — plain FastAPI, no OpenClaw required |
| Just the OpenClaw skill (you already have an API) | `openclaw-skill/job_tracker.md` — point the URL to your own backend |

### API only

```bash
cd api
pip install -r requirements.txt
uvicorn api.main:app --port 8000
# Swagger at http://localhost:8000/docs
```

### OpenClaw skill only

Copy `openclaw-skill/job_tracker.md` to your OpenClaw skills directory and update the API URL inside the file to point to your backend.

---

## Quick Start

### 1. Google Cloud Setup

> Full step-by-step guide (OAuth consent screen, scopes, common errors): [docs/google-setup.md](docs/google-setup.md)

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com)
2. Enable **Google Sheets API** and **Gmail API**
3. Create OAuth 2.0 credentials (Desktop app) → download as `credentials.json`
4. Create a Google Sheet — copy its ID from the URL

### 2. Configure

```bash
git clone https://github.com/yourusername/cerveau
cd cerveau
cp .env.example .env
```

Edit `.env`:
```env
SHEET_ID=your_google_sheet_id
CREDENTIALS_PATH=../credentials.json
TOKEN_PATH=../token.json
ANTHROPIC_API_KEY=     # Optional — enables AI email generation
```

### 3. First-time OAuth

```bash
cd api
pip install -r requirements.txt
python -c "from api.sheets import get_credentials; get_credentials()"
# Opens browser for Google auth → generates token.json
```

### 4. Run

```bash
docker compose up -d
```

This starts:
- **FastAPI** on port 8000 (not public-facing)
- **OpenClaw gateway** on port 18789 (handles Telegram ↔ API)

### 5. Connect your messaging app

Follow [OpenClaw setup](https://github.com/openclaw/openclaw) to link your preferred messaging app (Telegram, WhatsApp, Signal, and more). The `job_tracker.md` skill is automatically mounted in the container.

---

## Application Status Flow

```
sent → followed_up → interview → offer → rejected / abandoned
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `POST /candidatures` | Add application |
| `GET /candidatures/pipeline` | Summary by status |
| `GET /candidatures/relances` | Applications overdue for follow-up |
| `PUT /candidatures/{id}/statut` | Update status |
| `POST /candidatures/{id}/draft` | Create Gmail follow-up draft |

Swagger UI available at `http://localhost:8000/docs` when running locally.

---

## Google Sheet Schema

| Column | Description |
|---|---|
| ID | Auto-incremented |
| Company | |
| Position | |
| Date sent | YYYY-MM-DD |
| Status | enum |
| Contact name | |
| Contact email | |
| Contact LinkedIn | |
| Notes | Context, impressions — used by AI for email generation |
| Last action date | Auto-updated |
| Next follow-up | Calculated: last action + delay |
| Follow-up delay (days) | Default 7, configurable per row |

---

## AI Email Generation

When `ANTHROPIC_API_KEY` is set, follow-up emails are generated by Claude Haiku using:
- Company name and position
- Contact information
- Your notes from the sheet

Without the API key, a template email is used as fallback. Emails are always saved as **Gmail drafts** — never sent automatically.

---

## Why this exists

Most job trackers are either too heavy (full SaaS, proprietary data) or too light (just a spreadsheet). This project hits the middle ground: your data stays in Google Sheets, but you get an AI assistant in your pocket that reminds you when to follow up and writes the emails for you.

---

## Contributing

PRs welcome. Key areas where help is appreciated:
- Additional messaging app integrations via OpenClaw
- More LLM providers for email generation (currently Claude only)
- Multi-sheet / multi-user support

Open an issue first for larger changes.

---

## GitHub Topics

> If you're setting up the repo: add these topics in **Settings → Topics**
> `job-search` `fastapi` `google-sheets` `gmail` `self-hosted` `telegram-bot` `openclaw` `job-tracker` `python`

---

## License

MIT
