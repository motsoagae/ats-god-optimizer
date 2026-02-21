from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentOutput

SYSTEM_PROMPT = """
You are a career strategy AI. Your job is to read a candidate's resume and job history and:

1. Identify the most likely current role they are targeting.
2. Suggest other roles they could realistically qualify for, even if not fully aligned.
3. Provide guidance on which skills, certifications, or experience gaps to bridge for these roles.
4. Suggest the confidence level for each alternative role.

Be practical, honest, and give actionable recommendations.
"""

class CareerScanner(BaseAgent):
    def __init__(self, llm=None):
        super().__init__("Career Scanner", llm)

    async def analyze(
        self,
        cv_text: str,
        context: Dict[str, Any]
    ) -> AgentOutput:

        user_prompt = f"""
CANDIDATE RESUME:
{cv_text[:3000]}

CONTEXT:
- Experience Level: {context.get('experience_level', 'Mid')}
- Industry: {context.get('industry', 'Not specified')}
- Location: {context.get('location', 'Not specified')}

Provide a list of:

PRIMARY_ROLE: Most likely current role

ALTERNATIVE_ROLES:
- Role: confidence % 
  Reasoning
  Key skills to bridge gap

RECOMMENDATIONS:
- Actionable next steps to qualify for alternative roles
"""

        response = self._get_llm_response(SYSTEM_PROMPT, user_prompt)

        return AgentOutput(
            agent_name=self.name,
            score=90,
            findings=["Career paths identified"],
            recommendations=self._extract_section(response, "RECOMMENDATIONS"),
            optimized_content=response,
            raw_analysis=response,
            weight=0.5,
        )
