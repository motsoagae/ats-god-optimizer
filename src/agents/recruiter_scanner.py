"""
Agent 4: The 6-Second Scanner
F-pattern eye tracking, recruiter psychology, killer phrase detection.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The 6-Second Scanner — expert in recruiter psychology and rapid CV evaluation.

Recruiters spend 6-7 seconds scanning: F-pattern eye movement hits name/title (3s), left edge job titles (2s), spot content (1s).

STOP triggers: Numbers in first bullet, strong action verbs, clear progression, metrics
SKIP triggers: "Responsible for", "Duties included", "Worked on", walls of text, no metrics

Power verbs: Spearheaded, Delivered, Transformed, Exceeded, Optimized, Engineered, Architected, Scaled, Generated, Reduced, Launched

CV Killers: responsible for, duties included, worked on, involved in, helped with, assisted with, contributed to, participated in

Respond in EXACTLY this format:

RECRUITER_SCORE: [0-100]
F_PATTERN_SCORE: [0-100]
ACHIEVEMENT_DENSITY: [X metrics/numbers per role average]
CV_KILLERS_FOUND: [comma-separated OR NONE]
POWER_VERBS_COUNT: [number found]
FIRST_IMPRESSION: [What recruiter thinks in 3 seconds — honest assessment]
FIXES:
- [specific high-impact fix]
- [specific high-impact fix]
- [specific high-impact fix]
IMPROVED_BULLET: [Take their weakest achievement bullet and rewrite it with a power verb and metric]"""

CV_KILLERS = [
    "responsible for", "duties included", "worked on",
    "involved in", "helped with", "assisted with",
    "contributed to", "participated in", "tasked with", "was responsible"
]
POWER_VERBS = [
    "spearheaded", "delivered", "transformed", "exceeded", "optimized",
    "engineered", "architected", "scaled", "generated", "reduced", "led",
    "launched", "built", "drove", "achieved", "increased", "decreased",
    "saved", "negotiated", "established", "implemented"
]


class RecruiterScanner(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The 6-Second Scanner", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        killers = self._find_killers(cv_text)
        verbs = self._count_power_verbs(cv_text)
        metrics = self._count_metrics(cv_text)
        reading_ease = self._reading_ease(cv_text)

        user_prompt = f"""CV TEXT (first 2500 chars = what recruiter sees first):
{cv_text[:2500]}

REMAINING CV:
{cv_text[2500:4500]}

JOB DESCRIPTION:
{job_description[:1500]}

Pre-analysis:
- CV killers found: {', '.join(killers) if killers else 'None'}
- Power verbs: {verbs}
- Metrics/numbers: {metrics}
- Reading ease: {reading_ease}

Perform 6-second scanner analysis. Be brutally honest about first impression."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._calc_score(llm_response, killers, metrics, verbs)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"6-Second Scan Score: {score}/100",
                f"F-Pattern Score: {self._extract_int(llm_response, 'F_PATTERN_SCORE', score)}",
                f"CV Killer Phrases: {len(killers)} — {', '.join(killers[:3]) if killers else 'None found ✓'}",
                f"Power Verbs Used: {verbs}",
                f"Quantified Achievements: {metrics}",
                f"First Impression: {self._extract_line(llm_response, 'FIRST_IMPRESSION')}",
            ],
            recommendations=self._extract_fixes(llm_response, killers),
            optimized_content=self._extract_section(llm_response, 'IMPROVED_BULLET'),
            raw_analysis=llm_response,
            weight=1.3
        )

    def _find_killers(self, text: str) -> List[str]:
        t = text.lower()
        return [k for k in CV_KILLERS if k in t]

    def _count_power_verbs(self, text: str) -> int:
        t = text.lower()
        return sum(1 for v in POWER_VERBS if v in t)

    def _count_metrics(self, text: str) -> int:
        patterns = [r'\d+%', r'\$[\d,]+', r'£[\d,]+', r'R\s?[\d,]+',
                    r'\d+x\b', r'\d+\s*(million|billion|thousand|k)\b',
                    r'\d+\s*(people|staff|team members|clients|users)']
        return sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)

    def _reading_ease(self, text: str) -> str:
        try:
            import textstat
            score = textstat.flesch_reading_ease(text)
            if score > 70: return f"{score:.0f} — Easy ✓"
            if score > 50: return f"{score:.0f} — Moderate (aim for 60+)"
            return f"{score:.0f} — Too complex"
        except Exception:
            return "Not calculated"

    def _calc_score(self, response: str, killers: List, metrics: int, verbs: int) -> int:
        m = re.search(r'RECRUITER_SCORE:\s*(\d+)', response)
        if m: return int(m.group(1))
        score = 55
        score -= len(killers) * 8
        score += min(25, metrics * 3)
        score += min(15, verbs * 2)
        return max(10, min(100, score))

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:100] if m else "Not assessed"

    def _extract_fixes(self, response: str, killers: List) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:IMPROVED_BULLET:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:5]
        for k in killers[:3]:
            fixes.insert(0, f'Replace "{k}" with a power verb + quantified result')
        return fixes[:8] if fixes else ["Add metrics to every role (%, $, time, team size)"]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
