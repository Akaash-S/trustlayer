import uuid
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import init_db, get_db
from app.modules.redaction import redact_text, deanonymize_text # Updated import
from app.modules.document import extract_text
from app.modules.audit import create_audit_log
from app.services.llm_proxy import call_llm, LLMProxyError

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustLayer")

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Security: Disable CORS for Hackathon (as requested)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        # In prod, we might want to shut down, but proper retry handling is better.

@app.post("/v1/chat/completions")
async def chat_completions(
    prompt: Optional[str] = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Secure endpoint that accepts a text prompt OR a file.
    It extracts text, redacts PII, logs the audit, and forwards to LLM.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Processing Request ID: {request_id}")
    
    # 1. Input Handling
    raw_text = ""
    try:
        if file:
            logger.info(f"Processing File: {file.filename}")
            file_content = await file.read()
            raw_text = extract_text(file_buffer=file_content)
        elif prompt:
            raw_text = prompt
        else:
            raise HTTPException(status_code=400, detail="No prompt or file provided")

        if not raw_text:
            raise HTTPException(status_code=400, detail="Could not extract text from input")
    except Exception as e:
        logger.error(f"Input processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process input")

    # 2. Redaction
    try:
        redaction_result = redact_text(raw_text)
        sanitized_text = redaction_result.text
        # We hold the mapping in memory for this request
        deanonymize_map = redaction_result.mapping 
    except Exception as e:
        logger.error(f"Redaction failed: {e}")
        raise HTTPException(status_code=500, detail="Governance Policy Failure")
    
    # 3. Audit Logging (Async)
    # Note: Fire and forget task or await? Await ensures audit is committed.
    try:
        if redaction_result.items:
            logger.info(f"Redacted Entities: {redaction_result.items}")
            for entity_type, count in redaction_result.items.items():
                await create_audit_log(db, entity_type, count, request_id)
    except Exception as e:
        logger.error(f"Audit logging failed: {e}")
        # We proceed even if logs fail, but in strict secure environments we might fail closed.
        # For now, we log the error.

    # 4. Forward to LLM
    try:
        llm_response_sanitized = await call_llm(sanitized_text)
    except LLMProxyError as e:
        logger.error(f"LLM Call failed: {e}")
        raise HTTPException(status_code=502, detail=f"LLM Provider Error: {str(e)}")
        
    # 5. De-Anonymize Response (The Magic Step)
    # Restores [PERSON_1] -> John Doe in the final answer so user feels it's normal.
    final_response = deanonymize_text(llm_response_sanitized, deanonymize_map)
    
    return {
        "request_id": request_id,
        "original_length": len(raw_text),
        "sanitized_length": len(sanitized_text),
        "redacted_entities": redaction_result.items,
        "llm_response": final_response # User receives "normal" text
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
