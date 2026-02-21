"""
Agent 7: The Compliance Guardian
GDPR, SA privacy law, truth verification, ethics enforcement.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Compliance Guardian — legal and ethics enforcer for CV optimization.

You protect candidates from:
1. Discrimination risks: age, gender, marital status, religion in CV
2. Privacy risks: ID numbers, full home address, bank details
3. GDPR violations: for EU/UK applications
4. SA privacy law: POPIA compliance
5. Misrepresentation: inflated titles, fabricated metrics, false dates
6. Red flags: salary history (illegal in some US states), non-compete violations

You verify:
- All metrics are plausible (not obviously fabricated)
- Job titles match industry norms
- Date ranges do not contradict each other
- Skills match stated experience level

Respond in EXACTLY this format:

COMPLIANCE_SCORE: [0-100]
LEGAL_RISKS: [comma-separated list OR NONE]
GDPR_STATUS: [COMPLIANT / PARTIAL / NON-COMPLIANT — with reason]
POPIA_STATUS: [COMPLIANT / PARTIAL / NON-COMPLIANT — with reason]
TRUTH_FLAGS: [suspicious or unverifiable claims OR NONE]
SENSITIVE_DATA: [items to remove OR NONE]
FIXES:
- [specific compliance fix]
- [specific compliance fix]
- [specific compliance fix]
SANITIZED_SUMMARY: [Rewrite the professional summary removing any legally sensitive or discriminatory content]"""

SENSITIVE_PATTERNS = {
    'SA ID number (13 digits)': r'\b\d{13}\b',
    'date of birth': r'\bDOB\b|\bdate of birth\b|\bborn:\s*\d',
    'marital status': r'\b(married|single|divorced|widowed|separated)\b',
    'religion': r'\b(christian|muslim|jewish|hindu|buddhist|catholic|protestant|atheist)\b',
    'home address': r'\b\d{1,5}\s+\w+\s+(street|road|avenue|drive|lane|close|crescent)\b',
    'photo reference': r'\[photo\]|\[image\]|photograph enclosed',
    'salary history': r'previous salary|salary history|current salary:\s*R',
    'id/passport explicit': r'\bID\s*number\s*:\s*\d|\bpassport\s*:\s*[A-Z]\d',
}

EXAGGERATION_FLAGS = [
    (r'\b(guru|ninja|rockstar|wizard|unicorn)\b', 'Unprofessional buzzword'),
    (r'\b100%\s+(success rate|client satisfaction|accuracy)\b', 'Unverifiable 100% claim'),
    (r'saved\s+\$\s*\d{8,}', 'Implausibly large savings claim — verify'),
    (r'increased\s+revenue\s+by\s+\d{3,}%', 'Very high % increase — ensure verifiable'),
]


class ComplianceGuardian(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Compliance Guardian", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        sensitive = self._find_sensitive(cv_text)
        truth_flags = self._flag_exaggerations(cv_text)
        gdpr = self._gdpr_status(sensitive)
        popia = self._popia_status(sensitive)

        user_prompt = f"""CV TEXT:
{cv_text[:3500]}

CONTEXT:
- Target market: {context.get('target_market', 'South Africa')}

Pre-analysis:
- Sensitive data found: {', '.join(sensitive) if sensitive else 'None'}
- Truth flags: {', '.join(truth_flags) if truth_flags else 'None'}
- GDPR status: {gdpr}
- POPIA status: {popia}

Perform full compliance audit. Flag EVERYTHING legally risky."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._calc_score(sensitive, truth_flags, llm_response)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Compliance Score: {score}/100",
                f"GDPR Status: {gdpr}",
                f"POPIA Status: {popia}",
                f"Sensitive Data Items: {len(sensitive)} — {', '.join(list(sensitive.keys())[:3]) if sensitive else 'None ✓'}",
                f"Truth/Accuracy Flags: {len(truth_flags)} — {', '.join(truth_flags[:2]) if truth_flags else 'None ✓'}",
            ],
            recommendations=self._extract_fixes(llm_response, sensitive, truth_flags),
            optimized_content=self._extract_section(llm_response, 'SANITIZED_SUMMARY'),
            raw_analysis=llm_response,
            weight=1.0
        )

    def _find_sensitive(self, text: str) -> Dict[str, str]:
        found = {}
        for label, pattern in SENSITIVE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                found[label] = pattern
        return found

    def _flag_exaggerations(self, text: str) -> List[str]:
        flags = []
        for pattern, label in EXAGGERATION_FLAGS:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(label)
        return flags

    def _gdpr_status(self, sensitive: Dict) -> str:
        gdpr_risks = ['marital status', 'religion', 'date of birth', 'photo reference']
        violations = [k for k in sensitive if k in gdpr_risks]
        if violations: return f"NON-COMPLIANT — {', '.join(violations)}"
        if sensitive: return "PARTIAL — minor concerns"
        return "COMPLIANT ✓"

    def _popia_status(self, sensitive: Dict) -> str:
        popia_risks = ['SA ID number (13 digits)', 'home address', 'id/passport explicit']
        violations = [k for k in sensitive if k in popia_risks]
        if violations: return f"NON-COMPLIANT — {', '.join(violations)}"
        return "COMPLIANT ✓"

    def _calc_score(self, sensitive: Dict, flags: List, response: str) -> int:
        m = re.search(r'COMPLIANCE_SCORE:\s*(\d+)', response)
        if m: return int(m.group(1))
        score = 100 - (len(sensitive) * 10) - (len(flags) * 5)
        return max(20, min(100, score))

    def _extract_fixes(self, response: str, sensitive: Dict, flags: List) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:SANITIZED_SUMMARY:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:4]
        for label in list(sensitive.keys())[:3]:
            fixes.insert(0, f"REMOVE immediately: {label} — never required on a CV")
        for flag in flags[:2]:
            fixes.append(f"Review accuracy: {flag}")
        return fixes[:8]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
