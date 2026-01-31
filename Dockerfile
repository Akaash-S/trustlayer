# Use official Python runtime
# python:3.10-slim is currently Debian Bookworm, but works for Trixie too if specified
FROM python:3.10-slim

# Prevent Python from writing pyc files and allow stdout logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tika configuration
    TIKA_LOG_PATH='/var/log/tika'

# Install system dependencies
# Fix: Explicitly install OpenJDK 17 for Tika. 
# Added 'ant' and 'ca-certificates-java' to ensure keystores are generated correctly.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    ca-certificates-java \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Verify Java installation
RUN java -version

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Fix: Download spaCy model during build
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8501

# Start script
# Fix: Using 'app.main:app' because the file is located at /app/app/main.py inside container
# (WORKDIR is /app, and we copied local 'app' folder into it)
RUN echo "#!/bin/bash\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000 & \n\
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 & \n\
wait -n\n\
exit $?" > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
