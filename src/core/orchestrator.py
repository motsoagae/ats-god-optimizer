"""
ATS-GOD Master Orchestrator
Runs all 9 agents in parallel. Supports Groq (free) + OpenAI.
Auto-detects which API key is available.
"""
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from src.agents.algorithm_breaker import AlgorithmBreaker
from src.agents.sa_specialist import SASpecialist
from src.agents.global_setter import GlobalSetter
from src.agents.recruiter_scanner import RecruiterScanner
from src.agents.hiring_manager_whisperer import HiringManagerWhisperer
from src.agents.semantic_matcher import SemanticMatcher
from src.agents.compliance_guardian import ComplianceGuardian
from src.agents.future_architect import FutureArchitect
from src.agents.cover_letter_agent import CoverLetterAgent
from src.agents.base_agent import AgentOutput

logger = logging.getLogger(__name__)


def create_llm():
    """
    Auto-detect and create LLM client.
    Priority: Groq (free) → OpenAI (paid) → Anthropic (paid) → None (rule-based)
    """
    # 1. Try Groq (free tier — recommended)
    groq_key = os.getenv("GROQ_API_KEY", "")
    if groq_key and not groq_key.startswith("gsk_your"):
        try:
            from langchain_groq import ChatGroq
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            llm = ChatGroq(api_key=groq_key, model=model, temperature=0.3, max_tokens=1500)
            logger.info(f"✓ Using Groq LLM: {model}")
            return llm, "Groq", model
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    # 2. Try OpenAI
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-your"):
        try:
            from langchain_openai import ChatOpenAI
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(api_key=openai_key, model=model, temperature=0.3, max_tokens=1500)
            logger.info(f"✓ Using OpenAI LLM: {model}")
            return llm, "OpenAI", model
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")

    # 3. Try Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key and not anthropic_key.startswith("sk-ant-your"):
        try:
            from langchain_anthropic import ChatAnthropic
            model = "claude-haiku-4-5-20251001"
            llm = ChatAnthropic(api_key=anthropic_key, model=model, temperature=0.3, max_tokens=1500)
            logger.info(f"✓ Using Anthropic LLM: {model}")
            return llm, "Anthropic", model
        except Exception as e:
            logger.warning(f"Anthropic init failed: {e}")

    logger.info("No API key found — running in rule-based mode. Add GROQ_API_KEY for AI analysis.")
    return None, "Rule-Based", "None"


class ATSGodOrchestrator:
    """Master coordinator — runs all 9 agents, generates 3 CV variants + cover letter."""

    AGENT_ICONS = {
        "algorithm_breaker": "🎯",
        "sa_specialist": "🇿🇦",
        "global_setter": "🌍",
        "recruiter_scanner": "👁️",
        "hiring_manager": "💼",
        "semantic_matcher": "📊",
        "compliance_guardian": "⚖️",
        "future_architect": "🚀",
    }

    def __init__(self):
        self.llm, self.llm_provider, self.llm_model = create_llm()
        self.ai_mode = self.llm is not None

        self.agents = {
            "algorithm_breaker": AlgorithmBreaker(self.llm),
            "sa_specialist": SASpecialist(self.llm),
            "global_setter": GlobalSetter(self.llm),
            "recruiter_scanner": RecruiterScanner(self.llm),
            "hiring_manager": HiringManagerWhisperer(self.llm),
            "semantic_matcher": SemanticMatcher(self.llm),
            "compliance_guardian": ComplianceGuardian(self.llm),
            "future_architect": FutureArchitect(self.llm),
        }
        self.cover_agent = CoverLetterAgent(self.llm)

        status = f"🧠 {self.llm_provider} ({self.llm_model})" if self.ai_mode else "📐 Rule-Based"
        logger.info(f"ATS-GOD Orchestrator ready — {status}")

    async def optimize(
        self,
        cv_text: str,
        job_description: str,
        context: Dict[str, Any],
        generate_cover_letter: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Full optimization pipeline — all agents in parallel."""

        start = datetime.now()

        def _progress(pct: float, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        _progress(0.05, f"🚀 Starting 8 specialist agents ({self.llm_provider} mode)...")

        # Phase 1: Run all 8 agents in parallel
        agent_results = await self._run_parallel(cv_text, job_description, context, _progress)

        _progress(0.80, "📊 Synthesizing agent results...")

        # Phase 2: Build weighted summary
        summary = self._build_summary(agent_results, context)

        # Phase 3: Generate 3 CV variants
        _progress(0.85, "✍️ Generating 3 CV variants...")
        variants = self._generate_variants(cv_text, agent_results, summary)

        # Phase 4: Cover letter
        cover_letter = ""
        if generate_cover_letter:
            _progress(0.90, "📝 Writing cover letter...")
            try:
                cl_result = await asyncio.wait_for(
                    self.cover_agent.analyze(cv_text, job_description, context), timeout=60
                )
                cover_letter = cl_result.optimized_content
            except Exception as e:
                logger.error(f"Cover letter failed: {e}")
                cover_letter = "Cover letter generation failed — try again."

        # Phase 5: Compile action items
        _progress(0.95, "🔍 Compiling priority action items...")
        action_items = self._compile_actions(agent_results)

        elapsed = round((datetime.now() - start).total_seconds(), 1)
        _progress(1.0, f"✅ Complete in {elapsed}s!")

        return {
            "summary": summary,
            "agent_results": {k: v.dict() for k, v in agent_results.items()},
            "cv_variants": variants,
            "cover_letter": cover_letter,
            "action_items": action_items,
            "ai_mode": self.ai_mode,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "metadata": {
                "execution_seconds": elapsed,
                "timestamp": datetime.now().isoformat(),
                "version": "4.0.0",
                "agents_run": len(agent_results),
            }
        }

    async def _run_parallel(
        self,
        cv: str,
        jd: str,
        ctx: Dict,
        progress_cb: Callable
    ) -> Dict[str, AgentOutput]:
        """Run all 8 agents concurrently with progress updates."""

        tasks = {
            name: asyncio.create_task(self._safe_run(agent, cv, jd, ctx))
            for name, agent in self.agents.items()
        }

        results = {}
        completed = 0

        for name, task in tasks.items():
            try:
                result = await asyncio.wait_for(asyncio.shield(task), timeout=90)
                results[name] = result
                logger.info(f"Agent '{name}': {result.score}/100")
            except asyncio.TimeoutError:
                logger.error(f"Agent '{name}' timed out")
                results[name] = AgentOutput(
                    agent_name=name, score=50,
                    findings=["⚠️ Timed out — result may be incomplete"],
                    recommendations=["Re-run for complete analysis"]
                )
            except Exception as e:
                logger.error(f"Agent '{name}' error: {e}")
                results[name] = AgentOutput(
                    agent_name=name, score=50,
                    findings=[f"⚠️ Error: {str(e)[:100]}"],
                    recommendations=["Check API key and retry"]
                )

            completed += 1
            icon = self.AGENT_ICONS.get(name, "🤖")
            pct = 0.05 + (completed / len(tasks)) * 0.72
            progress_cb(pct, f"{icon} {name.replace('_', ' ').title()} complete ({completed}/{len(tasks)})")

        return results

    async def _safe_run(self, agent, cv, jd, ctx) -> AgentOutput:
        return await agent.analyze(cv, jd, ctx)

    def _build_summary(self, results: Dict[str, AgentOutput], context: Dict) -> Dict[str, Any]:
        """Weighted scoring based on target market."""

        market = context.get('target_market', 'Both')
        priority_weights = {
            'South Africa': {'sa_specialist': 2.0, 'algorithm_breaker': 1.8, 'compliance_guardian': 1.5},
            'International': {'global_setter': 2.0, 'algorithm_breaker': 1.8, 'semantic_matcher': 1.5},
            'Both': {'algorithm_breaker': 1.8, 'sa_specialist': 1.4, 'global_setter': 1.4},
        }.get(market, {})

        total_w, weighted_sum = 0, 0
        scores = {}

        for name, result in results.items():
            w = priority_weights.get(name, result.weight)
            weighted_sum += result.score * w
            total_w += w
            scores[name] = result.score

        overall = round(weighted_sum / total_w, 1) if total_w else 0

        if overall >= 82:
            variant, verdict = "BALANCED", "Strong profile — balanced optimization recommended."
        elif overall >= 65:
            variant, verdict = "ATS-MAX", "Good foundation — prioritize ATS keyword optimization."
        else:
            variant, verdict = "ATS-MAX", "Significant gaps — start with ATS-MAX and work through action items."

        return {
            "overall_score": overall,
            "recommended_variant": variant,
            "verdict": verdict,
            "interview_probability": min(95, int(overall * 0.88 + 8)),
            "agent_scores": scores,
            "weakest_area": min(scores, key=scores.get) if scores else "",
            "strongest_area": max(scores, key=scores.get) if scores else "",
            "target_market": market,
        }

    def _generate_variants(
        self,
        original_cv: str,
        results: Dict[str, AgentOutput],
        summary: Dict
    ) -> Dict[str, str]:
        """Generate 3 optimized CV variants."""

        score = summary['overall_score']
        ts = datetime.now().strftime('%d %B %Y')

        # Collect agent-generated content
        algo_summary = results.get('algorithm_breaker', AgentOutput()).optimized_content
        sa_summary = results.get('sa_specialist', AgentOutput()).optimized_content
        global_summary = results.get('global_setter', AgentOutput()).optimized_content
        clean_summary = results.get('compliance_guardian', AgentOutput()).optimized_content
        semantic_bridge = results.get('semantic_matcher', AgentOutput()).optimized_content
        career_narrative = results.get('future_architect', AgentOutput()).optimized_content
        improved_bullet = results.get('recruiter_scanner', AgentOutput()).optimized_content

        # Missing keywords from algorithm breaker
        algo_findings = results.get('algorithm_breaker', AgentOutput()).findings
        missing_kw = next((f for f in algo_findings if 'Missing' in f), "")

        header = f"""╔══════════════════════════════════════════════════════════╗
║           ATS-GOD OPTIMIZED CV — {ts}           ║
║                 Overall Score: {score}/100                  ║
╚══════════════════════════════════════════════════════════╝

"""

        ats_max = f"""{header}═══ ATS-MAX VARIANT (Algorithmic Score Priority) ═══
Target: 95%+ ATS parse rate | Best for: Large corporations, strict ATS

OPTIMIZED PROFESSIONAL SUMMARY:
{algo_summary or clean_summary or '[REPLACE: Paste your summary here and apply agent recommendations]'}

SEMANTIC KEYWORD ADDITIONS:
{semantic_bridge or '[Add job description keywords throughout your experience section]'}

KEYWORD GAP NOTE:
{missing_kw or 'Run optimization to identify missing keywords'}

══════════════ ORIGINAL CV (Apply changes above) ══════════════
{original_cv}"""

        balanced = f"""{header}═══ BALANCED VARIANT ⭐ RECOMMENDED (ATS + Human Appeal) ═══
Target: 85-95% ATS | Best for: Most applications

PROFESSIONAL SUMMARY:
{career_narrative or clean_summary or '[Apply the career narrative from Future Architect agent above]'}

SEMANTIC CONTEXT:
{semantic_bridge or '[Mirror JD language in your experience descriptions]'}

IMPROVED ACHIEVEMENT EXAMPLE:
{improved_bullet or '[Apply the improved bullet from Recruiter Scanner agent above]'}

══════════════ ORIGINAL CV (Apply changes above) ══════════════
{original_cv}"""

        creative = f"""{header}═══ CREATIVE VARIANT (Human-First) ═══
Target: 75-85% ATS | Best for: Startups, agencies, creative roles

CAREER NARRATIVE OPENING:
{career_narrative or '[Build your compelling career story around progression and impact]'}

SA MARKET ANGLE:
{sa_summary or global_summary or '[Add market-specific positioning]'}

══════════════ ORIGINAL CV (Apply changes above) ══════════════
{original_cv}"""

        return {"ats_max": ats_max, "balanced": balanced, "creative": creative}

    def _compile_actions(self, results: Dict[str, AgentOutput]) -> List[str]:
        """Priority-sorted, deduplicated action items."""

        weighted = []
        for name, result in results.items():
            urgency = 1.0 + (100 - result.score) / 40
            for rec in result.recommendations[:4]:
                if rec and len(rec) > 10:
                    weighted.append((urgency, rec))

        weighted.sort(key=lambda x: x[0], reverse=True)

        seen, unique = set(), []
        for _, rec in weighted:
            norm = rec.lower()[:60]
            if norm not in seen:
                seen.add(norm)
                unique.append(rec)

        return unique[:15]
