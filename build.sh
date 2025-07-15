#!/usr/bin/env bash
# exit on error
set -e

# Install Python dependencies
poetry install --no-root

# Install Playwright browser and its system dependencies
playwright install --with-deps chromium