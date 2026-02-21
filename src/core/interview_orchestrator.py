from typing import Dict, Any
from src.agents.interview_coach import InterviewCoach


class InterviewOrchestrator:
    def __init__(self, llm=None):
        self.coach = InterviewCoach(llm)

    async def prepare_interview(
        self,
        cv_text: str,
        job_description: str,
        context: Dict[str, Any]
    ):
        return await self.coach.analyze(
            cv_text=cv_text,
            job_description=job_description,
            context=context,
        )
