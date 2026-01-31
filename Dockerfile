# Use official Python runtime
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Helper to prevent Tika from querying external networks for the JAR if possible, 
    # though usually it needs to download it once. 
    TIKA_LOG_PATH='/var/log/tika'

# Install system dependencies (Java is required for Tika)
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model during build so it's cached
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Expose ports: 8000 (FastAPI), 8501 (Streamlit)
EXPOSE 8000 8501

# Create a startup script to run both services
RUN echo "#!/bin/bash\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000 & \n\
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 & \n\
wait -n\n\
exit $?" > /app/start.sh && chmod +x /app/start.sh

# Start command
CMD ["/app/start.sh"]
