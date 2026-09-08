from pydantic import BaseModel, Field, AliasChoices, field_validator
from typing import List, Dict, Any, Optional, Union
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType
from backend.app.utils.logging import logger

class CriterionScore(BaseModel):
    score: int = Field(ge=0, le=100)
    reasoning: str = Field(default="No reasoning provided")

    @field_validator("score", mode="before")
    @classmethod
    def parse_score(cls, v: Any) -> int:
        if isinstance(v, dict) and "score" in v:
            return v["score"]
        if isinstance(v, (int, float, str)):
            try:
                return int(v)
            except (ValueError, TypeError):
                return 0
        return 0

    @field_validator("reasoning", mode="before")
    @classmethod
    def parse_reasoning(cls, v: Any) -> str:
        if isinstance(v, dict) and "reasoning" in v:
            return str(v["reasoning"])
        if isinstance(v, str):
            return v
        return "No reasoning provided"

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs):
        if isinstance(obj, (int, float)):
            return cls(score=int(obj), reasoning="No reasoning provided")
        return super().model_validate(obj, *args, **kwargs)

class OpportunityScoreCard(BaseModel):
    overall_score: int = Field(
        ge=0, le=100,
        description="The weighted average score for this opportunity",
        validation_alias=AliasChoices("overall_score", "overallScore", "weighted_overall_score", "total_score", "score", "weighted_score")
    )

    impact: CriterionScore = Field(
        description="Potential value added to the project",
        validation_alias=AliasChoices("impact", "impact_score", "potential_impact")
    )
    difficulty: CriterionScore = Field(
        description="Technical challenge and effort required",
        validation_alias=AliasChoices("difficulty", "difficulty_score", "complexity")
    )
    reproducibility: CriterionScore = Field(
        description="Ease of confirming and verifying the issue",
        validation_alias=AliasChoices("reproducibility", "reproducible", "reproducibility_score")
    )
    repository_fit: CriterionScore = Field(
        description="How well this aligns with the project's goals and architecture",
        validation_alias=AliasChoices("repository_fit", "repositoryFit", "project_fit", "fit", "alignment")
    )
    maintainer_activity: CriterionScore = Field(
        description="Likelihood of a PR being reviewed based on recent activity",
        validation_alias=AliasChoices("maintainer_activity", "maintainerActivity", "activity", "maintainer_responsiveness")
    )
    duplicate_risk: CriterionScore = Field(
        description="Risk of this work overlapping with existing PRs or issues",
        validation_alias=AliasChoices("duplicate_risk", "duplicateRisk", "duplication", "overlap_risk")
    )
    testability: CriterionScore = Field(
        description="How easily this change can be verified with automated tests",
        validation_alias=AliasChoices("testability", "testability_score")
    )

    summary_reasoning: str = Field(
        description="Overall justification for the final score",
        validation_alias=AliasChoices("summary_reasoning", "reasoning", "analysis", "explanation", "justification", "summary"),
        default="Scored by AI agent"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "ignore"
    }

    @field_validator("impact", "difficulty", "reproducibility", "repository_fit", "maintainer_activity", "duplicate_risk", "testability", mode="before")
    @classmethod
    def ensure_criterion_object(cls, v: Any) -> Any:
        if isinstance(v, (int, float)):
            return {"score": int(v), "reasoning": "No reasoning provided"}
        return v

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
