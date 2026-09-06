from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from backend.app.config import settings
from backend.app.utils.logging import setup_logging
from backend.app.api.middleware import RequestIDMiddleware, LoggingMiddleware, RateLimitMiddleware
from backend.app.api.errors import (
    LoomError,
    loom_error_handler,
    validation_error_handler,
    universal_error_handler
)
from backend.app.api.v1 import api_v1_router
from backend.app.api.ws import router as ws_router
from backend.app.services.redis import redis_service

# Initialize structured logging
setup_logging(service_name=settings.APP_NAME)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis
    await redis_service.connect()
    yield
    # Shutdown: Disconnect from Redis
    await redis_service.disconnect()

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous collaboration for modern development teams.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register Routers
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws")

# Error Handlers
app.add_exception_handler(LoomError, loom_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, universal_error_handler)

# Add Middlewares
app.add_middleware(RateLimitMiddleware, limit=100, window=60)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)

# Configure CORS for frontend access (Android, iOS, Web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "app": "Loom API",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
