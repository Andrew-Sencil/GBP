from fastapi import FastAPI
from src.api.v1.routers import analyzer
from src.api.v1.routers import site_socials
from src.api.v1.routers import llm_analysis

app = FastAPI(title="Google Business Profile Analyzer API", version="0.0.1")

app.include_router(analyzer.router, prefix="/v1", tags=["Analyzer"])
app.include_router(site_socials.router, prefix="/v1", tags=["Socials/Website"])
app.include_router(llm_analysis.router, prefix="/v1", tags=["LLM Detailed Analysis"])


app.get("/", tags=["Root"])


async def root():
    return {"message": "Welcome to the GMB Analyzer API!", "documentation": "/docs"}
