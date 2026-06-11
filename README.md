# Vee Group Diagnostic Tool

**AI-powered startup failure diagnostics — cross-referenced against 2,982 real company cases.**

Built on Google Gemini 2.5 Flash with a 1M token context window. Submit your company description and receive a structured 10-section diagnostic report in under 60 seconds: severity score, ghost match, risk analysis, and a 90-day execution plan.

---

## What It Does

The diagnostic engine applies Vee Group's proprietary inductive methodology — the same pattern-recognition framework used in client engagements — to identify whether a company is repeating a known failure pattern.

Every input is cross-referenced against:
- **1,982 failed company cases** across 19 sectors
- **1,000 success benchmarks** of companies that navigated similar circumstances

The AI returns a **Ghost Match** — the closest historical company failure to your current trajectory — along with dimensional risk scores, root-cause analysis, and a prioritised execution plan.

---

## Output — 10-Section Diagnostic Report

| Section | Description |
|---|---|
| Diagnostic Stage | All-caps theatrical name of the current failure arc |
| Severity Score | 0–100 urgency rating |
| Primary Bottleneck | Single root-cause operational failure |
| Ghost Match | Closest failed company from the database + parallel drawn |
| Pattern Matches | Top failure patterns with match percentages |
| Success Benchmarks | Companies that navigated similar circumstances — what they did |
| Risk Scores | 5 dimensional bars: Growth, Brand, Campaign, Operational, Financial |
| Diagnostic Report | Full written analysis — clinical, data-grounded, no hedging |
| Execution Plan | Prioritised steps for the next 30, 60, 90 days |
| Survival Probability | % chance of survival with and without Vee Group intervention |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           LAYER OVER — EXECUTION                     │
│  Web Form · Consent Gate · Report UI · Risk Bars    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           ORCHESTRATION — Flask / Cloud Run          │
│  Sector Keyword Matcher · Token Budget Manager      │
│  Prompt Builder · Response Parser                   │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           AI LAYER — Gemini 2.5 Flash                │
│  1M Token Context · Inductive Reasoning Engine      │
│  Ghost Match · Pattern Cross-Reference              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           LAYER UNDER — SYSTEMS (Proprietary)        │
│  failures.json (1,982)  ·  successes.json (1,000)  │
│  19 Sector Maps · Smart Selection (120+60 cases)   │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           INFRASTRUCTURE                             │
│  Google Cloud Run · Vertex AI Auth · Zero Storage   │
└─────────────────────────────────────────────────────┘
```

Full architecture diagram: [`architecture.svg`](architecture.svg)  
Full architecture plan + roadmap: [`architecture-plan.html`](architecture-plan.html)  
Design system: [`design-system.html`](design-system.html)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.11, Flask 3.1 |
| AI Model | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| AI SDK | `google-genai` 1.16 |
| Deployment | Google Cloud Run (auto-scaling, zero idle cost) |
| Server | Gunicorn |
| Auth | Google AI API key / Vertex AI (env-based) |
| Storage | None — zero-storage privacy model |
| Data | Flat JSON files loaded into memory at startup |

---

## Privacy & Compliance

This tool was designed with a **zero-storage privacy model**:

- No user input is retained after the response is returned
- No session data, no analytics, no logging of company descriptions
- No cookies beyond functional necessity
- Full compliance gate for GDPR, DPDP (India), UK GDPR, and CCPA
- Users explicitly consent before any data is processed

Privacy policy available at `/privacy`.

---

## Running Locally

```bash
git clone https://github.com/vaibhavsaini005-cpu/vee-diagnostic-agent.git
cd vee-diagnostic-agent

pip install -r requirements.txt

# Add your Google AI API key
echo "GOOGLE_API_KEY=your_key_here" > .env

python app.py
# → http://localhost:5000
```

---

## Deployment (Google Cloud Run)

```bash
# Build and deploy
gcloud run deploy vee-diagnostic-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key

# Or use Vertex AI (no API key needed inside GCP)
gcloud run deploy vee-diagnostic-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your_project_id
```

---

## Sector Coverage

19 sectors supported with precision keyword matching:

B2B SaaS · B2C SaaS · FinTech · AI/ML · E-commerce/Marketplace · HealthTech · EdTech · HR Tech · DevTools/Infrastructure · Cybersecurity · Data & Analytics · Real Estate/PropTech · ClimateTech · LegalTech · AgriTech · Creator Economy · Consumer App · Logistics/Supply Chain · Crypto/Web3

---

## Proprietary Data Notice

The failure and success databases (`data/`) are **Vee Group proprietary research**. Every entry is watermarked with VEE GROUP tokens. This repository is shared publicly for hackathon evaluation only. Unauthorised commercial use of the databases is prohibited.

© 2026 Vee Group, New Delhi & United Kingdom

---

## Roadmap

| Phase | Timeline | Focus |
|---|---|---|
| V1 | Live | Diagnostic engine on Cloud Run |
| V2 | 1–3 months | Website integration (veegroup.in), lead funnel, custom domain |
| V3 | 3–6 months | Vector search (HNSW), database expansion to 5,000+ cases |
| V4 | 6–12 months | Multi-tool platform: investor readiness, competitive intel, financial benchmarker |
| V5 | 12–24 months | Fine-tuned Vee model, continuous company health monitoring |

---

## Submission

Built for the **Google for Startups AI Agents Challenge** — DevPost 2026.

**Vee Group** · [veegroup.in](https://veegroup.in) · New Delhi & United Kingdom
