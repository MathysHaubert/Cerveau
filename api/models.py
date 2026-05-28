from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Statut(str, Enum):
    a_contacter = "à contacter"
    envoye = "envoyé"
    relance = "relancé"
    entretien = "entretien"
    offre = "offre"
    refus = "refus"
    abandonne = "abandonné"


class CandidatureCreate(BaseModel):
    entreprise: str
    poste: str
    date_envoi: date
    statut: Optional[Statut] = None
    contact_nom: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    notes: Optional[str] = None
    delai_relance_jours: int = 7


class CandidatureUpdate(BaseModel):
    statut: Statut


class Candidature(BaseModel):
    id: int
    entreprise: str
    poste: str
    date_envoi: date
    statut: Statut
    contact_nom: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    notes: Optional[str] = None
    date_derniere_action: Optional[date] = None
    prochaine_relance: Optional[date] = None
    delai_relance_jours: int = 7


class DraftResponse(BaseModel):
    draft_id: str
    gmail_link: str
    message: str


class PipelineEntry(BaseModel):
    statut: str
    count: int
    candidatures: list[str]


class RelanceAlert(BaseModel):
    id: int
    entreprise: str
    poste: str
    date_envoi: date
    jours_sans_reponse: int
    contact_email: Optional[str] = None


class ReplyAlert(BaseModel):
    id: int
    entreprise: str
    poste: str
    contact_email: str
    subject: str
    snippet: str
    gmail_link: str
