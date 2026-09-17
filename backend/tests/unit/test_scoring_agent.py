import pytest
from unittest.mock import AsyncMock, patch
from backend.app.agents.scoring_agent import CriterionScore, OpportunityScoreCard, ScoringAgent

def test_criterion_score_parse_score():
    # dict with "score"
    assert CriterionScore.parse_score({"score": 85}) == 85
    # int, float, str
    assert CriterionScore.parse_score(90) == 90
    assert CriterionScore.parse_score(90.5) == 90
    assert CriterionScore.parse_score("95") == 95
    # invalid str/types
    assert CriterionScore.parse_score("invalid") == 0
    assert CriterionScore.parse_score([]) == 0

def test_criterion_score_parse_reasoning():
    # dict with "reasoning"
    assert CriterionScore.parse_reasoning({"reasoning": "Good"}) == "Good"
    # str
    assert CriterionScore.parse_reasoning("Excellent") == "Excellent"
    # fallback
    assert CriterionScore.parse_reasoning([]) == "No reasoning provided"

def test_criterion_score_model_validate():
    card = CriterionScore.model_validate(75)
    assert card.score == 75
    assert card.reasoning == "No reasoning provided"

def test_opportunity_score_card_ensure_criterion():
    card = OpportunityScoreCard(
        overall_score=80,
        impact=90,
        difficulty=85,
        reproducibility=70,
        repository_fit=95,
        maintainer_activity=60,
        duplicate_risk=50,
        testability=40,
        summary_reasoning="Looks good"
    )
    assert card.impact.score == 90
    assert card.difficulty.score == 85

@pytest.mark.asyncio
async def test_score_opportunity():
    agent = ScoringAgent()
    mock_card = OpportunityScoreCard(
        overall_score=80,
        impact=CriterionScore(score=90, reasoning="I"),
        difficulty=CriterionScore(score=80, reasoning="D"),
        reproducibility=CriterionScore(score=70, reasoning="R"),
        repository_fit=CriterionScore(score=85, reasoning="RF"),
        maintainer_activity=CriterionScore(score=60, reasoning="MA"),
        duplicate_risk=CriterionScore(score=75, reasoning="DR"),
        testability=CriterionScore(score=95, reasoning="T"),
        summary_reasoning="Overall good"
    )

    with patch("backend.app.ai.gateway.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_card
        res = await agent.score_opportunity(
            repository_name="repo",
            architecture_summary="arch",
            opportunity_title="title",
            opportunity_description="desc",
            signals_context="signals",
            maintainer_context="maintainer"
        )
        assert res.overall_score == 80
        mock_chat.assert_called_once()
