from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput


SYSTEM_PROMPT = """
You are an expert interview coach and hiring strategist.

Your job is to prepare candidates for interviews by:
- Predicting likely interview questions
- Explaining how to answer them clearly and confidently
- Providing compensation and market context
- Helping the candidate avoid common interview mistakes

Be practical, honest, and role-specific.
"""


class InterviewCoach(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("Interview Coach", llm)

    async def analyze(
        self,
        cv_text: str,
        job_description: str,
        context: Dict[str, Any]
    ) -> AgentOutput:

        user_prompt = f"""
CANDIDATE RESUME:
{cv_text[:3000]}

JOB DESCRIPTION:
{job_description[:1500]}

CONTEXT:
- Experience Level: {context.get('experience_level', 'Mid')}
- Target Role: {context.get('target_role', 'Not specified')}
- Industry: {context.get('industry', 'Not specified')}
- Location: {context.get('location', 'Not specified')}

Provide interview preparation in this format:

EXPECTED_QUESTIONS:
- Question
- Question

HOW_TO_ANSWER:
- Question: guidance on how to answer (not a script)

MARKET_AND_COMP:
- Typical salary range
- How competitive this role is
- How to answer salary expectations

INTERVIEW_STRATEGY:
- What to emphasize
- What to avoid
"""

        response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)

        return AgentOutput(
            agent_name=self.name,
            score=85,
            findings=[
                "Interview preparation generated",
            ],
            recommendations=self._extract_section(response, "INTERVIEW_STRATEGY"),
            optimized_content=response,
            raw_analysis=response,
            weight=0.5,
        )
