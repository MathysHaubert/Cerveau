import os
from datetime import date
from typing import Optional

import google.generativeai as genai
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

_gemini_model: Optional[genai.GenerativeModel] = None


def get_llm_client() -> Optional[genai.GenerativeModel]:
    global _gemini_model
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    if _gemini_model is None:
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
    return _gemini_model


def llm_generate(prompt: str) -> Optional[str]:
    model = get_llm_client()
    if not model:
        return None
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return None


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
    sheets.mark_relance_sent(candidature_id)
    return result
