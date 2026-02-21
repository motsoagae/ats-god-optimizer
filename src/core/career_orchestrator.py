from typing import Dict, Any
from src.agents.career_scanner import CareerScanner

class CareerOrchestrator:
    def __init__(self, llm=None):
        self.scanner = CareerScanner(llm)

    async def analyze_career(self, cv_text: str, context: Dict[str, Any]):
        return await self.scanner.analyze(cv_text=cv_text, context=context)
