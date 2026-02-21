"""
Agent 1: The Algorithm Breaker
Reverse-engineers Taleo, Workday, Greenhouse, Lever, SmartRecruiters.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Algorithm Breaker — expert in ATS parsing algorithms for Taleo, Workday, Greenhouse, Lever, SmartRecruiters, iCIMS.

Analyze the CV against the job description and respond in EXACTLY this format (no deviation):

ATS_SCORE: [0-100]
PARSER_RATES: Taleo:[X]% Workday:[X]% Greenhouse:[X]%
BLACK_FLAGS: [comma-separated list OR the word NONE]
KEYWORD_MATCH: [X]%
MISSING_KEYWORDS: [comma-separated top 10 missing keywords]
FIXES:
- [specific actionable fix]
- [specific actionable fix]
- [specific actionable fix]
OPTIMIZED_SUMMARY: [rewrite the professional summary for maximum ATS compatibility, 2-3 sentences]"""


class AlgorithmBreaker(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Algorithm Breaker", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        black_flags = self._detect_black_flags(cv_text)
        keyword_data = self._analyze_keywords(cv_text, job_description)

        user_prompt = f"""CV TEXT:
{cv_text[:3500]}

JOB DESCRIPTION:
{job_description[:2000]}

TARGET MARKET: {context.get('target_market', 'Both')}

Pre-analysis:
- Black flags detected: {', '.join(black_flags) if black_flags else 'None'}
- Keyword match: {keyword_data['match_pct']:.0f}%
- Missing keywords: {', '.join(keyword_data['missing'][:10])}

Perform full ATS analysis."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        score = self._extract_score(llm_response, keyword_data)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"ATS Readiness Score: {score}/100",
                f"Keyword Match Rate: {keyword_data['match_pct']:.0f}%",
                f"ATS Black Flags: {', '.join(black_flags) if black_flags else 'None detected'}",
                f"Missing Critical Keywords: {len(keyword_data['missing'])}",
                f"Parser Rates: {self._extract_parser_rates(llm_response)}",
            ],
            recommendations=self._extract_fixes(llm_response, black_flags, keyword_data),
            optimized_content=self._extract_section(llm_response, 'OPTIMIZED_SUMMARY'),
            raw_analysis=llm_response,
            weight=1.8
        )

    def _detect_black_flags(self, text: str) -> List[str]:
        flags = []
        if re.search(r'\|.+\|', text): flags.append("markdown_tables")
        if text.count('\t') > 5: flags.append("excessive_tabs")
        if len(re.findall(r'[^\x00-\x7F]', text)) > 10: flags.append("special_characters")
        if re.search(r'(header|footer)', text, re.IGNORECASE): flags.append("header_footer_text")
        if re.search(r'\[image\]|\[photo\]', text, re.IGNORECASE): flags.append("image_placeholders")
        return flags

    def _analyze_keywords(self, cv: str, jd: str) -> Dict:
        stop_words = {'and','the','for','with','that','are','will','you','have',
                      'this','from','they','been','has','was','our','your','their'}
        jd_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', jd)
                    if w.lower() not in stop_words]
        unique = list(set(jd_words))
        cv_lower = cv.lower()
        matched = [w for w in unique if w in cv_lower]
        missing = [w for w in unique if w not in cv_lower]
        pct = (len(matched) / max(len(unique), 1)) * 100
        return {'match_pct': pct, 'matched': matched[:10], 'missing': missing[:15]}

    def _extract_score(self, response: str, keyword_data: Dict) -> int:
        m = re.search(r'ATS_SCORE:\s*(\d+)', response)
        if m: return min(100, max(0, int(m.group(1))))
        return min(100, int(keyword_data['match_pct'] * 0.7 + 20))

    def _extract_parser_rates(self, response: str) -> str:
        m = re.search(r'PARSER_RATES:\s*(.+?)(?:\n|$)', response)
        return m.group(1).strip() if m else "Not calculated"

    def _extract_fixes(self, response: str, flags: List, keywords: Dict) -> List[str]:
        fixes = []
        m = re.search(r'FIXES:(.*?)(?:OPTIMIZED_SUMMARY:|$)', response, re.DOTALL)
        if m:
            fixes = [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                     if l.strip() and l.strip() != '-'][:5]
        flag_fixes = {
            'markdown_tables': 'Remove all tables — ATS cannot parse them. Use bullet points instead.',
            'excessive_tabs': 'Replace tab-based alignment with spaces.',
            'special_characters': 'Remove special/unicode characters — stick to standard ASCII.',
            'header_footer_text': 'Move header/footer content into the CV body.',
        }
        for flag in flags:
            if flag in flag_fixes and flag_fixes[flag] not in fixes:
                fixes.insert(0, flag_fixes[flag])
        if keywords['missing']:
            fixes.append(f"Add missing keywords: {', '.join(keywords['missing'][:6])}")
        return fixes[:8] if fixes else ["CV formatting looks ATS-compatible"]

    def _extract_section(self, response: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n[A-Z_]+:|$)', response, re.DOTALL)
        return m.group(1).strip() if m else ""
