import uvicorn

from src.core.config import config


def start():
    """
    Run the FastAPI application using Uvicorn.
    """
    uvicorn.run(
        "src.main:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
    )
