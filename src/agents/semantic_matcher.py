"""
Agent 6: The Semantic Matcher
NLP context analysis, cosine similarity, skill ontology mapping.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Semantic Matcher — NLP expert who understands meaning beyond keywords.

Modern ATS uses semantic search: "Led engineering team" matches "Team Lead", "React.js" = "Frontend Development", "Agile" = "Scrum/Kanban/Sprint planning".

Skill ontology:
- Data Science: Python, R, ML, TensorFlow, PyTorch, Pandas, Statistics, A/B Testing, Jupyter
- Cloud/DevOps: AWS, Azure, GCP, Terraform, Kubernetes, Docker, CI/CD, Jenkins, GitHub Actions
- Finance: FP&A, P&L, variance analysis, SAP, Oracle, Excel modeling, forecasting
- Marketing: SEO, SEM, Google Analytics, Meta Ads, CRM, content strategy, HubSpot
- HR: HRIS, talent acquisition, performance management, L&D, succession planning, Workday
- Project Mgmt: PMP, Agile, Scrum, PRINCE2, Jira, MS Project, stakeholder management

Respond in EXACTLY this format:

SEMANTIC_SCORE: [0-100]
COSINE_ESTIMATE: [X]% semantic alignment
SEMANTIC_GAPS: [concepts in JD not covered by CV — comma-separated]
HIDDEN_MATCHES: [CV_term→JD_term semantic equivalents — comma-separated]
TONE_ALIGNMENT: [Startup/Corporate/Government] [X]% aligned
IMPLICIT_REQUIREMENTS: [unstated requirements inferred from JD — comma-separated]
FIXES:
- [specific semantic improvement]
- [specific semantic improvement]
- [specific semantic improvement]
SEMANTIC_BRIDGE: [2-3 sentences that naturally introduce the 3 most critical missing semantic concepts using the candidate's existing experience]"""

SKILL_ONTOLOGY = {
    'agile': ['scrum', 'kanban', 'sprint', 'backlog', 'standup', 'retro', 'velocity'],
    'leadership': ['managed', 'led', 'mentored', 'coached', 'directed', 'supervised', 'head of'],
    'data analysis': ['analytics', 'insights', 'reporting', 'dashboards', 'kpi', 'metrics', 'tableau', 'power bi'],
    'cloud': ['aws', 'azure', 'gcp', 'cloud', 'kubernetes', 'docker', 'devops', 'terraform'],
    'communication': ['presentation', 'stakeholder', 'negotiation', 'briefing', 'reporting'],
    'project management': ['pmp', 'prince2', 'jira', 'ms project', 'delivery', 'milestones', 'governance'],
}


class SemanticMatcher(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Semantic Matcher", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        cosine = self._cosine_similarity(cv_text, job_description)
        hidden = self._find_hidden_matches(cv_text, job_description)
        tone = self._tone_analysis(cv_text, job_description)

        user_prompt = f"""CV TEXT:
{cv_text[:3000]}

JOB DESCRIPTION:
{job_description[:2000]}

Pre-calculated metrics:
- TF-IDF Cosine Similarity: {cosine:.2f}
- Hidden semantic matches: {hidden}
- Tone analysis: {tone}

Perform deep semantic gap analysis."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'SEMANTIC_SCORE', int(cosine * 100))

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Semantic Match Score: {score}/100",
                f"Cosine Similarity: {cosine:.2f} (>0.75 = strong match)",
                f"Hidden Semantic Matches: {hidden}",
                f"Tone Alignment: {self._extract_line(llm_response, 'TONE_ALIGNMENT')}",
                f"Semantic Gaps: {self._extract_line(llm_response, 'SEMANTIC_GAPS')}",
            ],
            recommendations=self._extract_fixes(llm_response),
            optimized_content=self._extract_section(llm_response, 'SEMANTIC_BRIDGE'),
            raw_analysis=llm_response,
            weight=1.1
        )

    def _cosine_similarity(self, cv: str, jd: str) -> float:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            vec = TfidfVectorizer(stop_words='english', max_features=500, ngram_range=(1, 2))
            matrix = vec.fit_transform([cv[:5000], jd[:5000]])
            return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
        except Exception:
            return 0.5

    def _find_hidden_matches(self, cv: str, jd: str) -> str:
        cv_lower, jd_lower = cv.lower(), jd.lower()
        matches = []
        for concept, synonyms in SKILL_ONTOLOGY.items():
            jd_needs = any(s in jd_lower for s in synonyms + [concept])
            cv_has_synonym = any(s in cv_lower for s in synonyms)
            cv_has_exact = concept in cv_lower
            if jd_needs and cv_has_synonym and not cv_has_exact:
                syn_found = next((s for s in synonyms if s in cv_lower), None)
                if syn_found:
                    matches.append(f"{syn_found}→{concept}")
        return ', '.join(matches[:4]) if matches else 'None detected'

    def _tone_analysis(self, cv: str, jd: str) -> str:
        startup = ['disrupt', 'scale', 'growth', 'startup', 'agile', 'iterate', 'pivot', 'lean']
        corporate = ['stakeholder', 'governance', 'compliance', 'framework', 'enterprise', 'policy', 'strategy']
        govt = ['public sector', 'government', 'municipality', 'department', 'regulation', 'audit']
        jd_lower = jd.lower()
        cv_lower = cv.lower()
        scores = {
            'Startup': (sum(1 for w in startup if w in jd_lower), sum(1 for w in startup if w in cv_lower)),
            'Corporate': (sum(1 for w in corporate if w in jd_lower), sum(1 for w in corporate if w in cv_lower)),
            'Government': (sum(1 for w in govt if w in jd_lower), sum(1 for w in govt if w in cv_lower)),
        }
        dominant = max(scores, key=lambda k: scores[k][0])
        jd_score, cv_score = scores[dominant]
        if jd_score == 0:
            return "Corporate — 75% aligned"
        pct = min(100, int((cv_score / jd_score) * 100))
        return f"{dominant} — {pct}% aligned"

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:100] if m else "Not assessed"

    def _extract_fixes(self, response: str) -> List[str]:
        m = re.search(r'FIXES:(.*?)(?:SEMANTIC_BRIDGE:|$)', response, re.DOTALL)
        if m:
            return [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                    if l.strip() and l.strip() != '-'][:6]
        return ["Mirror JD language more closely in experience descriptions"]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
