from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import Repository, RepositoryIndex, Issue, Opportunity
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType
from backend.app.utils.logging import logger

class OpportunityProposal(BaseModel):
    title: str = Field(description="Action-oriented title for the opportunity")
    description: str = Field(description="Detailed technical explanation of what needs to be done")
    type: str = Field(description="bug, feature, refactor, documentation, or testing")
    impact: str = Field(description="Low, Medium, or High")
    difficulty: str = Field(description="Easy, Intermediate, or Hard")
    confidence: float = Field(description="Score from 0.0 to 1.0 based on evidence strength")
    evidence_source: str = Field(description="The specific issue, TODO, or gap that triggered this")
    affected_files: List[str] = Field(description="List of files likely needing modification")

from pydantic import AliasChoices

class OpportunityList(BaseModel):
    opportunities: List[OpportunityProposal] = Field(
        default_factory=list,
        description="List of identified opportunities",
        validation_alias=AliasChoices("opportunities", "actionable_opportunities")
    )

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }

class OpportunityGeneratorAgent:
    async def generate_opportunities(
        self,
        db: AsyncSession,
        repository: Repository,
        index: RepositoryIndex,
        issues: List[Issue],
        code_signals: List[Dict[str, Any]],
        test_gaps: List[Dict[str, Any]],
        existing_prs: List[Dict[str, Any]]
    ) -> List[OpportunityProposal]:
        """
        Synthesizes various repository signals into concrete contribution opportunities.
        """
        logger.info(f"OpportunityGeneratorAgent: Generating opportunities for {repository.full_name}")

        # 1. Summarize context for the LLM
        issues_context = "\n".join([f"- Issue #{i.number}: {i.title}" for i in issues[:20]])

        # Group code signals to keep context manageable
        todo_count = len([s for s in code_signals if s["type"] == "TODO"])
        fixme_count = len([s for s in code_signals if s["type"] == "FIXME"])
        unimplemented = [s for s in code_signals if s["type"] == "UNIMPLEMENTED"][:10]

        signals_summary = f"""
        TODOs found: {todo_count}
        FIXMEs found: {fixme_count}
        Unimplemented snippets (samples):
        {chr(10).join([f"- {s['path']}:{s['line']} -> {s['content']}" for s in unimplemented])}
        """

        gaps_summary = "\n".join([f"- {g['path']}: {g['message']}" for g in test_gaps[:10]])

        pr_context = "\n".join([f"- PR #{p['number']}: {p['title']}" for p in existing_prs[:10]])

        prompt = f"""
        You are a senior engineering manager and architect. Your goal is to identify high-impact, actionable contribution opportunities for the following repository.

        REPOSITORY CONTEXT:
        Name: {repository.full_name}
        Architecture: {index.summary.get('architecture_summary') if index.summary else 'Unknown'}
        Tech Stack: {index.summary.get('technology_summary') if index.summary else 'Unknown'}

        OPEN ISSUES:
        {issues_context or "None found."}

        CODE SIGNALS:
        {signals_summary}

        TEST GAPS:
        {gaps_summary or "None found."}

        ACTIVE PULL REQUESTS (DO NOT duplicate these):
        {pr_context or "None active."}

        INSTRUCTIONS:
        1. Analyze these signals and find the top 5 most actionable opportunities.
        2. DO NOT invent work. Every opportunity must be linked to an actual issue, TODO, gap, or unimplemented function.
           NOTE: For documentation repositories (like guides or playbooks), a TODO or a missing section in a sequential guide is a valid signal.
        3. If no explicit TODOs or issues exist, suggest standard project high-impact improvements such as:
           - Creating a CONTRIBUTING.md or LICENSE if missing.
           - Improving README structure for better onboarding.
           - Suggesting a new section or chapter based on the existing repository patterns.
        4. Prioritize "low-hanging fruit" and "high-impact technical debt".
        5. Be technically specific in the description.
        6. YOU MUST RETURN A LIST OF OBJECTS. Each object in the "opportunities" list must have all fields: "title", "description", "type", "impact", "difficulty", "confidence", "evidence_source", and "affected_files".
        7. If NO actionable signals OR obvious project improvements are found, return an empty list for the "opportunities" field. Do NOT return other fields instead.
        """

        logger.info(f"OpportunityGeneratorAgent: Final prompt context summary: Issues={len(issues)}, Signals={len(code_signals)}, Gaps={len(test_gaps)}")

        request = ChatRequest(
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a strategic engineering leader identifying the most valuable work for a project."),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
        )

        logger.info(f"OpportunityGeneratorAgent: Sending request to AI Gateway...")
        try:
            result = await ai_gateway.chat_structured(
                request=request,
                response_model=OpportunityList,
                task=TaskType.PLANNING
            )
            logger.info(f"OpportunityGeneratorAgent: AI returned {len(result.opportunities)} opportunities.")
            if len(result.opportunities) == 0:
                logger.warning("OpportunityGeneratorAgent: AI returned zero opportunities!")
            return result.opportunities
        except Exception as e:
            logger.error(f"OpportunityGeneratorAgent: AI call failed: {str(e)}")
            raise e

opportunity_generator_agent = OpportunityGeneratorAgent()
