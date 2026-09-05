from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.utils.logging import setup_logging
from backend.app.api.middleware import RequestIDMiddleware, LoggingMiddleware

# Initialize structured logging
setup_logging(service_name=settings.APP_NAME)

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous collaboration for modern development teams.",
    version="1.0.0",
)

# Add Middlewares
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
