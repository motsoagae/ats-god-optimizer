"""
Agent 2: The South African Specialist
B-BBEE, EE Act, SETA, SAQA NQF, SA labour law optimization.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The South African Specialist — expert in B-BBEE, Employment Equity Act, SETA, SAQA NQF, LRA, BCEA, OHSA.

Analyze the CV for the South African job market and respond in EXACTLY this format:

SA_SCORE: [0-100]
BBEE_ALIGNMENT: [specific B-BBEE advantages and how to highlight them]
NQF_LEVEL: Current:[X or Not Specified] Required:[X based on role]
EE_STRATEGY: [specific Employment Equity positioning advice]
SA_KEYWORDS_ADD: [comma-separated SA-specific keywords to add]
FIXES:
- [specific fix for SA market]
- [specific fix for SA market]
- [specific fix for SA market]
SA_SUMMARY: [2-3 sentence professional summary optimized for SA employers and PNet/Careers24]"""


class SASpecialist(BaseAgent):
    SA_KEYWORDS = [
        "B-BBEE", "Employment Equity", "SETA", "NQF", "SAQA", "LRA", "BCEA",
        "OHSA", "Critical Skills", "Skills Development", "Transformation",
        "PNet", "Careers24", "South Africa", "Cape Town", "Johannesburg", "Durban"
    ]

    def __init__(self, llm=None):
        super().__init__("The South African Specialist", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        nqf = self._detect_nqf(cv_text)
        sa_coverage = self._sa_keyword_coverage(cv_text)

        user_prompt = f"""CV TEXT:
{cv_text[:3500]}

JOB DESCRIPTION:
{job_description[:2000]}

CONTEXT:
- Target: {context.get('target_market', 'South Africa')}
- Level: {context.get('experience_level', 'Mid')}
- Industry: {context.get('industry', 'Not specified')}

Pre-analysis:
- NQF Level detected: {nqf['level']} ({nqf['description']})
- SA keyword coverage: {sa_coverage}%

Provide full SA market optimization."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'SA_SCORE', 65)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"SA Market Score: {score}/100",
                f"NQF Level: {nqf['level']} — {nqf['description']}",
                f"SA Keyword Coverage: {sa_coverage}%",
                f"B-BBEE Alignment: {self._extract_line(llm_response, 'BBEE_ALIGNMENT')}",
                f"EE Strategy: {self._extract_line(llm_response, 'EE_STRATEGY')}",
            ],
            recommendations=self._extract_fixes(llm_response, 'SA_SUMMARY'),
            optimized_content=self._extract_section(llm_response, 'SA_SUMMARY'),
            raw_analysis=llm_response,
            weight=1.4
        )

    def _detect_nqf(self, text: str) -> Dict:
        t = text.lower()
        levels = [
            (10, ['phd', 'doctorate', 'd.phil'], "Doctoral Degree — NQF 10"),
            (9,  ['master', 'mba', 'msc', 'm.com', 'm.eng', 'mtech'], "Master's Degree — NQF 9"),
            (8,  ['honours', 'hons', 'postgraduate diploma', 'pgdip'], "Honours/PG Diploma — NQF 8"),
            (7,  ['bachelor', 'degree', 'b.sc', 'b.com', 'b.tech', 'b.eng', 'btech', 'bcom', 'bsc'], "Bachelor's Degree — NQF 7"),
            (6,  ['national diploma', 'diploma'], "National Diploma — NQF 6"),
            (5,  ['higher certificate', 'certificate'], "Certificate — NQF 5"),
        ]
        for level, keywords, desc in levels:
            if any(k in t for k in keywords):
                return {"level": level, "description": desc}
        return {"level": "Not detected", "description": "Grade 12 or not specified"}

    def _sa_keyword_coverage(self, text: str) -> int:
        t = text.upper()
        found = sum(1 for kw in self.SA_KEYWORDS if kw.upper() in t)
        return int((found / len(self.SA_KEYWORDS)) * 100)

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', text, re.DOTALL)
        return m.group(1).strip()[:100] if m else "See analysis"

    def _extract_fixes(self, response: str, end_key: str) -> List[str]:
        m = re.search(rf'FIXES:(.*?)(?:{end_key}:|$)', response, re.DOTALL)
        if m:
            return [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                    if l.strip() and l.strip() != '-'][:6]
        return ["Add B-BBEE alignment statement to CV", "Include SAQA NQF level in qualifications"]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
