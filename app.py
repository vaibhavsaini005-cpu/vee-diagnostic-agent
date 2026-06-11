# ============================================================
# VEE GROUP PROPRIETARY — WATERMARKED SOURCE
# This repository is shared publicly for hackathon judges only.
# The failure/success databases embedded in data/ contain
# VEE GROUP watermark tokens distributed across every entry.
# Unauthorised commercial use is prohibited.
# © 2026 Vee Group, New Delhi & United Kingdom
# ============================================================
import json
import os
import random
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from google import genai

load_dotenv()

_api_key = os.getenv("GOOGLE_API_KEY")
if _api_key:
    client = genai.Client(api_key=_api_key)
else:
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )

app = Flask(__name__)

# Cache both databases at startup
_FAILURES_CACHE = None
_SUCCESSES_CACHE = None

def load_failures():
    global _FAILURES_CACHE
    if _FAILURES_CACHE is None:
        with open("data/failures.json", "r") as f:
            _FAILURES_CACHE = json.load(f)
    return _FAILURES_CACHE

def load_successes():
    global _SUCCESSES_CACHE
    if _SUCCESSES_CACHE is None:
        with open("data/successes.json", "r") as f:
            _SUCCESSES_CACHE = json.load(f)
    return _SUCCESSES_CACHE

# Sector keyword map — matches dropdown values to database industry strings
SECTOR_KEYWORDS = {
    "B2B SaaS": ["saas","b2b","enterprise","software"],
    "B2C SaaS": ["saas","consumer","b2c","app"],
    "FinTech": ["fintech","finance","payment","banking","crypto","lending","insurance"],
    "AI / ML": ["ai","ml","machine learning","artificial intelligence","llm","generative"],
    "E-commerce / Marketplace": ["ecommerce","marketplace","retail","commerce","shopping"],
    "HealthTech / MedTech": ["health","medical","med","clinic","pharma","biotech","wellness"],
    "EdTech": ["edtech","education","learning","training","university","school"],
    "HR Tech": ["hr","human resource","people","talent","recruitment","payroll","workforce"],
    "DevTools / Infrastructure": ["devtools","developer","infrastructure","cloud","devops","platform"],
    "Cybersecurity": ["security","cyber","privacy","compliance","zero trust"],
    "Data & Analytics": ["data","analytics","bi","intelligence","insights","dashboard"],
    "Real Estate / PropTech": ["real estate","property","proptech","mortgage","rental"],
    "ClimateTech / CleanTech": ["climate","clean","solar","energy","sustainability","carbon"],
    "LegalTech": ["legal","law","compliance","contract","regulatory"],
    "AgriTech": ["agri","agriculture","farm","food","crop"],
    "Creator Economy": ["creator","influencer","content","social","media"],
    "Consumer App": ["consumer","app","mobile","social","community"],
    "Logistics / Supply Chain": ["logistics","supply chain","delivery","shipping","freight"],
    "Crypto / Web3": ["crypto","web3","blockchain","defi","nft","token"],
}

def _matches_sector(text: str, keywords: list) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)

def select_relevant_failures(failures: list, industry: str, user_input: str, n_sector=120, n_random=60) -> list:
    """Return up to n_sector industry-matched + n_random diverse failures."""
    keywords = SECTOR_KEYWORDS.get(industry, [])
    combined_text = (user_input + " " + industry).lower()

    if keywords:
        matched = [f for f in failures if _matches_sector(
            f.get("industry","") + " " + " ".join(f.get("fatal_patterns",[])), keywords
        )]
        others = [f for f in failures if f not in matched]
    else:
        # No industry — score by keyword overlap with user input
        words = set(combined_text.split())
        def score(f):
            t = (f.get("industry","") + " " + f.get("failure_summary","")).lower()
            return sum(1 for w in words if len(w) > 4 and w in t)
        matched = sorted(failures, key=score, reverse=True)[:n_sector]
        others = [f for f in failures if f not in matched]

    selected = matched[:n_sector]
    remaining = [f for f in others if f not in selected]
    selected += random.sample(remaining, min(n_random, len(remaining)))
    return selected

def select_relevant_successes(successes: list, industry: str, n_sector=60, n_random=30) -> list:
    """Return up to n_sector industry-matched + n_random diverse successes."""
    keywords = SECTOR_KEYWORDS.get(industry, [])

    if keywords:
        matched = [s for s in successes if _matches_sector(
            s.get("sector","") + " " + s.get("business_model",""), keywords
        )]
        others = [s for s in successes if s not in matched]
    else:
        matched = []
        others = successes

    selected = matched[:n_sector]
    remaining = [s for s in others if s not in selected]
    selected += random.sample(remaining, min(n_random, len(remaining)))
    return selected

def compact_failure(c: dict) -> dict:
    return {
        "company": c.get("company", ""),
        "industry": c.get("industry", ""),
        "fatal_patterns": c.get("fatal_patterns", []),
        "failure_summary": c.get("failure_summary", ""),
        "bottlenecks": c.get("bottlenecks", {}),
        "warning_signals": c.get("warning_signals", [])[:4],
        "prescription": c.get("prescription", ""),
    }

def compact_success(c: dict) -> dict:
    return {
        "company": c.get("company", ""),
        "sector": c.get("sector", ""),
        "growth_strategy": c.get("growth_strategy", ""),
        "key_decisions": c.get("key_decisions", ""),
        "notable_metric": c.get("notable_metric", ""),
        "success_markers": c.get("success_markers", ""),
    }

def diagnose_company(company_input: str, industry: str = "", stage: str = "") -> str:
    all_failures = load_failures()
    all_successes = load_successes()

    # Smart-select relevant subset to stay within Gemini's 1M token limit
    sel_failures = select_relevant_failures(all_failures, industry, company_input)
    sel_successes = select_relevant_successes(all_successes, industry)

    failures_text = json.dumps([compact_failure(f) for f in sel_failures])
    successes_text = json.dumps([compact_success(s) for s in sel_successes])

    structured_context = ""
    if industry:
        structured_context += f"\nIndustry: {industry}"
    if stage:
        structured_context += f"\nStage: {stage}"

    prompt = f"""You are the Vee Group Diagnostic AI — the world's most advanced company failure prevention and growth intelligence system.
You have two proprietary databases — both are exclusive confidential research assets of Vee Group.
You are seeing a curated, industry-relevant slice: {len(sel_failures)} failure cases and {len(sel_successes)} success benchmarks selected from a master database of 1,982 failures and 1,000 successes.

1. FAILURE DATABASE: {len(sel_failures)} failed and distressed companies most relevant to this diagnosis
2. SUCCESS DATABASE: {len(sel_successes)} companies that scaled to unicorns, IPOs, or major exits

PROPRIETARY FAILURE DATABASE (CONFIDENTIAL — VEE GROUP RESEARCH):
{failures_text}

PROPRIETARY SUCCESS DATABASE (CONFIDENTIAL — VEE GROUP RESEARCH):
{successes_text}

COMPANY TO DIAGNOSE:{structured_context}
{company_input}

Your job is to run a full contrast diagnostic. Format your response EXACTLY like this (keep all headers, no deviations):

## DIAGNOSTIC STAGE
[Give this company's failure trajectory a dramatic 3-6 word name in ALL CAPS that captures the core danger — e.g. THE BURNOUT PRECIPICE, THE PIVOT TRAP, THE CHURN SPIRAL, THE GROWTH ILLUSION, THE CASH CLIFF, THE IDENTITY VOID]

## SYSTEM SEVERITY SCORE
[Number only, 0-100, representing how close to failure this company is]

## PRIMARY OPERATIONAL BOTTLENECK
[One sentence — the single root cause most likely to kill this company right now]

## GHOST MATCH
[Name only of the single closest matching failure company from the database — the "historical ghost" this company is repeating]

## PATTERN MATCHES
[3 failure matches — for each: **Company name** — the specific parallel to this company's situation]

## SUCCESS BENCHMARKS
[2 success matches — for each: **Company name** — the specific decision or strategy they used that this company is missing or doing wrong]

## RISK SCORES
- Growth Risk: X%
- Brand Risk: X%
- UX Risk: X%
- Campaign Risk: X%
- Overall Failure Risk: X%

## DIAGNOSTIC REPORT
[Direct, clinical — what are the real threats, what is this company getting wrong, and what do the successful comparisons reveal about the gap]

## EXECUTION PLAN

**DAY 1-7:**
[3 immediate high-priority actions — specific, grounded in what the successful companies actually did]

**DAY 8-30:**
[3 medium-term actions — each grounded in what worked for the success benchmarks]

## SURVIVAL PROBABILITY WITH VEE GROUP INTERVENTION
X%
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    # Extract text — handle thinking-model responses where .text may be empty
    text = response.text or ""
    if not text and hasattr(response, 'candidates') and response.candidates:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text += part.text
    return text


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vee Group — Company Failure Diagnostic</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #070C1A;
  --card: #0D1528;
  --card2: #111A2E;
  --gold: #C9A84C;
  --gold2: #E8C96A;
  --text: #D4CCBB;
  --muted: #6B7A99;
  --border: rgba(201,168,76,0.18);
  --danger: #C0392B;
  --grid: rgba(201,168,76,0.04);
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  min-height: 100vh;
  overflow-x: hidden;
}

/* GRID OVERLAY */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
  z-index: 0;
}

/* NAV */
nav {
  position: relative;
  z-index: 10;
  padding: 28px 40px 24px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-logo {
  font-family: 'Cormorant Garamond', serif;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--gold2);
  text-transform: uppercase;
}

.nav-sub {
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 400;
}

.nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
}

.nav-tags {
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 100px;
  padding: 6px 14px;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--gold);
  font-family: 'JetBrains Mono', monospace;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gold);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%,100% { opacity:1; }
  50% { opacity:0.3; }
}

/* GOLD RULE */
.gold-rule {
  width: 40px;
  height: 1px;
  background: var(--gold);
  margin: 20px 40px;
  position: relative;
  z-index: 1;
}

/* MAIN */
.main {
  position: relative;
  z-index: 1;
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* PHASE CARD */
.phase-card {
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--card);
  margin-bottom: 16px;
  overflow: hidden;
}

.phase-header {
  padding: 20px 28px 16px;
  border-bottom: 1px solid var(--border);
}

.phase-label {
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--gold);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 6px;
}

.phase-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 28px;
  font-weight: 600;
  color: #E8E0D0;
  line-height: 1.1;
}

.phase-desc {
  font-size: 13px;
  color: var(--muted);
  margin-top: 6px;
  line-height: 1.6;
}

.phase-body {
  padding: 24px 28px;
}

/* FORM ELEMENTS */
.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.field-label {
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
}

.opt-tag {
  font-size: 9px;
  letter-spacing: 0.1em;
  color: var(--border);
  border: 1px solid var(--border);
  padding: 1px 5px;
  border-radius: 2px;
  margin-left: 6px;
  vertical-align: middle;
}

.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media(max-width:560px){ .field-row { grid-template-columns:1fr; } }

select, textarea {
  background: var(--bg);
  border: 1px solid rgba(201,168,76,0.2);
  border-radius: 3px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  padding: 12px 14px;
  outline: none;
  transition: border-color 0.2s;
  width: 100%;
}

select { cursor: pointer; appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%23C9A84C' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

select option { background: #0D1528; }
select:focus, textarea:focus { border-color: var(--gold); }
textarea::placeholder { color: var(--muted); }
textarea { resize: vertical; min-height: 130px; line-height: 1.6; }

/* CONSENT */
.consent-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(201,168,76,0.1);
  border-radius: 3px;
  background: rgba(201,168,76,0.03);
  margin-top: 14px;
}

.consent-row input[type="checkbox"] {
  margin-top: 2px;
  flex-shrink: 0;
  width: 15px;
  height: 15px;
  accent-color: var(--gold);
  cursor: pointer;
}

.consent-row label {
  font-size: 11px;
  line-height: 1.7;
  color: var(--muted);
  cursor: pointer;
}

.consent-row label a { color: var(--gold); text-decoration: underline; }

.data-notice {
  font-size: 10px;
  color: var(--muted);
  margin-top: 10px;
  letter-spacing: 0.04em;
  line-height: 1.6;
  opacity: 0.6;
}

/* RUN BUTTON */
.run-btn {
  width: 100%;
  margin-top: 18px;
  padding: 15px;
  background: transparent;
  border: 1px solid var(--gold);
  color: var(--gold);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.2s, color 0.2s;
}

.run-btn:hover { background: var(--gold); color: var(--bg); }
.run-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* LOADING */
.loading {
  display: none;
  text-align: center;
  padding: 60px 0;
}

.loading-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--muted);
  margin-top: 16px;
  text-align: center;
  animation: blink 1.4s ease-in-out infinite;
}

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* INTELLIGENCE PIPELINE (loading + results) */
.pipeline-card {
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 20px 22px;
  margin-bottom: 0;
}

.pipeline-results-card {
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 20px 22px;
}

.pipeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.pipeline-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--gold);
}

.pipeline-active-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--gold);
  animation: dot-pulse 1.2s ease-in-out infinite;
}

.pipeline-dot-gold {
  animation: none;
  background: var(--gold);
}

@keyframes dot-pulse {
  0%,80%,100%{ transform:scale(0.5); opacity:0.3; }
  40%{ transform:scale(1); opacity:1; }
}

.pipeline-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.pipeline-item:last-child { border-bottom: none; }

.pipeline-item-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  background: rgba(255,255,255,0.12);
  transition: background 0.4s ease;
}

.pipeline-item-dot.active { background: #2ECC71; }

.pipeline-item-info { flex: 1; }

.pipeline-item-name {
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
}

.pipeline-item-sub {
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  color: var(--muted);
  margin-top: 1px;
}

/* DIAGNOSTIC STAGE CARD */
.diag-stage-card {
  padding: 22px 26px;
  background: rgba(10,16,35,0.9);
  border: 1px solid rgba(192,57,43,0.3);
  border-left: 3px solid #C0392B;
  border-radius: 4px;
}

.diag-stage-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 6px;
}

.diag-stage-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #E05A4E;
  text-transform: uppercase;
  margin-bottom: 14px;
  line-height: 1.3;
}

.diag-score-row {
  margin-bottom: 8px;
}

.diag-score-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.diag-score-text strong { color: #E8E0D0; }

.diag-score-track {
  height: 4px;
  background: rgba(192,57,43,0.2);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 16px;
}

.diag-score-fill {
  height: 100%;
  border-radius: 2px;
  background: #C0392B;
  transition: width 1.4s cubic-bezier(0.16,1,0.3,1);
}

.diag-bottleneck-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #E05A4E;
  margin-bottom: 6px;
}

.diag-bottleneck-text {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
  font-weight: 500;
}

/* RESULTS */
.result { display: none; }

.result-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 28px;
  border-bottom: 1px solid var(--border);
}

.result-meta-left {}
.result-meta-label {
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--gold);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 4px;
}

.result-meta-company {
  font-family: 'Cormorant Garamond', serif;
  font-size: 20px;
  color: #E8E0D0;
}

.risk-badge {
  text-align: right;
}

.risk-badge-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 36px;
  font-weight: 500;
  color: var(--gold2);
  line-height: 1;
}

.risk-badge-label {
  font-size: 9px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--muted);
  margin-top: 4px;
}

/* CARD GAPS IN RESULT */
.diag-stage-card { margin: 20px 28px 0; }
.pipeline-results-card { margin: 14px 28px 14px; }

/* RESULT SECTIONS */
.result-section {
  padding: 22px 28px;
  border-bottom: 1px solid var(--border);
}

.result-section:last-child { border-bottom: none; }

.section-tag {
  font-size: 9px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--gold);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 12px;
  opacity: 0.8;
}

.section-body {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text);
}

.section-body p { margin-bottom: 10px; }
.section-body p:last-child { margin-bottom: 0; }
.section-body strong { color: #E8E0D0; font-weight: 600; }
.section-body em { color: var(--gold); font-style: normal; }

.success-section-inner {
  border-left: 2px solid var(--gold);
  padding-left: 16px;
}

/* RISK BARS */
.risk-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 4px;
}

.risk-item-label {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.06em;
  color: var(--muted);
  margin-bottom: 6px;
  text-transform: uppercase;
}

.risk-track {
  height: 2px;
  background: rgba(201,168,76,0.12);
  border-radius: 2px;
  overflow: hidden;
}

.risk-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--gold);
  transition: width 1.2s cubic-bezier(0.16,1,0.3,1);
}

/* SURVIVAL BOX */
.survival-box {
  margin: 0 28px 28px;
  border: 1px solid var(--border);
  padding: 22px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 3px;
  background: rgba(201,168,76,0.04);
}

.survival-label {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  line-height: 1.6;
}

.survival-num {
  font-family: 'Cormorant Garamond', serif;
  font-size: 52px;
  font-weight: 600;
  color: var(--gold2);
  line-height: 1;
}

.reset-btn {
  display: block;
  width: calc(100% - 56px);
  margin: 0 28px 28px;
  padding: 13px;
  background: transparent;
  border: 1px solid rgba(201,168,76,0.2);
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  cursor: pointer;
  border-radius: 3px;
  transition: border-color 0.2s, color 0.2s;
  text-align: center;
}

.reset-btn:hover { border-color: var(--gold); color: var(--gold); }

/* FOOTER */
footer {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 32px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--muted);
  letter-spacing: 0.1em;
  font-family: 'JetBrains Mono', monospace;
}

footer a { color: var(--muted); text-decoration: underline; }

/* COOKIE */
#cookie-banner {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  z-index: 9999;
  background: var(--card2);
  border-top: 1px solid var(--border);
  color: var(--muted);
  padding: 14px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 11px;
  font-family: 'Inter', sans-serif;
}

#cookie-banner p { margin:0; flex:1; min-width:200px; line-height:1.6; }
#cookie-banner p a { color: var(--gold); }
.cb-btns { display:flex; gap:8px; flex-shrink:0; }
.cb-btn {
  padding: 7px 16px;
  border-radius: 3px;
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
  cursor: pointer;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--muted);
  transition: 0.2s;
}
.cb-btn.primary { border-color: var(--gold); color: var(--gold); }
.cb-btn:hover { opacity: 0.7; }
</style>
</head>
<body>

<nav>
  <div class="nav-logo">Vee Group</div>
  <div class="nav-sub">Built on Human Behaviour</div>
  <div class="nav-row">
    <span class="nav-tags">Diagnostic Intelligence Platform &nbsp;·&nbsp; Business Growth Engineering</span>
    <div class="status-pill">
      <span class="status-dot"></span>
      1,982 Patterns &nbsp;·&nbsp; System Active
    </div>
  </div>
</nav>

<div class="gold-rule"></div>

<div class="main">

  <!-- INPUT PHASE -->
  <div class="phase-card" id="inputSection">
    <div class="phase-header">
      <div class="phase-label">Phase 01 &nbsp;·&nbsp; Client Intake</div>
      <div class="phase-title">Vee Archaeologist</div>
      <div class="phase-desc">Pattern Intelligence Engine — Historical Ghost Matching from 1,982 archived failures and 1,000 success benchmarks.</div>
    </div>
    <div class="phase-body">

      <div class="field-row">
        <div class="field-group">
          <div class="field-label">Industry <span class="opt-tag">Optional</span></div>
          <select id="industrySelect">
            <option value="">Select sector...</option>
            <option>B2B SaaS</option>
            <option>B2C SaaS</option>
            <option>FinTech</option>
            <option>AI / ML</option>
            <option>E-commerce / Marketplace</option>
            <option>HealthTech / MedTech</option>
            <option>EdTech</option>
            <option>HR Tech</option>
            <option>DevTools / Infrastructure</option>
            <option>Cybersecurity</option>
            <option>Data & Analytics</option>
            <option>Real Estate / PropTech</option>
            <option>ClimateTech / CleanTech</option>
            <option>LegalTech</option>
            <option>AgriTech</option>
            <option>Creator Economy</option>
            <option>Consumer App</option>
            <option>Deep Tech / Hardware</option>
            <option>Logistics / Supply Chain</option>
            <option>Travel / Hospitality Tech</option>
            <option>Media / AdTech</option>
            <option>Crypto / Web3</option>
            <option>Other</option>
          </select>
        </div>
        <div class="field-group">
          <div class="field-label">Stage <span class="opt-tag">Optional</span></div>
          <select id="stageSelect">
            <option value="">Select stage...</option>
            <option>Pre-Revenue / Idea</option>
            <option>MVP / Early Traction</option>
            <option>Seed / Pre-Seed</option>
            <option>Series A</option>
            <option>Series B</option>
            <option>Series C+</option>
            <option>Growth / Scale-Up</option>
            <option>Late Stage / Pre-IPO</option>
            <option>Bootstrapped / Profitable</option>
            <option>Turnaround / Distressed</option>
          </select>
        </div>
      </div>

      <div class="field-group">
        <div class="field-label">Company Profile</div>
        <textarea id="companyInput" placeholder="Describe your business — what you do, who your customers are, what you're struggling with, your biggest challenges right now. The more detail, the sharper the diagnosis."></textarea>
      </div>

      <div class="consent-row">
        <input type="checkbox" id="consentCheck" />
        <label for="consentCheck">I consent to Vee Group processing the information I submit here — including any industry, stage, and business description I provide — to generate a diagnostic report. I understand this input is analysed by Google Gemini AI as a data processor on Vee Group's behalf. This information is not retained by Vee Group after the response is returned. I have read and agree to the <a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a>. (Required — GDPR · UK GDPR · India DPDP Act 2023 · CCPA)</label>
      </div>
      <div class="data-notice">Your submission is transmitted to Google Gemini for analysis and discarded after the response is returned. No personal data is stored by Vee Group.</div>

      <button class="run-btn" onclick="diagnose()" id="diagnoseBtn">[ Run Diagnostic ]</button>
    </div>
  </div>

  <!-- LOADING -->
  <div class="loading" id="loading">
    <div class="loading-dots">
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
      <span class="loading-dot"></span>
    </div>
    <div class="loading-label" id="loadingLabel">Initialising Ghost Hunter…</div>
    <div class="pipeline-card" style="margin:18px auto 0;max-width:480px;">
      <div class="pipeline-header">
        <span class="pipeline-title">INTELLIGENCE PIPELINE</span>
        <span class="pipeline-active-dot" style="background:#2ECC71;box-shadow:0 0 6px #2ECC71;"></span>
      </div>
      <div class="pipeline-list" id="pipelineList"></div>
    </div>
  </div>

  <!-- RESULTS -->
  <div class="result phase-card" id="result">

    <div class="result-meta">
      <div class="result-meta-left">
        <div class="result-meta-label">Diagnostic Output</div>
        <div class="result-meta-company" id="companyLabel">—</div>
      </div>
      <div class="risk-badge">
        <div class="risk-badge-num" id="overallRisk">—</div>
        <div class="risk-badge-label">Overall Risk</div>
      </div>
    </div>

    <!-- DIAGNOSTIC STAGE CARD -->
    <div class="diag-stage-card" id="diagStageCard">
      <div class="diag-stage-label">DIAGNOSTIC STAGE</div>
      <div class="diag-stage-name" id="diagStageName">—</div>
      <div class="diag-score-row">
        <span class="diag-score-text">SYSTEM SEVERITY SCORE: <strong id="diagScore">—</strong>/100</span>
      </div>
      <div class="diag-score-track">
        <div class="diag-score-fill" id="diagScoreBar" style="width:0%"></div>
      </div>
      <div class="diag-bottleneck-label">PRIMARY OPERATIONAL BOTTLENECK</div>
      <div class="diag-bottleneck-text" id="diagBottleneck">—</div>
    </div>

    <!-- INTELLIGENCE PIPELINE -->
    <div class="pipeline-results-card">
      <div class="pipeline-header">
        <span class="pipeline-title">INTELLIGENCE PIPELINE</span>
        <span class="pipeline-active-dot pipeline-dot-gold"></span>
      </div>
      <div class="pipeline-list" id="pipelineResultsList"></div>
    </div>

    <div class="result-section">
      <div class="section-tag">Failure Pattern Matches</div>
      <div class="section-body" id="patternMatches"></div>
    </div>

    <div class="result-section">
      <div class="section-tag">Success Benchmarks — What the Winners Did Differently</div>
      <div class="section-body">
        <div class="success-section-inner" id="successBenchmarks"></div>
      </div>
    </div>

    <div class="result-section">
      <div class="section-tag">Risk Scores</div>
      <div class="risk-grid" id="riskBars"></div>
    </div>

    <div class="result-section">
      <div class="section-tag">Diagnostic Report</div>
      <div class="section-body" id="diagnosticReport"></div>
    </div>

    <div class="result-section">
      <div class="section-tag">Execution Plan — Next 30 Days</div>
      <div class="section-body" id="immediateActions"></div>
    </div>

    <div class="survival-box">
      <div class="survival-label">Survival Probability<br>with Vee Group Intervention</div>
      <div class="survival-num" id="survivalProb">—</div>
    </div>

    <button class="reset-btn" onclick="reset()">[ Run Another Diagnostic ]</button>

  </div>

</div>

<footer>
  Vee Group Graveyard Intelligence &nbsp;·&nbsp; Confidential Research &copy; 2026 &nbsp;·&nbsp;
  <a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a>
</footer>

<div id="cookie-banner" style="display:none;">
  <p>We use Google Fonts on this page, which may send a request to Google's servers. No advertising cookies or tracking pixels. <a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a>.</p>
  <div class="cb-btns">
    <button class="cb-btn primary" id="cb-accept">Accept</button>
    <button class="cb-btn" id="cb-decline">Decline</button>
  </div>
</div>

<script>
(function(){
  var KEY = 'vg_diag_cookie';
  if(!localStorage.getItem(KEY)){
    document.getElementById('cookie-banner').style.display = 'flex';
  }
  document.getElementById('cb-accept').addEventListener('click', function(){
    localStorage.setItem(KEY, 'accepted');
    document.getElementById('cookie-banner').style.display = 'none';
  });
  document.getElementById('cb-decline').addEventListener('click', function(){
    localStorage.setItem(KEY, 'declined');
    document.getElementById('cookie-banner').style.display = 'none';
  });
})();

async function diagnose() {
  var input = document.getElementById('companyInput').value.trim();
  var industry = document.getElementById('industrySelect').value;
  var stage = document.getElementById('stageSelect').value;

  if (!input) { alert('Please describe your company before running the diagnostic.'); return; }
  if (!document.getElementById('consentCheck').checked) {
    alert('Please read and accept the consent statement before running the diagnostic.');
    return;
  }
  if (input.length > 5000) { alert('Please limit your description to 5000 characters.'); return; }

  document.getElementById('inputSection').style.display = 'none';
  document.getElementById('loading').style.display = 'block';
  document.getElementById('result').style.display = 'none';
  document.getElementById('diagnoseBtn').disabled = true;
  try {
    var res = await fetch('/diagnose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company: input, industry: industry, stage: stage, consented: true })
    });
    var data = await res.json();
    if (data.error) { alert(data.error); reset(); return; }
    renderResult(data.result, input, industry, stage);
  } catch(e) {
    alert('Something went wrong. Please try again.');
    reset();
  }
}

function md(text) {
  if (!text) return '';
  var nl = String.fromCharCode(10);
  var nlRe = new RegExp(nl + '{2,}', 'g');
  var nlSingle = new RegExp(nl, 'g');
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^(\d+)\.\s+/gm, '<span style="font-weight:600;color:#C9A84C;margin-right:6px;">$1.</span>')
    .replace(/^[-\u2022]\s+/gm, '<span style="color:#C9A84C;margin-right:6px;">&mdash;</span>')
    .replace(nlRe, '</p><p>')
    .replace(nlSingle, '<br>')
    .replace(/^/, '<p>').replace(/$/, '</p>');
}

function extractSection(text, keywords, nextKeywords) {
  var t = text;
  var si = -1, headerLen = 0;
  for (var i = 0; i < keywords.length; i++) {
    var kw = keywords[i];
    var tries = ['## ' + kw, '### ' + kw, '# ' + kw, '**' + kw + '**', kw];
    for (var j = 0; j < tries.length; j++) {
      var idx = t.toUpperCase().indexOf(tries[j].toUpperCase());
      if (idx !== -1) { si = idx; headerLen = tries[j].length; break; }
    }
    if (si !== -1) break;
  }
  if (si === -1) return '';
  var from = si + headerLen;
  var ei = t.length;
  for (var i = 0; i < nextKeywords.length; i++) {
    var nk = nextKeywords[i];
    var tries = ['## ' + nk, '### ' + nk, '# ' + nk, '**' + nk + '**', nk];
    for (var j = 0; j < tries.length; j++) {
      var idx = t.toUpperCase().indexOf(tries[j].toUpperCase(), from);
      if (idx !== -1 && idx < ei) { ei = idx; break; }
    }
  }
  return t.substring(from, ei).trim();
}

var _pipelineTimer = null;

var PIPELINE_MODULES = [
  { name: 'Ghost Hunter',       sub: 'Historical failure matching' },
  { name: 'Distress Engine',    sub: 'Severity scoring' },
  { name: 'Behavioural Lab',    sub: 'DISC · OCAI · ADKAR analysis' },
  { name: 'Intervention Arch.', sub: 'Kill list & fixer profile' },
  { name: 'Forensic CFO',       sub: 'Burn multiple & runway calc' },
  { name: 'Matchmaker',         sub: '90-day execution roadmap' },
  { name: 'Report Generator',   sub: 'Client report & expert brief' },
  { name: 'Learning Engine',    sub: 'Persisting case patterns' },
  { name: 'Strategy Oracle',    sub: 'Long-range scenario modelling' }
];

function buildPipelineHtml(activeCount, subtitles) {
  subtitles = subtitles || {};
  var html = '';
  PIPELINE_MODULES.forEach(function(m, i) {
    var dotCls = i < activeCount ? 'pipeline-item-dot active' : 'pipeline-item-dot';
    var sub = subtitles[m.name] !== undefined ? subtitles[m.name] : m.sub;
    html += '<div class="pipeline-item">' +
      '<div class="' + dotCls + '"></div>' +
      '<div class="pipeline-item-info">' +
        '<div class="pipeline-item-name">' + m.name + '</div>' +
        '<div class="pipeline-item-sub">' + sub + '</div>' +
      '</div></div>';
  });
  return html;
}

var LOADING_LABELS = [
  'Initialising Ghost Hunter...',
  'Matching historical failure patterns...',
  'Running Distress Engine...',
  'Scoring system severity...',
  'Activating Behavioural Lab...',
  'Running DISC · OCAI analysis...',
  'Building Intervention Architecture...',
  'Engaging Forensic CFO...',
  'Calculating burn multiple & runway...',
  'Running Matchmaker...',
  'Generating execution roadmap...',
  'Compiling Diagnostic Report...',
  'Finalising Learning Engine...',
  'Running Strategy Oracle — scenario modelling...'
];

function startPipelineAnimation() {
  var listEl = document.getElementById('pipelineList');
  var labelEl = document.getElementById('loadingLabel');
  if (listEl) listEl.innerHTML = buildPipelineHtml(0);
  var step = 0;
  var labelStep = 0;
  _pipelineTimer = setInterval(function() {
    step++;
    labelStep++;
    if (step > PIPELINE_MODULES.length) step = PIPELINE_MODULES.length;
    if (labelStep >= LOADING_LABELS.length) labelStep = LOADING_LABELS.length - 1;
    if (listEl) listEl.innerHTML = buildPipelineHtml(step);
    if (labelEl) labelEl.textContent = LOADING_LABELS[labelStep];
  }, 1800);
}

function stopPipelineAnimation() {
  if (_pipelineTimer) { clearInterval(_pipelineTimer); _pipelineTimer = null; }
}

function renderResult(text, input, industry, stage) {
  stopPipelineAnimation();
  document.getElementById('loading').style.display = 'none';
  document.getElementById('result').style.display = 'block';

  var label = input.substring(0, 55) + '\u2026';
  if (industry || stage) {
    label = [industry, stage].filter(Boolean).join(' \u00b7 ') + ' \u2014 ' + label;
  }
  document.getElementById('companyLabel').textContent = label;

  // Populate diagnostic stage card
  var diagStage   = extractSection(text, ['DIAGNOSTIC STAGE'], ['SYSTEM SEVERITY SCORE','GHOST MATCH','PATTERN MATCHES']);
  var severityRaw = extractSection(text, ['SYSTEM SEVERITY SCORE'], ['PRIMARY OPERATIONAL BOTTLENECK','GHOST MATCH','PATTERN MATCHES']);
  var bottleneck  = extractSection(text, ['PRIMARY OPERATIONAL BOTTLENECK'], ['GHOST MATCH','PATTERN MATCHES']);
  var ghostMatch  = extractSection(text, ['GHOST MATCH'], ['PATTERN MATCHES']);

  var stageEl = document.getElementById('diagStageName');
  var bottleneckEl = document.getElementById('diagBottleneck');
  var scoreEl = document.getElementById('diagScore');
  var scoreBarEl = document.getElementById('diagScoreBar');
  var pipelineEl = document.getElementById('pipelineResultsList');

  if (stageEl) stageEl.textContent = diagStage.trim().replace(/\*\*/g, '') || '—';
  if (bottleneckEl) bottleneckEl.textContent = bottleneck.trim() || '—';

  var scoreMatch = severityRaw.match(/(\d+)/);
  var scoreVal = scoreMatch ? parseInt(scoreMatch[1]) : 0;
  if (scoreEl) scoreEl.textContent = scoreVal || '—';
  if (scoreBarEl) setTimeout(function() { scoreBarEl.style.width = Math.min(scoreVal, 100) + '%'; }, 100);

  var ghost = ghostMatch.trim().replace(/\*\*/g, '');
  var subs = {
    'Ghost Hunter': ghost || 'Historical failure matching',
    'Distress Engine': scoreVal ? 'Score: ' + scoreVal + '/100' : 'Severity scoring'
  };
  if (pipelineEl) pipelineEl.innerHTML = buildPipelineHtml(9, subs);

  var patterns  = extractSection(text, ['PATTERN MATCHES'], ['SUCCESS BENCHMARKS','RISK SCORES']);
  var successes = extractSection(text, ['SUCCESS BENCHMARKS'], ['RISK SCORES','DIAGNOSTIC REPORT']);
  var risks     = extractSection(text, ['RISK SCORES'], ['DIAGNOSTIC REPORT']);
  var report    = extractSection(text, ['DIAGNOSTIC REPORT'], ['EXECUTION PLAN','IMMEDIATE ACTIONS']);
  var actions   = extractSection(text, ['EXECUTION PLAN','IMMEDIATE ACTIONS'], ['SURVIVAL PROBABILITY']);
  var survival  = extractSection(text, ['SURVIVAL PROBABILITY WITH VEE GROUP INTERVENTION','SURVIVAL PROBABILITY'], []);

  var allEmpty = !patterns && !successes && !report && !actions;
  document.getElementById('patternMatches').innerHTML  = md(patterns || (allEmpty ? text : ''));
  document.getElementById('successBenchmarks').innerHTML = md(successes);
  document.getElementById('diagnosticReport').innerHTML  = md(report);
  document.getElementById('immediateActions').innerHTML  = md(actions);

  var riskSource = risks || text;
  var cats = ['Growth','Brand','UX','Campaign','Overall'];
  var barsHtml = '';
  var overallVal = '\u2014';

  cats.forEach(function(cat) {
    var re = new RegExp(cat + '[^\\n]*?(\\d+)%', 'i');
    var m = riskSource.match(re);
    if (m) {
      var val = parseInt(m[1]);
      if (cat === 'Overall') {
        overallVal = val + '%';
      } else {
        var colour = val >= 75 ? '#C0392B' : val >= 50 ? '#E67E22' : '#27AE60';
        barsHtml += '<div>' +
          '<div class="risk-item-label"><span>' + cat + ' Risk</span><span>' + val + '%</span></div>' +
          '<div class="risk-track"><div class="risk-fill" style="width:' + val + '%;background:' + colour + '"></div></div>' +
          '</div>';
      }
    }
  });

  document.getElementById('overallRisk').textContent = overallVal;
  document.getElementById('riskBars').innerHTML = barsHtml;

  var sm = (survival || text).match(/(\d+)%/);
  document.getElementById('survivalProb').textContent = sm ? sm[1] + '%' : '\u2014';
}

function reset() {
  document.getElementById('inputSection').style.display = 'block';
  document.getElementById('loading').style.display = 'none';
  document.getElementById('result').style.display = 'none';
  document.getElementById('diagnoseBtn').disabled = false;
  document.getElementById('companyInput').value = '';
  document.getElementById('industrySelect').value = '';
  document.getElementById('stageSelect').value = '';
  document.getElementById('consentCheck').checked = false;
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/diagnose', methods=['POST'])
def diagnose():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    company_input = data.get('company', '').strip()
    if not company_input:
        return jsonify({'error': 'No input provided'}), 400
    if len(company_input) > 5000:
        return jsonify({'error': 'Input too long. Please limit to 5000 characters.'}), 400
    if not data.get('consented', False):
        return jsonify({'error': 'Consent required'}), 403
    industry = data.get('industry', '').strip()
    stage = data.get('stage', '').strip()
    try:
        result = diagnose_company(company_input, industry, stage)
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    if not result:
        return jsonify({'error': 'The AI returned an empty response. Please try again.'}), 500
    return jsonify({'result': result})


PRIVACY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Privacy Policy | Vee Group Diagnostic System</title>
<meta name="robots" content="noindex">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Inter', sans-serif; background: #fff9f0; color: #081f5c; min-height: 100vh; }
  nav { background: #081f5c; padding: 20px 48px; display: flex; align-items: center; justify-content: space-between; }
  nav .logo { color: #fff9f0; font-size: 18px; font-weight: 700; letter-spacing: 0.05em; }
  nav a { color: #edf1f6; font-size: 12px; opacity: 0.7; text-decoration: none; letter-spacing: 0.06em; }
  nav a:hover { opacity: 1; }
  .hero { background: #081f5c; padding: 52px 48px 40px; }
  .hero .eyebrow { color: #edf1f6; font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; opacity: 0.5; margin-bottom: 10px; }
  .hero h1 { color: #fff9f0; font-size: 36px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 10px; }
  .hero .meta { color: #edf1f6; font-size: 13px; opacity: 0.5; }
  .body { max-width: 760px; margin: 0 auto; padding: 56px 24px 80px; }
  .section { margin-bottom: 44px; }
  .section h2 { font-size: 18px; font-weight: 600; padding-bottom: 10px; border-bottom: 1px solid rgba(8,31,92,0.12); margin-bottom: 16px; }
  .section h3 { font-size: 13px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.55; margin: 20px 0 8px; }
  .section p { font-size: 15px; line-height: 1.8; margin-bottom: 12px; opacity: 0.85; }
  .section ul { padding-left: 20px; margin-bottom: 12px; }
  .section ul li { font-size: 15px; line-height: 1.8; margin-bottom: 6px; opacity: 0.85; }
  .section a { color: #081f5c; }
  .flag-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 16px; }
  .flag { background: #f2f0de; border: 1px solid rgba(8,31,92,0.1); border-radius: 10px; padding: 16px; }
  .flag .country { font-size: 10px; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; opacity: 0.5; margin-bottom: 6px; }
  .flag p { font-size: 13px; line-height: 1.65; margin: 0; opacity: 0.8; }
  footer { background: #081f5c; text-align: center; padding: 28px; color: #edf1f6; font-size: 13px; }
  footer a { color: #edf1f6; text-decoration: underline; opacity: 0.8; }
  @media(max-width: 560px) { .flag-grid { grid-template-columns: 1fr; } .hero { padding: 40px 24px 32px; } .hero h1 { font-size: 28px; } nav { padding: 16px 20px; } }
</style>
</head>
<body>

<nav>
  <div class="logo">VEE GROUP</div>
  <a href="/">← Back to Diagnostic</a>
</nav>

<div class="hero">
  <div class="eyebrow">Legal</div>
  <h1>Privacy Policy</h1>
  <div class="meta">Effective date: 8 June 2026 &nbsp;·&nbsp; Last updated: 8 June 2026</div>
</div>

<div class="body">

  <div class="section">
    <h2>1. Who we are</h2>
    <p>Vee Group is a Business Growth Engineering firm operating from New Delhi, India and the United Kingdom. This privacy policy applies to the Vee Group Diagnostic System, which allows users to submit a description of their business for AI-powered failure pattern analysis.</p>
    <p>Contact: <a href="mailto:info@veegroup.in">info@veegroup.in</a> &nbsp;·&nbsp; +91 85959 99212</p>
  </div>

  <div class="section">
    <h2>2. What data we collect and why</h2>
    <p>When you use the diagnostic tool, you may provide:</p>
    <ul>
      <li><strong>Industry category</strong> (optional dropdown selection)</li>
      <li><strong>Business stage</strong> (optional dropdown selection)</li>
      <li><strong>Free-text business description</strong> — which may include business name, revenue, funding details, operational context, or other information you choose to share</li>
    </ul>
    <p>We collect this solely to generate a diagnostic report in response to your request. We do not ask for or require personal contact information (name, email, phone) to use the tool.</p>
  </div>

  <div class="section">
    <h2>3. Third-party data processor — Google Gemini AI</h2>
    <p>Your submission (including industry, stage, and description) is transmitted to <strong>Google Gemini</strong> (operated by Google LLC) for AI analysis. Google acts as a data processor on our behalf. <strong>Vee Group does not store your submission</strong> — it is held in memory only for the duration of the API call and discarded immediately after the response is returned.</p>
    <p>Google's data processing terms apply to their handling of API inputs. See <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google's Privacy Policy</a>.</p>
    <p>By ticking the consent checkbox before running the diagnostic, you acknowledge that your input will be processed by Google Gemini as described above.</p>
  </div>

  <div class="section">
    <h2>4. Legal basis for processing</h2>
    <div class="flag-grid">
      <div class="flag">
        <div class="country">India — DPDP Act 2023</div>
        <p>Processing is based on your <strong>explicit consent</strong>, given via the checkbox before submitting. You may withdraw consent at any time by not using the tool.</p>
      </div>
      <div class="flag">
        <div class="country">EU — GDPR (Art. 6)</div>
        <p>Lawful basis: <strong>Consent</strong> (Art. 6(1)(a)). You provide consent before submitting your business description for analysis.</p>
      </div>
      <div class="flag">
        <div class="country">United Kingdom — UK GDPR</div>
        <p>Same basis as EU GDPR, applied under retained UK law. You have the same rights as EU data subjects.</p>
      </div>
      <div class="flag">
        <div class="country">California, USA — CCPA / CPRA</div>
        <p>We do <strong>not sell or share</strong> personal information. You have the right to know what we collect and to request deletion.</p>
      </div>
      <div class="flag">
        <div class="country">Canada — PIPEDA</div>
        <p>We collect personal information only with your consent and use it only for the stated purpose — generating your diagnostic report.</p>
      </div>
      <div class="flag">
        <div class="country">Australia — Privacy Act 1988</div>
        <p>We handle personal information in accordance with the Australian Privacy Principles. You may request access or correction at any time.</p>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>5. Data retention</h2>
    <p>Vee Group retains <strong>no copy</strong> of your diagnostic submission. The text you enter and any dropdown selections are transmitted to Google Gemini, the response is rendered in your browser, and the data is not written to any Vee Group database or file storage.</p>
    <p>Server access logs (standard infrastructure logs from Google Cloud Run) may record the time and IP address of your request for up to 30 days as part of standard platform operation. These logs do not contain your submission text or dropdown selections.</p>
  </div>

  <div class="section">
    <h2>6. Cookies and tracking</h2>
    <p>This application uses <strong>no advertising cookies</strong> and <strong>no third-party tracking pixels</strong>. We load typefaces via Google Fonts, which may result in a request to Google's servers when the page loads. A cookie consent preference is stored in your browser's <code>localStorage</code> (key: <code>vg_diag_cookie</code>) to avoid showing the banner on repeat visits. This is a functional preference store — no personal data is contained in it.</p>
  </div>

  <div class="section">
    <h2>7. Your rights</h2>
    <p>Depending on your jurisdiction, you have the right to access, correct, delete, or restrict the processing of your personal data, and to withdraw consent at any time. Since Vee Group does not store your submission, there is typically no data held by us to act on. For any rights requests or concerns, write to <a href="mailto:info@veegroup.in">info@veegroup.in</a>.</p>
  </div>

  <div class="section">
    <h2>8. Children</h2>
    <p>This tool is intended for business founders and leaders. We do not knowingly collect data from individuals under 18. If you believe a minor has used this tool, contact us and we will investigate promptly.</p>
  </div>

  <div class="section">
    <h2>9. Supervisory authorities</h2>
    <ul>
      <li><strong>India:</strong> Data Protection Board of India (under DPDP Act 2023)</li>
      <li><strong>EU:</strong> Your national Data Protection Authority</li>
      <li><strong>UK:</strong> Information Commissioner's Office — <a href="https://ico.org.uk" target="_blank" rel="noopener">ico.org.uk</a></li>
      <li><strong>Australia:</strong> OAIC — <a href="https://oaic.gov.au" target="_blank" rel="noopener">oaic.gov.au</a></li>
    </ul>
  </div>

  <div class="section">
    <h2>10. Changes to this policy</h2>
    <p>We may update this policy when our practices change or when law requires it. The effective date at the top will always reflect the most recent version.</p>
  </div>

  <div class="section">
    <h2>11. Contact</h2>
    <ul>
      <li><strong>Email:</strong> <a href="mailto:info@veegroup.in">info@veegroup.in</a></li>
      <li><strong>Phone:</strong> +91 85959 99212</li>
      <li><strong>Address:</strong> Vee Group, New Delhi, India</li>
    </ul>
  </div>

</div>

<footer>
  © 2026 Vee Group &nbsp;·&nbsp; New Delhi &nbsp;·&nbsp; United Kingdom &nbsp;·&nbsp;
  <a href="/">Diagnostic System</a>
</footer>

</body>
</html>
"""

@app.route('/privacy')
def privacy():
    return render_template_string(PRIVACY_HTML)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
