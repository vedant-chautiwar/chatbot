from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import settings
from app.database.indexes import init_indexes
from app.database.mongodb import mongodb_manager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT != "development" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing backend application in environment: %s", settings.ENVIRONMENT)
    settings.validate_runtime_keys()

    # Connect to MongoDB Atlas
    await mongodb_manager.connect(settings.MONGODB_URI, settings.MONGODB_DATABASE)
    await init_indexes(mongodb_manager)

    yield

    # Clean shutdown of connection pools
    logger.info("Shutting down backend application...")
    await mongodb_manager.close()


app = FastAPI(
    title="Agentic AI Chatbot with Intelligent Web Search API",
    description=(
        "Production backend for an agentic AI chatbot built with FastAPI, LangGraph, "
        "Groq LLM, Tavily Search, FastAPI JWT Auth, and MongoDB Atlas."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Centralized Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format request validation errors consistently without exposing internal details."""
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []))
        errors.append({"field": field, "message": err.get("msg")})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Request validation failed", "errors": errors},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Ensure standard JSON responses for HTTP exceptions."""
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Safely catch all unhandled exceptions without leaking stack traces to clients."""
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Include API Router
app.include_router(api_router)


@app.get("/", summary="Root health check")
async def root():
    return {
        "service": "Agentic AI Chatbot Backend",
        "status": "online",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "disabled",
    }
