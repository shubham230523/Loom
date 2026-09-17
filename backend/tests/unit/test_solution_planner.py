import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.agents.solution_planner import SolutionPlannerAgent, SolutionPlanOutput

@pytest.fixture
def agent():
    return SolutionPlannerAgent()

@pytest.mark.asyncio
async def test_create_plan_success(agent):
    db = AsyncMock()
    repo = MagicMock(id="r1", full_name="o/n", language="python")
    index = MagicMock(summary={"architecture_summary": "Arch"})
    opp = MagicMock(title="T", description="D", type="bug")

    mock_plan = SolutionPlanOutput(
        problem="P",
        root_cause="RC",
        relevant_files=["f1.py"],
        implementation_steps=["Step 1"],
        confidence=0.9
    )

    with patch("backend.app.agents.solution_planner.semantic_search_service", new_callable=AsyncMock) as mock_search, \
         patch("backend.app.agents.solution_planner.ai_gateway", new_callable=AsyncMock) as mock_ai:

        mock_search.search.return_value = [
            {"type": "file", "path": "f1.py"},
            {"type": "symbol", "name": "my_func", "symbol_type": "function", "path": "f2.py"}
        ]
        mock_ai.chat_structured.return_value = mock_plan

        plan = await agent.create_plan(db, repo, index, opp)

        assert plan.problem == "P"
        assert "f1.py" in plan.relevant_files
        mock_ai.chat_structured.assert_called_once()

        # Verify symbol was included in prompt
        args, kwargs = mock_ai.chat_structured.call_args
        prompt = kwargs["request"].messages[1].content
        assert "- Function: my_func in f2.py" in prompt

@pytest.mark.asyncio
async def test_create_plan_with_issue(agent):
    db = AsyncMock()
    repo = MagicMock(id="r1", full_name="o/n", language="python")
    index = MagicMock(summary={"architecture_summary": "Arch"})
    opp = MagicMock(title="T", description="D", type="bug")
    issue = MagicMock(number=123, title="Issue T", body="Issue B")

    mock_plan = SolutionPlanOutput(
        problem="P",
        root_cause="RC",
        implementation_steps=["Step 1"]
    )

    with patch("backend.app.agents.solution_planner.semantic_search_service", new_callable=AsyncMock) as mock_search, \
         patch("backend.app.agents.solution_planner.ai_gateway", new_callable=AsyncMock) as mock_ai:

        mock_search.search.return_value = []
        mock_ai.chat_structured.return_value = mock_plan

        await agent.create_plan(db, repo, index, opp, issue=issue)

        args, kwargs = mock_ai.chat_structured.call_args
        prompt = kwargs["request"].messages[1].content
        assert "[UNTRUSTED LINKED ISSUE]" in prompt
        assert "#123: Issue T" in prompt

def test_solution_plan_output_validation():
    # Test stringify_nested_objects validator with dict and nested list
    data = {
        "problem": {"issue": "complex", "details": ["part1", "part2"]},
        "root_cause": "missing check",
        "relevant_files": ["a.py"],
        "implementation_steps": [{"action": "fix", "details": "here"}]
    }
    plan = SolutionPlanOutput(**data)
    assert "issue: complex" in plan.problem
    assert "details: [\"part1\", \"part2\"]" in plan.problem
    assert plan.implementation_steps == ["fix: here"]

def test_solution_plan_flatten_steps_complex():
    # Test flatten_steps with nested phases
    data = {
        "problem": "P",
        "root_cause": "RC",
        "implementation_steps": {
            "phase1": ["step1", {"action": "step2", "details": "d2"}],
            "phase2": {"steps": ["step3"]}
        }
    }
    plan = SolutionPlanOutput(**data)
    assert "step1" in plan.implementation_steps
    assert "step2: d2" in plan.implementation_steps
    assert "step3" in plan.implementation_steps

def test_solution_plan_flatten_steps_action_only():
    data = {
        "problem": "P",
        "root_cause": "RC",
        "implementation_steps": [{"action": "only action"}]
    }
    plan = SolutionPlanOutput(**data)
    assert plan.implementation_steps == ["only action"]

def test_solution_plan_flatten_steps_misc():
    data = {
        "problem": "P",
        "root_cause": "RC",
        "implementation_steps": "just a string"
    }
    plan = SolutionPlanOutput(**data)
    assert plan.implementation_steps == ["just a string"]
