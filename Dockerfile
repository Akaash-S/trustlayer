# Use specific Bookworm tag for stability (contains OpenJDK 17)
FROM python:3.10-slim-bookworm

# Prevent Python from writing pyc files and allow stdout logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TIKA_LOG_PATH='/var/log/tika'

# Install system dependencies
# OpenJDK 17 is the standard LTS that works well with Tika
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    ca-certificates-java \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Fix: REMOVED 'python -m spacy download ...'
# The model is installed via requirements.txt directly. 
# Running the download command again causes 404 errors as seen in logs.

# Helper: Pre-download Tika JAR to ensure it works offline/fast
RUN python -c "import tika; tika.initVM()"

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8501

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
