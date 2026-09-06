from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType
from backend.app.utils.logging import logger

class CriterionScore(BaseModel):
    score: int = Field(ge=0, le=100)
    reasoning: str

class OpportunityScoreCard(BaseModel):
    overall_score: int = Field(ge=0, le=100, description="The weighted average score for this opportunity")

    impact: CriterionScore = Field(description="Potential value added to the project")
    difficulty: CriterionScore = Field(description="Technical challenge and effort required")
    reproducibility: CriterionScore = Field(description="Ease of confirming and verifying the issue")
    repository_fit: CriterionScore = Field(description="How well this aligns with the project's goals and architecture")
    maintainer_activity: CriterionScore = Field(description="Likelihood of a PR being reviewed based on recent activity")
    duplicate_risk: CriterionScore = Field(description="Risk of this work overlapping with existing PRs or issues")
    testability: CriterionScore = Field(description="How easily this change can be verified with automated tests")

    summary_reasoning: str = Field(description="Overall justification for the final score")

class ScoringAgent:
    async def score_opportunity(
        self,
        repository_name: str,
        architecture_summary: str,
        opportunity_title: str,
        opportunity_description: str,
        signals_context: str,
        maintainer_context: str
    ) -> OpportunityScoreCard:
        """
        Calculates a multi-criteria score for a contribution opportunity.
        """
        logger.info(f"ScoringAgent: Scoring opportunity '{opportunity_title}' for {repository_name}")

        prompt = f"""
        You are an expert technical project manager and open-source contributor.
        Your task is to score a potential contribution opportunity for the repository '{repository_name}'.

        REPOSITORY ARCHITECTURE:
        {architecture_summary}

        MAINTAINER ACTIVITY CONTEXT:
        {maintainer_context}

        OPPORTUNITY:
        Title: {opportunity_title}
        Description: {opportunity_description}

        EVIDENCE & SIGNALS:
        {signals_context}

        INSTRUCTIONS:
        1. Score each criterion from 0 to 100.
        2. Impact: 100 = critical fix/feature; 0 = trivial/irrelevant.
        3. Difficulty: 100 = extremely easy; 0 = extremely complex (Note: higher is better for scoring).
        4. Reproducibility: 100 = clear steps; 0 = vague/intermittent.
        5. Repository Fit: 100 = perfectly aligned; 0 = out of scope.
        6. Maintainer Activity: 100 = very active, likely review; 0 = stagnant.
        7. Duplicate Risk: 100 = definitely unique; 0 = clear duplicate.
        8. Testability: 100 = easy to test unitarily; 0 = hard to verify.
        9. Calculate an weighted overall score (0-100).
        """

        request = ChatRequest(
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a meticulous technical auditor for open-source contributions."),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
        )

        return await ai_gateway.chat_structured(
            request=request,
            response_model=OpportunityScoreCard,
            task=TaskType.PLANNING # Reusing planning task type
        )

scoring_agent = ScoringAgent()
