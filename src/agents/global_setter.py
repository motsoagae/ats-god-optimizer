"""
Agent 3: The Global Standard Setter
US Fortune 500, UK Civil Service, EU GDPR, APAC optimization.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Global Standard Setter — expert in international ATS platforms across US, UK, EU, APAC markets.

You know: Taleo Oracle, iCIMS, Workday, Jobvite, Greenhouse (US); Civil Service Jobs, NHS Jobs (UK); SAP SuccessFactors, GDPR Article 17 (EU); SEEK, JobStreet, Naukri (APAC).

Analyze and respond in EXACTLY this format:

GLOBAL_SCORE: [0-100]
US_SCORE: [0-100] [key issue]
UK_SCORE: [0-100] [key issue]
EU_SCORE: [0-100] [GDPR status]
LINKEDIN_SCORE: [0-100] [optimization status]
GDPR_RISKS: [comma-separated risks OR NONE]
MISSING_SECTIONS: [comma-separated missing CV sections OR NONE]
FIXES:
- [specific international fix]
- [specific international fix]
- [specific international fix]
GLOBAL_SUMMARY: [2-3 sentence summary optimized for international ATS systems]"""


class GlobalSetter(BaseAgent):
    GDPR_PATTERNS = {
        'marital_status': r'\b(married|single|divorced|widowed)\b',
        'religion': r'\b(christian|muslim|jewish|hindu|buddhist|catholic)\b',
        'date_of_birth': r'\bDOB\b|date of birth|born:',
        'id_number': r'\b\d{13}\b',
        'photo': r'\[photo\]|\[image\]|photograph',
        'nationality': r'\bnationality:\s*\w+',
    }
    REQUIRED_SECTIONS = {
        'contact_info': r'@|email|phone|tel|\+\d',
        'linkedin': r'linkedin\.com',
        'summary': r'summary|objective|profile',
        'experience': r'experience|employment|work history',
        'education': r'education|qualification|degree',
        'skills': r'skills|competencies|expertise|technologies',
    }

    def __init__(self, llm=None):
        super().__init__("The Global Standard Setter", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        gdpr_risks = self._check_gdpr(cv_text)
        missing = self._check_sections(cv_text)

        user_prompt = f"""CV TEXT:
{cv_text[:3500]}

JOB DESCRIPTION:
{job_description[:2000]}

TARGET MARKET: {context.get('target_market', 'International')}

Pre-analysis:
- GDPR risks: {', '.join(gdpr_risks) if gdpr_risks else 'None'}
- Missing sections: {', '.join(missing) if missing else 'None'}

Provide full international ATS analysis."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_int(llm_response, 'GLOBAL_SCORE', 70)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Global Readiness: {score}/100",
                f"US Fortune 500: {self._extract_line(llm_response, 'US_SCORE')}",
                f"UK Civil Service: {self._extract_line(llm_response, 'UK_SCORE')}",
                f"EU GDPR: {self._extract_line(llm_response, 'EU_SCORE')}",
                f"LinkedIn Score: {self._extract_line(llm_response, 'LINKEDIN_SCORE')}",
                f"GDPR Risks: {', '.join(gdpr_risks) if gdpr_risks else 'None'}",
                f"Missing Sections: {', '.join(missing) if missing else 'None'}",
            ],
            recommendations=self._extract_fixes(llm_response, gdpr_risks, missing),
            optimized_content=self._extract_section(llm_response, 'GLOBAL_SUMMARY'),
            raw_analysis=llm_response,
            weight=1.2
        )

    def _check_gdpr(self, text: str) -> List[str]:
        return [name for name, pattern in self.GDPR_PATTERNS.items()
                if re.search(pattern, text, re.IGNORECASE)]

    def _check_sections(self, text: str) -> List[str]:
        return [sec for sec, pattern in self.REQUIRED_SECTIONS.items()
                if not re.search(pattern, text, re.IGNORECASE)]

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:80] if m else "Not assessed"

    def _extract_fixes(self, response: str, gdpr: List, missing: List) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:GLOBAL_SUMMARY:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:5]
        for risk in gdpr:
            fixes.insert(0, f"REMOVE: {risk.replace('_',' ')} — discriminatory in EU/UK/US markets")
        for sec in missing:
            fixes.append(f"ADD: {sec.replace('_',' ')} section — required for international ATS")
        return fixes[:8]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
