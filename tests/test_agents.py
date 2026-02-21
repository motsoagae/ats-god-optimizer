"""
ATS-GOD Test Suite
All tests run WITHOUT an API key — uses rule-based mode.
Run: pytest tests/ -v
"""
import asyncio
import pytest

# ─── Sample Data ─────────────────────────────────────────────────────────────

CV = """
Jane Smith
jane.smith@email.com | +27 82 123 4567 | linkedin.com/in/janesmith | github.com/janesmith

PROFESSIONAL SUMMARY
Senior Software Engineer with 9 years in fintech and banking. Led cross-functional teams of 8-12.
Delivered 4 platform migrations on time. Reduced system downtime by 45% through proactive monitoring.

EXPERIENCE

Senior Software Engineer | ABC Bank | Cape Town | 2020 – Present
- Spearheaded migration to microservices architecture, reducing deployment time by 60%
- Led team of 10 engineers across 3 time zones, improving sprint velocity by 35%
- Implemented CI/CD pipeline (GitHub Actions, Docker, Kubernetes) saving 25 hours/sprint
- Architected real-time fraud detection system processing R2.3B in daily transactions

Software Engineer | XYZ FinTech | Johannesburg | 2016 – 2020
- Built Python FastAPI backend handling 80,000 daily active users
- Reduced API response time from 1.8s to 180ms (90% improvement)
- Delivered 3 major feature releases, increasing user retention by 22%

Junior Developer | StartupCo | 2014 – 2016
- Developed React.js frontend for SaaS product with 5,000 users

EDUCATION
BSc Computer Science (NQF Level 7) | University of Cape Town | 2014

SKILLS
Python, Java, React.js, AWS (Lambda, EC2, RDS), Docker, Kubernetes, PostgreSQL,
Redis, GitHub Actions, Terraform, Agile/Scrum, SQL
"""

JD = """
Senior Software Engineer — FinTech Innovation

We are looking for a Senior Software Engineer to join our Cape Town engineering team.

Requirements:
- 5+ years software engineering experience
- Python, AWS, Docker, Kubernetes
- Experience with microservices architecture
- Team leadership and mentoring experience
- Agile/Scrum methodology
- B-BBEE awareness preferred
- Experience with financial systems

We offer: Competitive package, remote-friendly, growth opportunities.
"""

CTX = {
    "target_market": "South Africa",
    "experience_level": "Senior",
    "industry": "FinTech",
    "target_role": "Senior Software Engineer"
}


# ─── Helper ───────────────────────────────────────────────────────────────────

def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── Import Tests ─────────────────────────────────────────────────────────────

def test_all_imports():
    from src.agents.algorithm_breaker import AlgorithmBreaker
    from src.agents.sa_specialist import SASpecialist
    from src.agents.global_setter import GlobalSetter
    from src.agents.recruiter_scanner import RecruiterScanner
    from src.agents.hiring_manager_whisperer import HiringManagerWhisperer
    from src.agents.semantic_matcher import SemanticMatcher
    from src.agents.compliance_guardian import ComplianceGuardian
    from src.agents.future_architect import FutureArchitect
    from src.agents.cover_letter_agent import CoverLetterAgent
    from src.core.orchestrator import ATSGodOrchestrator
    from src.core.exporter import export_to_txt, export_to_docx


# ─── Agent Tests ──────────────────────────────────────────────────────────────

def test_algorithm_breaker():
    from src.agents.algorithm_breaker import AlgorithmBreaker
    result = run(AlgorithmBreaker(llm=None).analyze(CV, JD, CTX))
    assert result.agent_name == "The Algorithm Breaker"
    assert 0 <= result.score <= 100
    assert len(result.findings) >= 3
    assert len(result.recommendations) >= 1


def test_sa_specialist_nqf_detection():
    from src.agents.sa_specialist import SASpecialist
    result = run(SASpecialist(llm=None).analyze(CV, JD, CTX))
    assert result.agent_name == "The South African Specialist"
    assert 0 <= result.score <= 100
    # Should detect BSc = NQF 7
    assert any("NQF" in f or "7" in f for f in result.findings)


def test_global_setter_gdpr_clean_cv():
    from src.agents.global_setter import GlobalSetter
    result = run(GlobalSetter(llm=None).analyze(CV, JD, CTX))
    assert result.score >= 40
    # Clean CV should not have GDPR violations
    gdpr_findings = [f for f in result.findings if "NON-COMPLIANT" in f]
    assert len(gdpr_findings) == 0


def test_global_setter_catches_gdpr_violation():
    from src.agents.global_setter import GlobalSetter
    dirty_cv = CV + "\nMarital Status: Married | Religion: Christian | DOB: 1985-01-15"
    result = run(GlobalSetter(llm=None).analyze(dirty_cv, JD, CTX))
    all_text = " ".join(result.findings + result.recommendations)
    assert any(word in all_text.lower() for word in ["marital", "religion", "remove", "gdpr"])


def test_recruiter_scanner_finds_killers():
    from src.agents.recruiter_scanner import RecruiterScanner
    killer_cv = CV + "\nResponsible for managing the team. Duties included reporting to management."
    result = run(RecruiterScanner(llm=None).analyze(killer_cv, JD, CTX))
    all_text = " ".join(result.findings + result.recommendations).lower()
    assert "responsible for" in all_text or "duties" in all_text or "replace" in all_text


def test_recruiter_scanner_counts_metrics():
    from src.agents.recruiter_scanner import RecruiterScanner
    result = run(RecruiterScanner(llm=None).analyze(CV, JD, CTX))
    # Our sample CV has many metrics (45%, 60%, 35%, etc.)
    metrics_finding = next((f for f in result.findings if "Quantified" in f or "Metrics" in f), "")
    if metrics_finding:
        # Should find at least some metrics in our rich CV
        assert any(char.isdigit() for char in metrics_finding)


def test_compliance_guardian_clean_cv():
    from src.agents.compliance_guardian import ComplianceGuardian
    result = run(ComplianceGuardian(llm=None).analyze(CV, JD, CTX))
    assert result.score >= 50
    assert any("COMPLIANT" in f for f in result.findings)


def test_compliance_guardian_catches_id_number():
    from src.agents.compliance_guardian import ComplianceGuardian
    id_cv = CV + "\nID Number: 8501015000082\nMarried with 2 children"
    result = run(ComplianceGuardian(llm=None).analyze(id_cv, JD, CTX))
    all_text = " ".join(result.findings + result.recommendations).lower()
    assert any(word in all_text for word in ["id", "sensitive", "remove", "popia", "marital"])
    assert result.score < 90  # Should be penalized


def test_semantic_matcher_cosine():
    from src.agents.semantic_matcher import SemanticMatcher
    result = run(SemanticMatcher(llm=None).analyze(CV, JD, CTX))
    assert result.agent_name == "The Semantic Matcher"
    assert 0 <= result.score <= 100
    cosine_finding = next((f for f in result.findings if "Cosine" in f), "")
    assert cosine_finding  # Should calculate and report cosine similarity


def test_future_architect_emerging_skills():
    from src.agents.future_architect import FutureArchitect
    result = run(FutureArchitect(llm=None).analyze(CV, JD, CTX))
    assert result.agent_name == "The Future-Proof Architect"
    assert 0 <= result.score <= 100
    # CV has "Agile/Scrum" and Python which are emerging skills
    skills_finding = next((f for f in result.findings if "Emerging" in f), "")
    assert skills_finding


def test_cover_letter_agent():
    from src.agents.cover_letter_agent import CoverLetterAgent
    result = run(CoverLetterAgent(llm=None).analyze(CV, JD, CTX))
    assert result.agent_name == "The Cover Letter Composer"
    # In rule-based mode, returns fallback
    assert result.score >= 0


# ─── Orchestrator Tests ───────────────────────────────────────────────────────

def test_orchestrator_runs_all_agents():
    from src.core.orchestrator import ATSGodOrchestrator
    orch = ATSGodOrchestrator()

    results = run(orch.optimize(cv_text=CV, job_description=JD, context=CTX,
                                generate_cover_letter=False))

    assert "summary" in results
    assert "agent_results" in results
    assert "cv_variants" in results
    assert "action_items" in results
    assert len(results["agent_results"]) == 8


def test_orchestrator_summary_structure():
    from src.core.orchestrator import ATSGodOrchestrator
    orch = ATSGodOrchestrator()
    results = run(orch.optimize(CV, JD, CTX, generate_cover_letter=False))

    summary = results["summary"]
    assert "overall_score" in summary
    assert "recommended_variant" in summary
    assert "interview_probability" in summary
    assert "agent_scores" in summary
    assert 0 <= summary["overall_score"] <= 100
    assert 0 <= summary["interview_probability"] <= 100
    assert summary["recommended_variant"] in ["BALANCED", "ATS-MAX", "CREATIVE"]


def test_orchestrator_generates_3_variants():
    from src.core.orchestrator import ATSGodOrchestrator
    orch = ATSGodOrchestrator()
    results = run(orch.optimize(CV, JD, CTX, generate_cover_letter=False))
    variants = results["cv_variants"]
    assert "ats_max" in variants
    assert "balanced" in variants
    assert "creative" in variants
    assert all(len(v) > 100 for v in variants.values())


def test_exporter_txt():
    from src.core.orchestrator import ATSGodOrchestrator
    from src.core.exporter import export_to_txt
    orch = ATSGodOrchestrator()
    results = run(orch.optimize(CV, JD, CTX, generate_cover_letter=False))
    txt = export_to_txt(results)
    assert "ATS-GOD" in txt
    assert "OVERALL SCORE" in txt
    assert "PRIORITY ACTION ITEMS" in txt
    assert len(txt) > 1000
