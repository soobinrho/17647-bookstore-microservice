# Reference: https://docs.astral.sh/uv/guides/integration/fastapi/#deployment
FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# Run the application.
# -u is required to force the stdout and stderr to be unbuffered.
# Source:
#   https://stackoverflow.com/a/29745541
ENTRYPOINT [".venv/bin/python", "-u", "app/main.py"]
