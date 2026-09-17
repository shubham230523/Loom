import pytest
from unittest.mock import MagicMock
from backend.app.api.errors import (
    LoomError, AuthenticationError, AuthorizationError, RateLimitError,
    loom_error_handler, validation_error_handler, universal_error_handler
)

@pytest.mark.asyncio
async def test_error_handlers():
    request = MagicMock()

    # LoomError
    exc1 = LoomError("fail", status_code=400, code="ERR", details="D")
    resp1 = await loom_error_handler(request, exc1)
    assert resp1.status_code == 400

    # Auth errors
    exc2 = AuthenticationError()
    assert exc2.status_code == 401

    exc3 = AuthorizationError()
    assert exc3.status_code == 403

    exc4 = RateLimitError()
    assert exc4.status_code == 429

    # Validation error
    from pydantic import ValidationError
    exc5 = MagicMock()
    exc5.errors.return_value = ["e"]
    resp5 = await validation_error_handler(request, exc5)
    assert resp5.status_code == 422

    # Universal handler
    exc6 = Exception("Boom")
    resp6 = await universal_error_handler(request, exc6)
    assert resp6.status_code == 500
