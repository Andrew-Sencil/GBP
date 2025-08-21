# syntax=docker/dockerfile:1

# ---- Builder Stage ----
# This stage's only job is to install our Python dependencies into a .venv.
# We no longer need to install Playwright's browsers here.
FROM python:3.12-slim as builder
RUN pip install poetry==1.8.2
RUN poetry config virtualenvs.in-project true

# --- ADD THIS LINE ---
# Increase the HTTP timeout for installers to 5 minutes to handle slow network connections.
RUN poetry config installer.http-timeout 300

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main


# ---- Final, Production Stage ----
# --- THE DEFINITIVE FIX ---
# We start from the official Playwright image, which has all OS dependencies and browsers pre-installed.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy as base

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user for security.
# The Playwright image runs as root by default, so we create our own user.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/bin/sh" \
    --uid "${UID}" \
    appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv .venv

# Set the PATH to include our virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Switch to our non-privileged user
USER appuser

# Copy the application source code
COPY . .

EXPOSE 8000

# Run the application. Uvicorn will be found in the .venv's PATH.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]