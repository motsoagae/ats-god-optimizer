"""
ATS-GOD Base Agent
Supports both Groq (free) and OpenAI — auto-detects which key is available.
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentOutput(BaseModel):
    agent_name: str = ""
    score: int = 0
    findings: List[str] = []
    recommendations: List[str] = []
    optimized_content: str = ""
    raw_analysis: str = ""
    weight: float = 1.0


class BaseAgent(ABC):
    def __init__(self, name: str, llm=None):
        self.name = name
        self.llm = llm

    def _get_llm_response(self, system_prompt: str, user_prompt: str) -> str:
        if not self.llm:
            return self._rule_based_fallback(user_prompt)
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.warning(f"[{self.name}] LLM call failed: {e}")
            return self._rule_based_fallback(user_prompt)

    def _rule_based_fallback(self, prompt: str) -> str:
        return f"[Rule-based mode — add GROQ_API_KEY or OPENAI_API_KEY for AI analysis]\nAgent: {self.name}"

    @abstractmethod
    async def analyze(self, cv_text: str, job_description: str, context: Dict[str, Any]) -> AgentOutput:
        pass
