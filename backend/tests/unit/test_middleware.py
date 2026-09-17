import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.api.middleware import RequestIDMiddleware, LoggingMiddleware, RateLimitMiddleware

def test_request_id_middleware():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/")
    def read_root():
        return {"hello": "world"}

    client = TestClient(app)

    # Test auto-generation
    response = client.get("/")
    assert "X-Request-ID" in response.headers

    # Test passing existing ID
    rid = "test-rid-123"
    response = client.get("/", headers={"X-Request-ID": rid})
    assert response.headers["X-Request-ID"] == rid

@pytest.mark.asyncio
async def test_logging_middleware_exception():
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get("/error")
    def trigger_error():
        raise ValueError("Boom")

    client = TestClient(app)
    with pytest.raises(ValueError):
        client.get("/error")

@pytest.mark.asyncio
async def test_rate_limit_middleware_success():
    app = FastAPI()
    # Mock settings to not be development
    with patch("backend.app.api.middleware.settings") as mock_settings:
        mock_settings.DEBUG = False
        mock_settings.ENVIRONMENT = "production"
        app.add_middleware(RateLimitMiddleware, limit=5)

        @app.get("/")
        def read_root():
            return {"ok": True}

        client = TestClient(app)

        with patch("backend.app.api.middleware.redis_service", new_callable=AsyncMock) as mock_redis:
            # 1. New key
            mock_redis.get.return_value = None
            response = client.get("/")
            assert response.status_code == 200
            mock_redis.set.assert_called_once()

            # 2. Existing key under limit
            mock_redis.get.return_value = "3"
            response = client.get("/")
            assert response.status_code == 200
            mock_redis.client.incr.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_middleware_exceeded():
    app = FastAPI()
    with patch("backend.app.api.middleware.settings") as mock_settings:
        mock_settings.DEBUG = False
        mock_settings.ENVIRONMENT = "production"
        app.add_middleware(RateLimitMiddleware, limit=5)

        client = TestClient(app)

        with patch("backend.app.api.middleware.redis_service", new_callable=AsyncMock) as mock_redis:
            mock_redis.get.return_value = "5" # limit reached
            response = client.get("/")
            assert response.status_code == 429
            assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

@pytest.mark.asyncio
async def test_rate_limit_middleware_redis_error():
    app = FastAPI()
    with patch("backend.app.api.middleware.settings") as mock_settings:
        mock_settings.DEBUG = False
        mock_settings.ENVIRONMENT = "production"
        app.add_middleware(RateLimitMiddleware)

        @app.get("/")
        def read_root():
            return {"ok": True}

        client = TestClient(app)

        with patch("backend.app.api.middleware.redis_service", new_callable=AsyncMock) as mock_redis:
            mock_redis.get.side_effect = Exception("Redis down")
            response = client.get("/")
            assert response.status_code == 200 # Should fall through to next middleware

def test_rate_limit_middleware_dev_mode():
    app = FastAPI()
    with patch("backend.app.api.middleware.settings") as mock_settings:
        mock_settings.DEBUG = True
        mock_settings.ENVIRONMENT = "development"
        app.add_middleware(RateLimitMiddleware)

        @app.get("/")
        def read_root():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
