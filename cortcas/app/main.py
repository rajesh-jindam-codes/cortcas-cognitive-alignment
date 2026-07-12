from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import sub-routers
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.students import router as student_router
from app.api.v1.endpoints.sessions import router as session_router
from app.api.v1.endpoints.predictions import router as prediction_router
from app.api.v1.endpoints.dashboard import router as dashboard_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Continuous Observation & Reality-Tracked Cognitive Alignment System (CORTCAS) API Layer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(student_router, prefix="/api/v1/students", tags=["Students"])
app.include_router(session_router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(prediction_router, prefix="/api/v1/predictions", tags=["Machine Learning Predictions"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard Statistics"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "healthy",
        "service": "CORTCAS Cognitive Alignment backend service layer",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
