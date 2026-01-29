"""
Immobili Images API - Main application.

Public API for accessing property images and AI-generated descriptions.
Designed for embedding generation and content retrieval.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, immobili

# Create FastAPI app
app = FastAPI(
    title="Immobili Images API",
    description="""
    Public API for accessing property images with AI-generated descriptions.

    **Features:**
    - JWT Authentication
    - Public properties only (privacy filters applied)
    - Images with AI features from Gemini Vision
    - Optimized for embedding generation and content retrieval

    **Use case:**
    - Generate CLIP embeddings for image search
    - Content generation for blog articles
    - Property recommendation systems
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(immobili.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Immobili Images API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "auth": f"{settings.API_V1_PREFIX}/auth/login"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
