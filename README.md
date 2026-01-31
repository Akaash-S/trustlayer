# TrustLayer AI

A secure AI Governance Gateway acting as a proxy between enterprise users and LLMs to prevent data leakage.

## Features
- **PII Redaction:** Automatically detects and masks sensitive data (Person, Email, Phone) using Microsoft Presidio.
- **Document Support:** parsing of PDF, Excel, and Word files via Apache Tika.
- **Audit Logging:** SQLite-backed audit trails of redacted entities.
- **Dashboard:** Streamlit-based visualization of governance metrics.
- **LLM Proxy:** Forwards sanitized prompts to LLM (mocked or real).

## Setup

1.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_lg
    ```

## Running the Application

### 1. Start the FastAPI Gateway
```bash
uvicorn app.main:app --reload
```
API will be available at `http://localhost:8000`.
Docs at `http://localhost:8000/docs`.

### 2. Start the Dashboard
```bash
streamlit run dashboard.py
```
Dashboard will open in your browser.

## Testing

You can send a POST request to the gateway:

**Using curl:**
```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "prompt=My name is Alice and my email is alice@example.com"
```

**Using Python:**
```python
import requests
resp = requests.post("http://localhost:8000/v1/chat/completions", data={"prompt": "Call me at 555-1234"})
print(resp.json())
```
