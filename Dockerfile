FROM python:3.12-slim

# Create app directory
WORKDIR /app

# Install system deps needed for git and build tools
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       git \
       build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Expose port used by Spaces (and defaults used by app.py)
ENV PORT=7860
EXPOSE 7860

# Default command runs the FastAPI app with uvicorn and uses the PORT env var
# Use shell form so ${PORT:-7860} is expanded; remove --reload for production.
CMD ["sh", "-c", "exec uvicorn src.fastapi_app:app --host 0.0.0.0 --port ${PORT:-7860}"]
