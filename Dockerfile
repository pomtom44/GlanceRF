# GlanceRF - Docker image (headless server mode)
# Uses same source as Windows/Mac/Linux installers
# Build: docker build -t glancerf .
# Run:   docker run -p 8080:8080 -p 8081:8081 glancerf

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies (headless Linux - no GUI)
COPY requirements/requirements-linux.txt .
RUN pip install --no-cache-dir -r requirements-linux.txt

# Copy application code
COPY run.py .
COPY glancerf/ ./glancerf/
COPY logos/ ./logos/

# Server-only mode for Docker (no browser, no desktop window)
# desktop_mode is forced to headless via run.py when this is set
ENV GLANCERF_DOCKER=1

EXPOSE 8080 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('GLANCERF_PORT', '8080') + '/api/time', timeout=3)" || exit 1

CMD ["python", "run.py"]
