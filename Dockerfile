FROM python:3.12-slim

# System deps for watchdog and aiohttp
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Create non-root user — the agent runs as 'sentience', not root
RUN useradd -m -s /bin/bash sentience
USER sentience

WORKDIR /workspace

# Dashboard port
EXPOSE 8420

# The workspace is bind-mounted at runtime, not copied
CMD ["python", "main.py"]
