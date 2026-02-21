"""
Agent 8: The Future-Proof Architect
Career trajectory, emerging skills, next-role positioning.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Future-Proof Architect — career strategist who positions CVs for the NEXT role, not just the current one.

2024-2025 emerging skills that differentiate candidates:
Technical: Generative AI, LLM integration, Prompt Engineering, AI tools (GitHub Copilot, ChatGPT), Power BI, Tableau, Python for data, API integration, automation, cloud-native, Kubernetes
Leadership: OKR frameworks, async remote leadership, global distributed teams, AI-augmented decision making
Sustainability: ESG reporting, carbon footprint, sustainability strategy, circular economy
Soft: Psychological safety, inclusive leadership, neurodiversity awareness, design thinking

Career progression patterns:
- Specialist → Senior Specialist → Lead → Manager → Director → VP/C-Suite
- IC → Tech Lead → Engineering Manager → Director of Engineering → CTO
- Analyst → Senior → Principal → Head of → VP of → Chief

Respond in EXACTLY this format:

FUTURE_SCORE: [0-100]
CAREER_TRAJECTORY: [honest assessment of progression direction and velocity]
NEXT_ROLE_READINESS: [X]% ready for [next logical role]
SKILL_GAPS: [skills needed for next role — comma-separated]
EMERGING_SKILLS_PRESENT: [trending skills already in CV — comma-separated OR NONE]
EMERGING_SKILLS_MISSING: [top 3 to add based on their trajectory]
LEARNING_PATH: [prioritized: skill (timeline to acquire)]
FIXES:
- [specific future-proofing fix]
- [specific future-proofing fix]
- [specific future-proofing fix]
CAREER_NARRATIVE: [2-3 sentences showing compelling upward career arc, positioning them for their next role]"""

EMERGING_2025 = [
    "generative ai", "llm", "prompt engineering", "ai tools", "github copilot",
    "power bi", "tableau", "esg", "sustainability", "okr", "okrs",
    "remote leadership", "async", "python", "automation", "api", "no-code",
    "low-code", "data-driven", "cloud native", "kubernetes", "terraform"
]


class FutureArchitect(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Future-Proof Architect", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        cv_lower = cv_text.lower()
        present = [s for s in EMERGING_2025 if s in cv_lower]
        progression = self._assess_progression(cv_text)

        user_prompt = f"""CV TEXT:
{cv_text[:3500]}

JOB DESCRIPTION:
{job_description[:1500]}

CONTEXT:
- Experience Level: {context.get('experience_level', 'Mid')}
- Target Role: {context.get('target_role', 'Similar to current')}
- Industry: {context.get('industry', 'Not specified')}

Pre-analysis:
- Emerging skills already present: {', '.join(present) if present else 'None'}
- Career progression assessment: {progression}
- Emerging skill coverage: {len(present)}/{len(EMERGING_2025)} tracked skills ({int(len(present)/len(EMERGING_2025)*100)}%)

Design future-proof positioning."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'FUTURE_SCORE', 60)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Future-Proof Score: {score}/100",
                f"Career Trajectory: {self._extract_line(llm_response, 'CAREER_TRAJECTORY')}",
                f"Next Role Readiness: {self._extract_line(llm_response, 'NEXT_ROLE_READINESS')}",
                f"Emerging Skills Present: {len(present)}/{len(EMERGING_2025)} — {', '.join(present[:4]) if present else 'None'}",
                f"Progression: {progression}",
            ],
            recommendations=self._extract_fixes(llm_response, present),
            optimized_content=self._extract_section(llm_response, 'CAREER_NARRATIVE'),
            raw_analysis=llm_response,
            weight=0.9
        )

    def _assess_progression(self, text: str) -> str:
        words = ['promoted', 'advanced', 'progressed', 'grew', 'scaled', 'expanded', 'elevated']
        count = sum(1 for w in words if w in text.lower())
        if count >= 3: return "Strong upward progression ✓"
        if count >= 1: return "Some progression — strengthen career narrative"
        return "Progression unclear — needs career arc work"

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:100] if m else "Not assessed"

    def _extract_fixes(self, response: str, present: List) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:CAREER_NARRATIVE:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:5]
        if len(present) < 3:
            fixes.append("Add 2-3 emerging skills: generative AI tools, data-driven decision making, ESG awareness")
        return fixes[:8]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
