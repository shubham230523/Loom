import pytest
from backend.app.database.session import get_db

@pytest.mark.asyncio
async def test_get_db_direct():
    db_gen = get_db()
    db = await db_gen.__anext__()
    assert db is not None
    try:
        await db_gen.__anext__()
    except StopAsyncIteration:
        pass
