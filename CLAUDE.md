# CLAUDE.md — ATS-GOD Optimizer Codebase Guide

This file provides AI assistants with everything needed to understand, develop, and maintain the **ATS-GOD v4.0** codebase effectively.

---

## Project Overview

ATS-GOD is a Streamlit-based web application that optimizes CVs against job descriptions using **9 specialized AI agents**. It supports three LLM providers (Groq, OpenAI, Anthropic) and falls back to rule-based analysis when no API key is present.

**Primary use case:** A user uploads a CV and pastes a job description → the system runs 9 agents in parallel → produces a scored report, 3 CV variants, prioritized action items, and an optional cover letter.

---

## Repository Structure

```
ats-god-optimizer/
├── app.py                          # Streamlit UI entry point (~400 lines)
├── requirements.txt                # All Python dependencies
├── .env.example                    # API key configuration template
├── .github/
│   └── workflows/ci.yml            # GitHub Actions CI pipeline
├── .devcontainer/                  # Dev container configuration
├── src/
│   ├── agents/                     # 9 specialized AI agent modules
│   │   ├── base_agent.py           # BaseAgent class + AgentOutput schema
│   │   ├── algorithm_breaker.py    # Agent 1: ATS algorithm analysis
│   │   ├── sa_specialist.py        # Agent 2: South African market
│   │   ├── global_setter.py        # Agent 3: International/GDPR
│   │   ├── recruiter_scanner.py    # Agent 4: 6-second recruiter scan
│   │   ├── hiring_manager_whisperer.py  # Agent 5: Technical credibility
│   │   ├── semantic_matcher.py     # Agent 6: NLP/TF-IDF semantic gap
│   │   ├── compliance_guardian.py  # Agent 7: GDPR/POPIA legal checks
│   │   ├── future_architect.py     # Agent 8: Career trajectory/2025 skills
│   │   └── cover_letter_agent.py   # Agent 9: Cover letter generation
│   └── core/
│       ├── orchestrator.py         # Master orchestrator (parallel agent runner)
│       └── exporter.py             # TXT/DOCX export utilities
└── tests/
    └── test_agents.py              # 16 test functions (pytest + pytest-asyncio)
```

> **Note:** `src/agents/career_scanner.py` and `src/core/interview_orchestrator.py` exist but are not used in the main application flow.

---

## Development Commands

### Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in API keys
```

### Run the Application
```bash
streamlit run app.py
```

### Run Tests
```bash
pytest tests/ -v
# Tests run in rule-based mode — no API key needed
```

### CI Pipeline

Tests are automatically run by GitHub Actions on every push to `main` and on PRs targeting `main`. Steps:
1. Setup Python 3.11
2. Install dependencies
3. Run `pytest tests/ -v`
4. Verify all module imports
5. Syntax-check `app.py`

---

## Environment Configuration

Copy `.env.example` to `.env` and fill in at least one provider:

```
GROQ_API_KEY=gsk_...           # Recommended: free tier available
GROQ_MODEL=llama-3.3-70b-versatile

OPENAI_API_KEY=sk-...          # Optional fallback
OPENAI_MODEL=gpt-4o-mini

ANTHROPIC_API_KEY=sk-ant-...   # Optional fallback

APP_ENV=development
LOG_LEVEL=INFO
```

**LLM Provider Priority (auto-detected at runtime):**
1. Groq (free, recommended)
2. OpenAI
3. Anthropic
4. Rule-based mode (no API key required)

Never commit a `.env` file. Placeholder strings like `your_key_here` are explicitly rejected at runtime.

---

## Architecture

### Agent System

Every agent inherits from `BaseAgent` (`src/agents/base_agent.py`) and implements:

```python
async def analyze(self, cv_text: str, jd_text: str, context: dict) -> AgentOutput
```

`AgentOutput` is a Pydantic model:

```python
class AgentOutput(BaseModel):
    agent_name: str
    score: int              # 0-100
    findings: List[str]     # 3-5 items
    recommendations: List[str]  # 5-8 items
    optimized_content: str  # AI-generated suggestion
    raw_analysis: str       # Full LLM response
    weight: float           # Scoring weight
```

Each agent has a **rule-based fallback** that activates when no LLM is available.

### Orchestrator

`ATSGodOrchestrator` in `src/core/orchestrator.py`:
- Detects the LLM provider once at initialization
- Runs all 8 optimization agents concurrently via `asyncio.gather`
- Applies a **90-second timeout** per agent
- Computes weighted scores (weights vary by target market)
- Generates 3 CV variants and (optionally) a cover letter
- Returns a structured result dictionary

**Market-based scoring weights:**

| Agent | South Africa | International | Both |
|---|---|---|---|
| algorithm_breaker | 1.8 | 1.8 | 1.8 |
| sa_specialist | 2.0 | 0.5 | 1.4 |
| global_setter | 0.8 | 2.0 | 1.4 |
| compliance_guardian | 1.5 | 1.0 | 1.2 |
| semantic_matcher | 1.1 | 1.5 | 1.3 |

### Orchestrator Result Schema

```python
{
    "summary": {
        "overall_score": float,
        "recommended_variant": str,   # "ATS-MAX" | "BALANCED" | "CREATIVE"
        "verdict": str,
        "interview_probability": int, # 0-95
        "agent_scores": {str: int},
        "weakest_area": str,
        "strongest_area": str,
        "target_market": str,
    },
    "agent_results": {str: AgentOutput},
    "cv_variants": {"ats_max": str, "balanced": str, "creative": str},
    "cover_letter": str,
    "action_items": [str],        # Max 15, prioritized
    "ai_mode": bool,
    "llm_provider": str,
    "llm_model": str,
    "metadata": {
        "execution_seconds": float,
        "timestamp": str,
        "version": "4.0.0",
        "agents_run": int,
    }
}
```

### Streamlit App (`app.py`)

Key functions:
- `read_pdf(file)` — dual parsing: PyPDF2 → pdfplumber fallback
- `read_docx(file)` — extracts paragraphs and table cells
- `detect_available_llm()` — checks env vars in priority order
- `render_sidebar()` — target market, experience, industry, role inputs
- `render_results(results)` — renders metrics, agent scores, CV tabs, downloads
- `main()` — top-level Streamlit entrypoint

### Exporter (`src/core/exporter.py`)

- `export_to_txt(results) -> str` — plain text, no extra dependencies
- `export_to_docx(results) -> Optional[bytes]` — formatted Word document; silently returns `None` if `python-docx` is unavailable

---

## Agent Responsibilities (Quick Reference)

| # | Agent | Key Role | Weight Range |
|---|---|---|---|
| 1 | `AlgorithmBreaker` | ATS parser compatibility, keyword match rate | 1.8 |
| 2 | `SouthAfricanSpecialist` | B-BBEE, NQF, Employment Equity, SA keywords | 0.5–2.0 |
| 3 | `GlobalStandardSetter` | GDPR, international sections, Fortune 500 standards | 0.8–2.0 |
| 4 | `RecruiterScanner` | 6-second scan, killer phrases, power verbs, metrics density | 1.3 |
| 5 | `HiringManagerWhisperer` | Technical credibility, vague phrase detection | 1.2 |
| 6 | `SemanticMatcher` | TF-IDF cosine similarity, skill ontology, tone alignment | 1.1–1.5 |
| 7 | `ComplianceGuardian` | GDPR/POPIA violations, discrimination, exaggerations | 1.0–1.5 |
| 8 | `FutureProofArchitect` | Emerging skills (2025), career trajectory positioning | 0.9 |
| 9 | `CoverLetterAgent` | 250-350 word personalized cover letter | N/A |

---

## Key Conventions

### Adding a New Agent

1. Create `src/agents/my_new_agent.py` inheriting `BaseAgent`
2. Implement `async analyze(self, cv_text, jd_text, context) -> AgentOutput`
3. Add a rule-based fallback path requiring no LLM
4. Register in `ATSGodOrchestrator.__init__()` and the agent run list
5. Add market-based weight entries in the orchestrator's weight dictionaries
6. Wire up a display card in `render_results()` in `app.py`
7. Add at least 2 test cases in `tests/test_agents.py`

### Modifying an Existing Agent

- Keep the `AgentOutput` schema unchanged unless updating the Pydantic model
- Always update the rule-based fallback to match any LLM prompt changes
- Scores must remain in the 0-100 range
- `findings`: 3-5 items; `recommendations`: 5-8 items

### LLM Calls

- CV text capped at 3500 chars, JD text capped at 2000 chars before sending to LLM
- Use system prompt + user prompt pattern
- Parse LLM output with regex (key:value or section headers) — do not assume JSON
- Wrap all LLM calls with timeout and fallback logic

### Testing

- All tests must pass with `GROQ_API_KEY` unset (rule-based mode only)
- Use `pytest-asyncio` for async test functions
- Test both "clean" and "violation" paths for agents that detect issues
- Do not add integration tests that require real API keys to CI

### Imports and PYTHONPATH

Project root is the Python path. Imports use:
```python
from src.agents.algorithm_breaker import AlgorithmBreaker
from src.core.orchestrator import ATSGodOrchestrator
```

The CI pipeline sets `PYTHONPATH=.` before running tests.

---

## ATS Detection Heuristics

**CV black flags (Agent 1):** markdown tables, excessive tabs, special characters, headers/footers, image placeholders

**CV killer phrases (Agent 4):** "responsible for", "duties included", "worked on", "involved in", "helped with", "assisted with", "contributed to", "participated in"

**Power verbs (Agent 4, 20+ tracked):** Spearheaded, Delivered, Transformed, Exceeded, Optimized, Engineered, Architected, Scaled, Generated, Reduced, Led, Launched, Built, Drove, Achieved, Increased, Decreased, Saved, Negotiated, Established, Implemented

**SA-specific keywords (Agent 2, 16 tracked):** B-BBEE, Employment Equity, SETA, NQF, SAQA, LRA, BCEA, OHSA, Critical Skills, Skills Development, Transformation, PNet, Careers24, South Africa, Cape Town, Johannesburg

**Emerging 2025 skills (Agent 8, 20 tracked):** Generative AI, LLM, Prompt Engineering, GitHub Copilot, Power BI, Tableau, ESG, OKR, Remote Leadership, Python, Automation, API, No-code, Low-code, Cloud Native, Kubernetes, Terraform, Data-driven

---

## Scoring Logic

```python
# Weighted average of 8 agent scores
overall_score = sum(score * weight for ...) / sum(weights)

# CV variant recommendation
if overall_score >= 82:   recommended_variant = "BALANCED"
elif overall_score >= 65: recommended_variant = "ATS-MAX"
else:                     recommended_variant = "ATS-MAX"

# Interview probability
interview_probability = min(95, int(overall_score * 0.88 + 8))

# Action item urgency (for sorting)
urgency = 1.0 + (100 - agent_score) / 40
```

---

## Known Unused Files

Do not integrate these without explicit direction:
- `src/agents/career_scanner.py`
- `src/core/interview_orchestrator.py`

---

## Dependencies Summary

| Category | Libraries |
|---|---|
| LLM | langchain, langchain-groq, langchain-openai, langchain-anthropic, groq, openai, anthropic |
| Document parsing | python-docx, PyPDF2, pdfplumber |
| NLP/ML | scikit-learn (TF-IDF), textstat |
| Web UI | streamlit |
| Utilities | python-dotenv, pydantic, tenacity |
| Testing | pytest, pytest-asyncio |

---

## Git Workflow

Development branches follow the pattern `claude/<descriptor>-<session-id>`. Always commit to the designated branch and push with:

```bash
git push -u origin <branch-name>
```

Write clear, descriptive commit messages. Never push directly to `master` or `main`.
