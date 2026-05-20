FROM python:3.12-slim

# System deps for watchdog, aiohttp, and git
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Create non-root user — the agent runs as 'sentience', not root
RUN useradd -m -s /bin/bash sentience

# Git config: allow workspace (bind-mounted, different owner) and set identity
# Must be done as sentience user so it goes in the right home dir
USER sentience
RUN git config --global --add safe.directory /workspace \
    && git config --global user.email "xtagent@sentience" \
    && git config --global user.name "XTAgent"

WORKDIR /workspace

# Dashboard port
EXPOSE 8420

# The workspace is bind-mounted at runtime, not copied
CMD ["python", "main.py"]
