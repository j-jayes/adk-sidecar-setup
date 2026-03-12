FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY lease_reviewer/ ./lease_reviewer/

# Install dependencies with uv
RUN uv sync --no-dev

# Expose ADK API server port
EXPOSE 8000

# Run the ADK API server pointing at /app (discovers lease_reviewer module)
CMD ["uv", "run", "adk", "api_server", "--host", "0.0.0.0", "--port", "8000", "/app"]
