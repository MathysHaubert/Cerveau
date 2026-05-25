import os
from datetime import date
from typing import Optional

import anthropic
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

import api.gmail as gmail_module
import api.sheets as sheets
from api.models import (
    Candidature,
    CandidatureCreate,
    CandidatureUpdate,
    DraftResponse,
    PipelineEntry,
    RelanceAlert,
    ReplyAlert,
    Statut,
)

load_dotenv()

app = FastAPI(title="Job Tracker API", version="1.0.0")

_api_key_header = APIKeyHeader(name="X-API-Secret", auto_error=False)


def verify_secret(key: str = Security(_api_key_header)):
    secret = os.environ.get("API_SECRET")
    if secret and key != secret:
        raise HTTPException(status_code=403, detail="Forbidden")


_auth = Depends(verify_secret)

_anthropic_client: Optional[anthropic.Anthropic] = None


def get_llm_client():
    global _anthropic_client
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "dummy")
    if not base_url and (not api_key or api_key == "your_anthropic_api_key_here"):
        return None
    if _anthropic_client is None:
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        _anthropic_client = anthropic.Anthropic(**kwargs)
    return _anthropic_client


def llm_generate(prompt: str) -> str:
    client = get_llm_client()
    if not client:
        return None
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


@app.post("/candidatures", response_model=Candidature, status_code=201)
def create_candidature(data: CandidatureCreate, _=_auth):
    return sheets.add_candidature(data)


@app.get("/candidatures", response_model=list[Candidature])
def list_all(_=_auth):
    return sheets.list_candidatures()


@app.get("/candidatures/pipeline", response_model=list[PipelineEntry])
def pipeline(_=_auth):
    all_c = sheets.list_candidatures()
    groups: dict[str, list[str]] = {}
    for c in all_c:
        label = c.statut.value
        groups.setdefault(label, []).append(f"{c.entreprise} – {c.poste}")

    order = [s.value for s in Statut]
    return [
        PipelineEntry(statut=statut, count=len(entries), candidatures=entries)
        for statut in order
        if (entries := groups.get(statut))
    ]


@app.get("/candidatures/relances", response_model=list[RelanceAlert])
def get_relances(_=_auth):
    today = date.today()
    relances = sheets.get_relances()
    alerts = []
    for c in relances:
        jours = (today - c.date_derniere_action).days if c.date_derniere_action else (today - c.date_envoi).days
        alerts.append(RelanceAlert(
            id=c.id,
            entreprise=c.entreprise,
            poste=c.poste,
            date_envoi=c.date_envoi,
            jours_sans_reponse=jours,
            contact_email=c.contact_email,
        ))
    return alerts


@app.get("/candidatures/replies", response_model=list[ReplyAlert])
def get_replies(_=_auth):
    active = [
        c for c in sheets.list_candidatures()
        if c.statut in (Statut.envoye, Statut.relance) and c.contact_email
    ]
    return gmail_module.check_replies(active)


@app.get("/candidatures/{candidature_id}", response_model=Candidature)
def get_one(candidature_id: int, _=_auth):
    c = sheets.get_candidature(candidature_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    return c


@app.put("/candidatures/{candidature_id}/statut", response_model=Candidature)
def update_statut(candidature_id: int, data: CandidatureUpdate, _=_auth):
    c = sheets.update_statut(candidature_id, data.statut)
    if not c:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    return c


@app.post("/candidatures/{candidature_id}/draft", response_model=DraftResponse)
def create_draft(candidature_id: int, _=_auth):
    c = sheets.get_candidature(candidature_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")

    body = gmail_module.generate_email_body(c, llm_client=llm_generate)
    result = gmail_module.create_draft(c, body)

    # Mark as relancé in sheet
    sheets.mark_relance_sent(candidature_id)

    return result
