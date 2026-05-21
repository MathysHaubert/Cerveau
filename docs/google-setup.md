# Google API Setup — Gmail + Sheets

## 1. Créer un projet Google Cloud

1. Aller sur [console.cloud.google.com](https://console.cloud.google.com)
2. Cliquer **Select a project** → **New Project**
3. Nom : `job-tracker` (ou ce que tu veux)
4. Cliquer **Create**

---

## 2. Activer les APIs

Dans le menu latéral : **APIs & Services → Library**

Chercher et activer :
- **Google Sheets API** → Enable
- **Gmail API** → Enable

---

## 3. Créer les credentials OAuth 2.0

### 3a. Configurer l'écran de consentement

**APIs & Services → OAuth consent screen**

- User Type : **External** → Create
- App name : `Job Tracker`
- User support email : ton email
- Developer contact : ton email
- **Save and Continue** (les autres champs sont optionnels)

Sur l'écran **Scopes** → Save and Continue (on les gère dans le code)

Sur l'écran **Test users** → **Add Users** → ajouter ton email Google → Save and Continue

> ⚠️ En mode External + non vérifié, seuls les test users peuvent s'authentifier. C'est suffisant pour un usage personnel.

### 3b. Créer les credentials

**APIs & Services → Credentials → Create Credentials → OAuth client ID**

- Application type : **Desktop app**
- Name : `job-tracker-desktop`
- **Create**

Cliquer **Download JSON** → renommer le fichier en `credentials.json` → placer à la racine du projet.

```
cerveau/
├── credentials.json   ← ici
├── docker-compose.yml
└── api/
```

---

## 4. Créer le Google Sheet

1. Aller sur [sheets.google.com](https://sheets.google.com)
2. Créer un nouveau sheet vide
3. Copier l'ID depuis l'URL :

```
https://docs.google.com/spreadsheets/d/SHEET_ID_ICI/edit
                                        ^^^^^^^^^^^^^^
```

4. Coller dans `.env` :

```env
SHEET_ID=ton_sheet_id
```

> Les headers sont créés automatiquement au premier appel API — ne pas les écrire manuellement.

---

## 5. Configurer `.env`

```bash
cp .env.example .env
```

```env
SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms   # exemple
CREDENTIALS_PATH=../credentials.json
TOKEN_PATH=../token.json
ANTHROPIC_API_KEY=sk-ant-...   # optionnel
```

---

## 6. Première authentification OAuth

Cette étape génère `token.json` qui sera réutilisé ensuite (refresh automatique).

```bash
cd api
pip install -r requirements.txt
python -c "from api.sheets import get_credentials; get_credentials()"
```

- Un navigateur s'ouvre
- Se connecter avec le compte Google qui a accès au Sheet et à Gmail
- Accepter les permissions demandées (Sheets + Gmail)
- Une fois validé, `token.json` est créé à la racine

> Si erreur "Access blocked" : vérifier que ton email est dans les **Test users** (étape 3a).

---

## 7. Scopes autorisés

Le projet demande ces scopes OAuth :

| Scope | Usage |
|---|---|
| `spreadsheets` | Lire/écrire le Google Sheet |
| `gmail.compose` | Créer des brouillons Gmail |
| `gmail.readonly` | Lire les mails reçus (détection de réponses) |

---

## 8. Lancer le projet

```bash
docker compose up -d
```

Vérifier que l'API répond :

```bash
curl http://localhost:8000/docs
```

---

## Re-authentification

Nécessaire si :
- Tu as modifié les scopes dans le code
- Le `token.json` est corrompu ou expiré sans refresh token valide

```bash
rm token.json
python -c "from api.sheets import get_credentials; get_credentials()"
```

---

## Erreurs courantes

| Erreur | Cause | Fix |
|---|---|---|
| `Access blocked: This app's request is invalid` | Email pas dans Test users | Ajouter dans OAuth consent screen → Test users |
| `Token has been expired or revoked` | Token invalide | Supprimer `token.json` → re-auth |
| `The caller does not have permission` | API pas activée | Activer Sheets API ou Gmail API dans la console |
| `invalid_grant` | `credentials.json` mauvais projet | Re-télécharger depuis la console |
| `Quota exceeded` | Trop d'appels API | Attendre ou réduire la fréquence des checks |
