# Job Tracker - Formats d'affichage

## Pipeline

```
Pipeline - {date}

A contacter (2) : OpenAI, Mistral
Envoye (3) : Datadog, Stripe, Notion
Relance (1) : Figma
Entretien (2) : Anthropic, Linear
Refus (1) : Google
```

## Reponses recues

```
Reponses recues :
- Stripe (Backend Engineer) — alice@stripe.com
  Sujet : "Re: Candidature Backend Engineer"
  Apercu : "Bonjour, merci pour votre candidature..."
  Lien : https://mail.google.com/...
```

Vide : "Aucune reponse recue."

## Relances en retard

```
Relances en attente :
- Datadog (SRE) - 8j sans reponse
- Stripe (Backend) - 7j sans reponse

Tape "relance [entreprise]" pour creer un brouillon.
```

## Rappel quotidien (9h)

Afficher reponses recues si present, puis relances en attente si present. Si tout vide : "Rien a signaler aujourd'hui."
