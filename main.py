from fastapi import FastAPI
from src.api.v1.routers import analyzer

app = FastAPI(title="Google Business Profile Analyzer API", version="0.0.1")

app.include_router(analyzer.router, prefix="/v1", tags=["Analyzer"])

app.get("/", tags=["Root"])


async def root():
    return {"message": "Welcome to the GMB Analyzer API!", "documentation": "/docs"}
