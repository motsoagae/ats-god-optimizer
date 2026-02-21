"""
Agent 5: The Hiring Manager Whisperer
Technical depth, evidence trails, vague claim detection.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Hiring Manager Whisperer — you think exactly like a hiring manager doing a deep technical review.

Hiring managers: CHECK every technical claim for credibility, look for EVIDENCE (projects, metrics, tools), spot VAGUE claims, create interview questions from CV content, validate career progression logic.

Vague = bad: "experienced in Python", "knowledge of AWS", "familiar with Agile"
Specific = good: "Built FastAPI service handling 10k req/s on AWS Lambda", "Led 4-sprint Agile migration reducing release cycles from 6 weeks to 2"

Respond in EXACTLY this format:

HM_SCORE: [0-100]
TECHNICAL_CLAIMS: [count of technical claims found]
EVIDENCED_CLAIMS: [count with actual evidence]
VAGUE_SKILLS: [comma-separated vague claims found OR NONE]
PORTFOLIO_PRESENT: [YES/NO]
CONVERSATION_STARTERS:
- [specific question HM would ask about a claim]
- [specific question HM would ask about a claim]
FIXES:
- [specific fix]
- [specific fix]
- [specific fix]
EVIDENCE_REWRITE: [Take their single vaguest technical claim and rewrite it with full context: what was built, what tools, what scale, what outcome]"""


class HiringManagerWhisperer(BaseAgent):
    VAGUE_PATTERNS = [
        r'experienced? in ([A-Za-z\s\.\/\+]{3,25})',
        r'knowledge of ([A-Za-z\s\.\/\+]{3,25})',
        r'familiar with ([A-Za-z\s\.\/\+]{3,25})',
        r'proficient in ([A-Za-z\s\.\/\+]{3,25})',
        r'understanding of ([A-Za-z\s\.\/\+]{3,25})',
        r'exposure to ([A-Za-z\s\.\/\+]{3,25})',
    ]

    def __init__(self, llm=None):
        super().__init__("The Hiring Manager Whisperer", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        vague = self._find_vague(cv_text)
        has_portfolio = bool(re.search(r'github|gitlab|portfolio|bitbucket', cv_text, re.IGNORECASE))
        has_metrics = bool(re.search(r'\d+%|\$\d+|R\s?\d+|saved|reduced|increased', cv_text, re.IGNORECASE))

        user_prompt = f"""CV TEXT:
{cv_text[:3500]}

JOB DESCRIPTION:
{job_description[:1500]}

CONTEXT:
- Level: {context.get('experience_level', 'Mid')}
- Industry: {context.get('industry', 'Not specified')}

Pre-analysis:
- Vague skills found: {', '.join(vague) if vague else 'None'}
- Portfolio link present: {has_portfolio}
- Has quantified metrics: {has_metrics}

Perform deep hiring manager technical validation."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'HM_SCORE', 60)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Hiring Manager Appeal: {score}/100",
                f"Vague Skill Claims: {len(vague)} — {', '.join(vague[:3]) if vague else 'None ✓'}",
                f"Portfolio/GitHub: {'✓ Present' if has_portfolio else '✗ Missing — critical for technical roles'}",
                f"Quantified Metrics: {'✓ Present' if has_metrics else '✗ Missing — add numbers'}",
                f"Technical Claims: {self._extract_line(llm_response, 'TECHNICAL_CLAIMS')} found, {self._extract_line(llm_response, 'EVIDENCED_CLAIMS')} with evidence",
            ],
            recommendations=self._extract_fixes(llm_response, vague, has_portfolio),
            optimized_content=self._extract_section(llm_response, 'EVIDENCE_REWRITE'),
            raw_analysis=llm_response,
            weight=1.2
        )

    def _find_vague(self, text: str) -> List[str]:
        found = []
        for p in self.VAGUE_PATTERNS:
            matches = re.findall(p, text, re.IGNORECASE)
            found.extend([m.strip() for m in matches if len(m.strip()) > 2])
        return list(set(found))[:8]

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:80] if m else "Not assessed"

    def _extract_fixes(self, response: str, vague: List, has_portfolio: bool) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:EVIDENCE_REWRITE:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:5]
        if not has_portfolio:
            fixes.insert(0, "Add GitHub/portfolio URL — hiring managers want to verify technical claims")
        for skill in vague[:2]:
            fixes.append(f'Expand "{skill.strip()}" — add tools used, project scale, measurable outcome')
        return fixes[:8]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
