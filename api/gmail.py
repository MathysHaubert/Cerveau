import base64
import os
from email.mime.text import MIMEText

from googleapiclient.discovery import build

from api.sheets import get_credentials
from api.models import Candidature, DraftResponse, ReplyAlert


def get_gmail_service():
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def _encode_message(to: str, subject: str, body: str) -> dict:
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"message": {"raw": raw}}


def create_draft(candidature: Candidature, body: str) -> DraftResponse:
    service = get_gmail_service()

    to = candidature.contact_email or ""
    subject = f"Relance candidature – {candidature.poste} chez {candidature.entreprise}"

    draft_body = _encode_message(to, subject, body)
    draft = service.users().drafts().create(userId="me", body=draft_body).execute()

    draft_id = draft["id"]
    gmail_link = f"https://mail.google.com/mail/#drafts/{draft_id}"

    return DraftResponse(
        draft_id=draft_id,
        gmail_link=gmail_link,
        message=f"Brouillon créé pour {candidature.entreprise} ({candidature.poste})",
    )


def check_replies(candidatures: list[Candidature]) -> list[ReplyAlert]:
    service = get_gmail_service()

    candidates_by_email = {
        c.contact_email: c
        for c in candidatures
        if c.contact_email
    }
    if not candidates_by_email:
        return []

    query = "from:(" + " OR ".join(candidates_by_email.keys()) + ") in:inbox"
    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=50,
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    alerts = []
    seen_emails = set()

    for m in messages:
        msg = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["Subject", "From"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        from_header = headers.get("From", "")

        matched = next(
            (email for email in candidates_by_email if email in from_header),
            None,
        )
        if not matched or matched in seen_emails:
            continue

        seen_emails.add(matched)
        c = candidates_by_email[matched]
        alerts.append(ReplyAlert(
            id=c.id,
            entreprise=c.entreprise,
            poste=c.poste,
            contact_email=matched,
            subject=headers.get("Subject", "(no subject)"),
            snippet=msg.get("snippet", ""),
            gmail_link=f"https://mail.google.com/mail/u/0/#inbox/{m['id']}",
        ))

    return alerts


def generate_email_body(candidature: Candidature, llm_client=None) -> str:
    """
    Génère le corps de l'email de relance via OpenClaw/Claude.
    Si llm_client fourni, utilise l'IA. Sinon, template fixe de fallback.
    """
    if llm_client:
        prompt = f"""Rédige un email de relance professionnel et bref pour une candidature.

Informations :
- Entreprise : {candidature.entreprise}
- Poste : {candidature.poste}
- Date de candidature : {candidature.date_envoi}
- Contact : {candidature.contact_nom or 'Madame, Monsieur'}
- Notes sur le poste : {candidature.notes or 'Aucune'}

L'email doit :
- Être bref (3-4 phrases max)
- Rappeler la candidature sans être insistant
- Exprimer toujours l'intérêt pour le poste
- Proposer un échange si disponible
- Ton professionnel et direct

Réponds uniquement avec le corps de l'email, sans objet ni signature."""

        return llm_client(prompt)

    # Fallback template
    contact = candidature.contact_nom or "Madame, Monsieur"
    return f"""Bonjour {contact},

Je me permets de revenir vers vous concernant ma candidature au poste de {candidature.poste} au sein de {candidature.entreprise}, envoyée le {candidature.date_envoi.strftime('%d/%m/%Y')}.

Je reste très intéressé(e) par cette opportunité et me tiens disponible pour un échange si vous le souhaitez.

Dans l'attente de votre retour, je vous adresse mes cordiales salutations."""
