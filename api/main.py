import os
from datetime import date
from typing import Optional

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

import api.gmail as gmail_module
import api.sheets as sheets
from api.models import (
    Candidature,
    CandidatureCreate,
    CandidatureUpdate,
    DraftResponse,
    PipelineEntry,
    RelanceAlert,
    Statut,
)

load_dotenv()

app = FastAPI(title="Job Tracker API", version="1.0.0")

_anthropic_client: Optional[anthropic.Anthropic] = None


def get_llm_client():
    global _anthropic_client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_anthropic_api_key_here":
        return None
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
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
def create_candidature(data: CandidatureCreate):
    return sheets.add_candidature(data)


@app.get("/candidatures", response_model=list[Candidature])
def list_all():
    return sheets.list_candidatures()


@app.get("/candidatures/pipeline", response_model=list[PipelineEntry])
def pipeline():
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
def get_relances():
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


@app.get("/candidatures/{candidature_id}", response_model=Candidature)
def get_one(candidature_id: int):
    c = sheets.get_candidature(candidature_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    return c


@app.put("/candidatures/{candidature_id}/statut", response_model=Candidature)
def update_statut(candidature_id: int, data: CandidatureUpdate):
    c = sheets.update_statut(candidature_id, data.statut)
    if not c:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    return c


@app.post("/candidatures/{candidature_id}/draft", response_model=DraftResponse)
def create_draft(candidature_id: int):
    c = sheets.get_candidature(candidature_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")

    body = gmail_module.generate_email_body(c, llm_client=llm_generate)
    result = gmail_module.create_draft(c, body)

    # Mark as relancé in sheet
    sheets.mark_relance_sent(candidature_id)

    return result
