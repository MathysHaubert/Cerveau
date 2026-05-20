# Job Tracker — Contexte projet

## But

Automatiser le suivi de candidatures pour recherche d'emploi :
- Google Sheets = base de données des candidatures
- Gmail API = création de brouillons de relance (pas d'envoi auto)
- Telegram = interface utilisateur via OpenClaw
- FastAPI Python = API locale entre OpenClaw et les APIs Google

## Architecture

```
Telegram → OpenClaw (VPS OVH) → FastAPI (localhost:8000) → Google Sheets
                                                          → Gmail (drafts)
```

## Structure fichiers

```
job-tracker/
├── api/
│   ├── main.py          # FastAPI endpoints
│   ├── sheets.py        # Google Sheets read/write (gspread)
│   ├── gmail.py         # Gmail draft creation + LLM email generation
│   ├── models.py        # Pydantic models (Candidature, Statut enum, etc.)
│   └── requirements.txt
├── openclaw-skill/
│   └── job_tracker.md   # Skill OpenClaw — instructions NL + exemples
├── credentials.json     # OAuth Google (ne pas committer)
├── token.json           # Token refresh auto (ne pas committer)
├── .env                 # SHEET_ID, ANTHROPIC_API_KEY, etc.
└── .env.example
```

## Décisions de design

- **FastAPI** : OpenClaw appelle URLs HTTP comme skills → API locale propre
- **Pas d'envoi auto** : brouillon Gmail créé, l'utilisateur envoie manuellement
- **LLM pour emails** : `gmail.py::generate_email_body()` utilise Claude Haiku avec les notes du sheet; fallback template fixe si pas de clé API
- **Délai relance** : 7 jours par défaut, configurable par ligne dans Sheets (colonne "Délai relance (jours)")
- **OAuth partagé** : `sheets.py::get_credentials()` gère Sheets + Gmail avec un seul `credentials.json`

## Statuts candidature

`envoyé` → `relancé` → `entretien` → `offre` → `refus` / `abandonné`

## Google Sheets schéma (colonnes dans l'ordre)

| # | Nom | Notes |
|---|---|---|
| 1 | ID | auto-incrémenté |
| 2 | Entreprise | |
| 3 | Poste | |
| 4 | Date envoi | YYYY-MM-DD |
| 5 | Statut | enum ci-dessus |
| 6 | Contact nom | |
| 7 | Contact email | |
| 8 | Contact LinkedIn | |
| 9 | Notes | contexte poste, impressions |
| 10 | Date dernière action | mise à jour auto |
| 11 | Prochaine relance | calculé: dernière action + délai |
| 12 | Délai relance (jours) | défaut 7 |

## Variables d'environnement (.env)

```
SHEET_ID=               # ID du Google Sheet (URL)
CREDENTIALS_PATH=../credentials.json
TOKEN_PATH=../token.json
ANTHROPIC_API_KEY=      # Optionnel, pour génération IA emails
```

## Setup initial (à faire une fois)

1. Google Cloud Console → créer projet → activer "Google Sheets API" + "Gmail API"
2. Créer credentials OAuth 2.0 Desktop → télécharger `credentials.json`
3. Créer Google Sheet avec headers (auto-créés au 1er appel API)
4. Copier `.env.example` → `.env`, remplir `SHEET_ID`
5. `cd api && pip install -r requirements.txt`
6. `python -c "from sheets import get_credentials; get_credentials()"` → auth OAuth dans browser
7. `uvicorn main:app --port 8000`

## Déploiement VPS

- FastAPI via `systemd` ou `docker-compose`, port 8000 non exposé publiquement
- OpenClaw installé séparément, skill `job_tracker.md` dans `~/.claw/skills/`
- Rappel quotidien 9h configuré dans OpenClaw (cron interne)

## APIs clés

| Endpoint | Description |
|---|---|
| `POST /candidatures` | Ajouter candidature |
| `GET /candidatures/pipeline` | Résumé par statut |
| `GET /candidatures/relances` | Candidatures > délai sans réponse |
| `PUT /candidatures/{id}/statut` | Changer statut |
| `POST /candidatures/{id}/draft` | Créer brouillon relance Gmail |
