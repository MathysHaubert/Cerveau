import os
from datetime import date, timedelta
from typing import Optional
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from api.models import Candidature, CandidatureCreate, Statut

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

SHEET_HEADERS = [
    "ID", "Entreprise", "Poste", "Date envoi", "Statut",
    "Contact nom", "Contact email", "Contact LinkedIn", "Notes",
    "Date dernière action", "Prochaine relance", "Délai relance (jours)"
]

_creds_cache: Optional[Credentials] = None
_sheet_cache: Optional[gspread.Worksheet] = None
_sheet_id_cache: Optional[str] = None


def invalidate_cache():
    global _creds_cache, _sheet_cache, _sheet_id_cache
    _creds_cache = None
    _sheet_cache = None
    _sheet_id_cache = None


def get_credentials() -> Credentials:
    global _creds_cache
    token_path = os.environ.get("TOKEN_PATH", "token.json")
    creds_path = os.environ.get("CREDENTIALS_PATH", "credentials.json")

    if _creds_cache and _creds_cache.valid:
        return _creds_cache

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    _creds_cache = creds
    return creds


def get_sheet() -> gspread.Worksheet:
    global _sheet_cache, _sheet_id_cache
    sheet_id = os.environ["SHEET_ID"]
    if _sheet_cache is not None and _sheet_id_cache == sheet_id:
        return _sheet_cache

    creds = get_credentials()
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(sheet_id).sheet1

    if not worksheet.row_values(1):
        worksheet.append_row(SHEET_HEADERS)

    _sheet_cache = worksheet
    _sheet_id_cache = sheet_id
    return worksheet


def row_to_candidature(row: list, index: int) -> Optional[Candidature]:
    if len(row) < 5 or not row[0]:
        return None
    try:
        return Candidature(
            id=int(row[0]),
            entreprise=row[1],
            poste=row[2],
            date_envoi=date.fromisoformat(row[3]),
            statut=Statut(row[4]),
            contact_nom=row[5] if len(row) > 5 else None,
            contact_email=row[6] if len(row) > 6 else None,
            contact_linkedin=row[7] if len(row) > 7 else None,
            notes=row[8] if len(row) > 8 else None,
            date_derniere_action=date.fromisoformat(row[9]) if len(row) > 9 and row[9] else None,
            prochaine_relance=date.fromisoformat(row[10]) if len(row) > 10 and row[10] else None,
            delai_relance_jours=int(row[11]) if len(row) > 11 and row[11] else 7,
        )
    except Exception:
        return None


def get_next_id(worksheet) -> int:
    records = worksheet.get_all_values()
    data_rows = [r for r in records[1:] if r and r[0].strip().isdigit()]
    if not data_rows:
        return 1
    return max(int(r[0]) for r in data_rows) + 1


def add_candidature(data: CandidatureCreate) -> Candidature:
    ws = get_sheet()
    next_id = get_next_id(ws)
    today = date.today().isoformat()
    prochaine = (data.date_envoi + timedelta(days=data.delai_relance_jours)).isoformat()

    statut = data.statut if data.statut is not None else Statut.a_contacter
    row = [
        next_id,
        data.entreprise,
        data.poste,
        data.date_envoi.isoformat(),
        statut.value,
        data.contact_nom or "",
        data.contact_email or "",
        data.contact_linkedin or "",
        data.notes or "",
        today,
        prochaine,
        data.delai_relance_jours,
    ]
    ws.append_row(row)

    return Candidature(
        id=next_id,
        entreprise=data.entreprise,
        poste=data.poste,
        date_envoi=data.date_envoi,
        statut=statut,
        contact_nom=data.contact_nom,
        contact_email=data.contact_email,
        contact_linkedin=data.contact_linkedin,
        notes=data.notes,
        date_derniere_action=date.today(),
        prochaine_relance=data.date_envoi + timedelta(days=data.delai_relance_jours),
        delai_relance_jours=data.delai_relance_jours,
    )


def list_candidatures() -> list[Candidature]:
    ws = get_sheet()
    records = ws.get_all_values()
    result = []
    for i, row in enumerate(records[1:], start=2):
        c = row_to_candidature(row, i)
        if c:
            result.append(c)
    return result


def find_candidature_row(ws, candidature_id: int) -> tuple[Optional[Candidature], int]:
    records = ws.get_all_values()
    for i, row in enumerate(records[1:], start=2):
        if row and row[0].strip() == str(candidature_id):
            return row_to_candidature(row, i), i
    return None, -1


def update_statut(candidature_id: int, statut: Statut) -> Optional[Candidature]:
    ws = get_sheet()
    c, row_num = find_candidature_row(ws, candidature_id)
    if not c:
        return None

    today = date.today()
    updates = [
        {"range": f"E{row_num}", "values": [[statut.value]]},
        {"range": f"J{row_num}", "values": [[today.isoformat()]]},
    ]
    if statut in (Statut.envoye, Statut.relance):
        prochaine = today + timedelta(days=c.delai_relance_jours)
        updates.append({"range": f"K{row_num}", "values": [[prochaine.isoformat()]]})
    ws.batch_update(updates)

    c.statut = statut
    c.date_derniere_action = today
    return c


def get_relances() -> list[Candidature]:
    today = date.today()
    all_c = list_candidatures()
    return [
        c for c in all_c
        if c.statut in (Statut.envoye, Statut.relance)
        and c.prochaine_relance is not None
        and c.prochaine_relance <= today
    ]


def get_candidature(candidature_id: int) -> Optional[Candidature]:
    ws = get_sheet()
    c, _ = find_candidature_row(ws, candidature_id)
    return c


def mark_relance_sent(candidature_id: int):
    ws = get_sheet()
    c, row_num = find_candidature_row(ws, candidature_id)
    if not c:
        return
    today = date.today()
    prochaine = today + timedelta(days=c.delai_relance_jours)
    ws.batch_update([
        {"range": f"E{row_num}", "values": [[Statut.relance.value]]},
        {"range": f"J{row_num}", "values": [[today.isoformat()]]},
        {"range": f"K{row_num}", "values": [[prochaine.isoformat()]]},
    ])
