import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.repository.matchmaker import MatchmakerService
from backend.app.database.models import Opportunity, Repository
import uuid

@pytest.mark.asyncio
async def test_get_recommendations_success():
    service = MatchmakerService()
    db = AsyncMock()

    mock_opp = Opportunity(id=uuid.uuid4(), title="T", description="D", type="bug", difficulty="easy", impact="high", score=90.0, confidence=0.9)
    mock_repo = Repository(id=uuid.uuid4(), full_name="o/r", language="python", owner="o", name="r", stargazers_count=100)

    mock_res = MagicMock()
    mock_res.__iter__.return_value = [(mock_opp, mock_repo)]
    db.execute.return_value = mock_res

    res = await service.get_recommendations(db, types=["bug"], difficulties=["easy"], languages=["python"])
    assert len(res) == 1
    assert res[0]["opportunity"]["title"] == "T"
    assert res[0]["repository"]["full_name"] == "o/r"

@pytest.mark.asyncio
async def test_get_recommendations_no_filters():
    service = MatchmakerService()
    db = AsyncMock()
    db.execute.return_value = []
    res = await service.get_recommendations(db)
    assert res == []
