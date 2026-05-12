# syntax=docker/dockerfile:1.7

# Multi-stage build for kgconvai. The final image is ~250 MB and runs the
# Gradio chat UI by default. Override CMD to use the Streamlit admin panel or
# the CLI directly.
#
# Build:  docker build -t kgconvai:latest .
# Run:    docker run --rm -p 7860:7860 kgconvai:latest
# Admin:  docker run --rm -p 8501:8501 kgconvai:latest \
#             python -m kgconvai web admin --port 8501

FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# System deps that some wheels need at install time (kept tiny)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY schemas/ ./schemas/
COPY ontology/ ./ontology/
COPY dialogue_graph/ ./dialogue_graph/

# Build a virtualenv so the runtime stage can copy it wholesale
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install ".[kg]" gradio>=4.40 streamlit>=1.36 pyvis

# ---------- runtime ----------------------------------------------------------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# Non-root user (Hugging Face Spaces convention)
RUN useradd --create-home --shell /bin/bash app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/schemas /app/schemas
COPY --from=builder /app/ontology /app/ontology
COPY --from=builder /app/dialogue_graph /app/dialogue_graph
COPY pyproject.toml README.md /app/

USER app
EXPOSE 7860
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -m kgconvai version || exit 1

CMD ["python", "-m", "kgconvai", "web", "chat", "--host", "0.0.0.0", "--port", "7860"]
