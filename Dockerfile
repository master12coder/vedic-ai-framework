FROM python:3.12-slim

WORKDIR /app

# Install build dependencies for pyswisseph
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy package definitions first (layer caching)
COPY engine/pyproject.toml engine/pyproject.toml
COPY products/pyproject.toml products/pyproject.toml
COPY apps/pyproject.toml apps/pyproject.toml

# Copy source code
COPY engine/ engine/
COPY products/ products/
COPY apps/ apps/

# Install all packages
RUN pip install --no-cache-dir -e engine/ -e products/ -e "apps/[telegram]"

# Create data directories
RUN mkdir -p data charts

# Default: CLI help
ENTRYPOINT ["python", "-m", "jyotish_app.cli.main"]
CMD ["--help"]
