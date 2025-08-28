# syntax=docker/dockerfile:1
# Final Version: A secure, efficient, and reliable Dockerfile combining best practices.

# =================================================================
# 1. Base Image: Start with a specific, small, and official Python image.
# =================================================================
FROM python:3.12-slim-bullseye

# =================================================================
# 2. Environment Setup: Configure the environment for non-interactive builds.
#    - Use global locations for Poetry and Playwright so all users can access them.
# =================================================================
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_HOME="/opt/poetry"
ENV PLAYWRIGHT_BROWSERS_PATH="/ms-playwright"
ENV PATH="$POETRY_HOME/bin:$PATH"

# =================================================================
# 3. System Dependencies: Install curl for Poetry and build-essential for packages.
# =================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# =================================================================
# 4. Install Poetry
# =================================================================
RUN curl -sSL https://install.python-poetry.org | python3 -

# =================================================================
# 5. Application Setup: Create app directory and copy dependency files for caching.
# =================================================================
WORKDIR /app
COPY pyproject.toml poetry.lock* /app/

# =================================================================
# 6. Install Dependencies:
#    - Combine 'poetry install' and 'playwright install' into one layer for efficiency.
# =================================================================
RUN POETRY_INSTALLER_HTTP_TIMEOUT=300 poetry install --no-root --only main \
    && poetry run playwright install chromium --with-deps

# =================================================================
# 7. Security: Create a non-root user to run the application.
# =================================================================
RUN useradd --create-home --shell /bin/bash appuser

# =================================================================
# 8. Copy Application Code & Set Permissions
#    - Give the appuser ownership of the app code AND the Playwright browsers.
# =================================================================
COPY . /app
RUN chown -R appuser:appuser /app /ms-playwright

# =================================================================
# 9. Switch to Non-Root User
# =================================================================
USER appuser

# =================================================================
# 10. Expose Port & Define CMD
# =================================================================
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]