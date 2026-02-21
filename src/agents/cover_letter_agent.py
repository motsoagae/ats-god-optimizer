"""
Agent 9 (Bonus): The Cover Letter Composer
Personalized, ATS-optimized cover letters that actually get read.
"""
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """You are The Cover Letter Composer — expert at writing cover letters that get interviews.

90% of cover letters are ignored because they're generic. Yours are different:
- Open with the PROBLEM the company solves or a compelling industry insight (NOT "I am writing to apply...")
- Show you've RESEARCHED the company/role — mention something specific from the JD
- Prove you can DO THE JOB with 2-3 specific achievements with metrics
- End with a CONFIDENT call to action (NOT "I hope to hear from you")
- 3 paragraphs MAXIMUM — 250-350 words total

SA market: slightly more formal, mention B-BBEE if relevant
International: punchy, direct, results-first

Structure:
P1 — Hook: Address their challenge or your insight about their world (3-4 sentences)
P2 — Proof: 2-3 specific achievements that directly match their requirements (4-5 sentences)
P3 — Close: Confident, brief, clear call to action (2-3 sentences)

Respond in EXACTLY this format:

COVER_LETTER_START
[Full cover letter here — 250-350 words, 3 paragraphs, professional]
COVER_LETTER_END

QUALITY_SCORE: [0-100]
PERSONALIZATION: [Generic/Basic/Good/Excellent]
WORD_COUNT: [actual word count]
TIPS:
- [tip to personalize further]
- [tip to personalize further]"""


class CoverLetterAgent(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("The Cover Letter Composer", llm)

    async def analyze(self, cv_text: str, job_description: str, context: Dict) -> AgentOutput:
        company = self._extract_company(job_description)
        role = self._extract_role(job_description)

        user_prompt = f"""CV TEXT (extract 3 strongest achievements with metrics):
{cv_text[:3000]}

JOB DESCRIPTION:
{job_description[:2000]}

CONTEXT:
- Target Market: {context.get('target_market', 'South Africa')}
- Experience Level: {context.get('experience_level', 'Mid')}
- Industry: {context.get('industry', 'Not specified')}
- Company detected: {company}
- Role detected: {role}

Write a compelling, personalized cover letter that will earn an interview.
Do NOT use "I am writing to apply". Do NOT be generic.
Reference specific elements from the job description."""

        llm_response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)
        letter = self._extract_letter(llm_response)
        score = self._extract_int(llm_response, 'QUALITY_SCORE', 70)

        return AgentOutput(
            agent_name=self.name,
            score=score,
            findings=[
                f"Cover Letter Quality: {score}/100",
                f"Word Count: {len(letter.split())} words",
                f"Personalization: {self._extract_line(llm_response, 'PERSONALIZATION')}",
                f"Company: {company}",
                f"Role: {role}",
            ],
            recommendations=self._extract_tips(llm_response),
            optimized_content=letter,
            raw_analysis=llm_response,
            weight=0.8
        )

    def _extract_company(self, jd: str) -> str:
        patterns = [
            r'(?:at|join|company|organisation|organization):\s*([A-Z][A-Za-z\s&]{2,30})',
            r'^([A-Z][A-Za-z\s&]{2,30})\s+(?:is|are)\s+(?:looking|seeking|hiring)',
        ]
        for p in patterns:
            m = re.search(p, jd, re.MULTILINE)
            if m: return m.group(1).strip()[:40]
        return "[Company Name]"

    def _extract_role(self, jd: str) -> str:
        patterns = [
            r'(?:position|role|job title|vacancy):\s*(.+?)(?:\n|$)',
            r'^([\w\s/]{5,40})\n',
        ]
        for p in patterns:
            m = re.search(p, jd, re.IGNORECASE | re.MULTILINE)
            if m: return m.group(1).strip()[:60]
        return "[Role]"

    def _extract_letter(self, response: str) -> str:
        m = re.search(r'COVER_LETTER_START\s*\n(.*?)\nCOVER_LETTER_END', response, re.DOTALL)
        if m: return m.group(1).strip()
        # Fallback
        m2 = re.search(r'COVER_LETTER_START\s*\n(.+)', response, re.DOTALL)
        return m2.group(1).strip()[:2000] if m2 else response[:1500]

    def _extract_int(self, text: str, key: str, default: int) -> int:
        m = re.search(rf'{key}:\s*(\d+)', text)
        return int(m.group(1)) if m else default

    def _extract_line(self, text: str, key: str) -> str:
        m = re.search(rf'{key}:\s*(.+?)(?:\n|$)', text)
        return m.group(1).strip()[:60] if m else "Not assessed"

    def _extract_tips(self, response: str) -> List[str]:
        m = re.search(r'TIPS:(.*?)(?:$)', response, re.DOTALL)
        if m:
            return [l.strip().lstrip('- ') for l in m.group(1).strip().split('\n')
                    if l.strip() and l.strip() != '-'][:3]
        return ["Add the hiring manager's name if you can find it", "Reference a recent company news item"]
