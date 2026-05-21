# Google API Setup — Gmail + Sheets

## 1. Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Name: `job-tracker` (anything works)
4. Click **Create**

---

## 2. Enable APIs

In the sidebar: **APIs & Services → Library**

Search and enable:
- **Google Sheets API** → Enable
- **Gmail API** → Enable

---

## 3. Create OAuth 2.0 Credentials

### 3a. Configure the consent screen

**APIs & Services → OAuth consent screen**

- User Type: **External** → Create
- App name: `Job Tracker`
- User support email: your email
- Developer contact: your email
- **Save and Continue** (other fields are optional)

On the **Scopes** screen → Save and Continue (scopes are handled in code)

On the **Test users** screen → **Add Users** → add your Google email → Save and Continue

> ⚠️ In External + unverified mode, only test users can authenticate. This is enough for personal use.

### 3b. Create the credentials

**APIs & Services → Credentials → Create Credentials → OAuth client ID**

- Application type: **Desktop app**
- Name: `job-tracker-desktop`
- **Create**

Click **Download JSON** → rename the file to `credentials.json` → place it at the project root.

```
cerveau/
├── credentials.json   ← here
├── docker-compose.yml
└── api/
```

---

## 4. Create the Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com)
2. Create a new blank sheet
3. Copy the ID from the URL:

```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
                                        ^^^^^^^^^^^^^
```

4. Paste it into `.env`:

```env
SHEET_ID=your_sheet_id
```

> Headers are created automatically on the first API call — do not write them manually.

---

## 5. Configure `.env`

```bash
cp .env.example .env
```

```env
SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms   # example
CREDENTIALS_PATH=../credentials.json
TOKEN_PATH=../token.json
ANTHROPIC_API_KEY=sk-ant-...   # optional
```

---

## 6. First OAuth Authentication

This step generates `token.json`, which is reused automatically afterwards (auto-refresh).

```bash
cd api
pip install -r requirements.txt
python -c "from api.sheets import get_credentials; get_credentials()"
```

- A browser window opens
- Log in with the Google account that owns the Sheet and Gmail
- Accept the requested permissions (Sheets + Gmail)
- Once done, `token.json` is created at the project root

> If you get "Access blocked": make sure your email is in **Test users** (step 3a).

---

## 7. OAuth Scopes

The project requests these scopes:

| Scope | Purpose |
|---|---|
| `spreadsheets` | Read/write the Google Sheet |
| `gmail.compose` | Create Gmail drafts |
| `gmail.readonly` | Read received emails (reply detection) |

---

## 8. Start the Project

```bash
docker compose up -d
```

Verify the API is running:

```bash
curl http://localhost:8000/docs
```

---

## Re-authentication

Required if:
- You changed the OAuth scopes in the code
- `token.json` is corrupted or expired without a valid refresh token

```bash
rm token.json
python -c "from api.sheets import get_credentials; get_credentials()"
```

---

## Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Access blocked: This app's request is invalid` | Email not in Test users | Add it in OAuth consent screen → Test users |
| `Token has been expired or revoked` | Invalid token | Delete `token.json` → re-auth |
| `The caller does not have permission` | API not enabled | Enable Sheets API or Gmail API in the console |
| `invalid_grant` | Wrong `credentials.json` | Re-download from the console |
| `Quota exceeded` | Too many API calls | Wait or reduce check frequency |
