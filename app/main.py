import uuid
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import init_db, get_db
from app.modules.redaction import redact_text
from app.modules.document import extract_text
from app.modules.audit import create_audit_log
from app.services.llm_proxy import call_llm

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Security: Disable CORS for Hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/v1/chat/completions")
async def chat_completions(
    prompt: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Secure endpoint that accepts a text prompt OR a file.
    It extracts text, redacts PII, logs the audit, and forwards to LLM.
    """
    request_id = str(uuid.uuid4())
    
    # 1. Input Handling
    raw_text = ""
    if file:
        file_content = await file.read()
        raw_text = extract_text(file_buffer=file_content)
    elif prompt:
        raw_text = prompt
    else:
        raise HTTPException(status_code=400, detail="No prompt or file provided")

    if not raw_text:
        raise HTTPException(status_code=400, detail="Could not extract text from input")

    # 2. Redaction
    redaction_result = redact_text(raw_text)
    sanitized_text = redaction_result.text
    
    # 3. Audit Logging (Async)
    for entity_type, count in redaction_result.items.items():
        await create_audit_log(db, entity_type, count, request_id)
    
    # 4. Forward to LLM
    llm_response = await call_llm(sanitized_text)
    
    return {
        "request_id": request_id,
        "original_length": len(raw_text),
        "sanitized_length": len(sanitized_text),
        "redacted_entities": redaction_result.items,
        "llm_response": llm_response
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
