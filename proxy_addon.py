import json
import logging
from mitmproxy import http
from app.modules.redaction import redact_text, deanonymize_text

# Configure simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustLayerProxy")

import asyncio
from app.modules.audit import create_audit_log
from app.core.database import get_db, init_db, SessionLocal
import uuid

class TrustLayerAddon:
    def __init__(self):
        self.mappings = {} # {flow_id: mapping_dict}
        logger.info("🛡️ TrustLayer DLP Proxy Active")
        
    def load(self, loader):
        # We need to initialize the DB. 
        # Since load is sync, we schedule it.
        asyncio.create_task(self._init_db_safe())

    async def _init_db_safe(self):
        try:
            await init_db()
            print("✅ [PROXY] DB Initialized")
            logger.info("DB Initialized for Proxy")
            
            # Create a "Startup" log event so we verify DB is writable
            async with SessionLocal() as db:
                 print("🔄 [PROXY] Attempting to write startup log...")
                 await create_audit_log(db, "SYSTEM_STARTUP", 1, "INIT")
                 print("✅ [PROXY] Startup log written to DB")
                 logger.info("Startup log written to DB")
                 
        except Exception as e:
            print(f"❌ [PROXY] DB Init failed: {e}")
            logger.error(f"DB Init failed: {e}")

    # Make request async to support DB calls
    async def request(self, flow: http.HTTPFlow):
        # Filter for AI Sites (Basic list)
        target_hosts = ["chat.openai.com", "chatgpt.com", "gemini.google.com", "claude.ai"]
        if not any(host in flow.request.pretty_host for host in target_hosts):
            return

        # Only check POST/PUT (Sending data)
        if flow.request.method not in ["POST", "PUT"]:
            return
            
        try:
            content = flow.request.content.decode('utf-8')
            if not content:
                return

            # Attempt JSON parsing
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                return # Not JSON
            
            # --- ChatGPT Specific Handling ---
            modified = False
            mapping = {}
            final_items = {} # For Audit
            
            # Recursive search for strings to redact (Simplified)
            def process_value(val):
                nonlocal modified, mapping, final_items
                if isinstance(val, str) and len(val) > 5:
                    result = redact_text(val)
                    if result.items:
                        modified = True
                        mapping.update(result.mapping)
                        # Accumulate counts
                        for k, v in result.items.items():
                            final_items[k] = final_items.get(k, 0) + v
                        return result.text
                return val

            # Deep traverse
            def traverse(obj):
                if isinstance(obj, dict):
                    return {k: traverse(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [traverse(elem) for elem in obj]
                else:
                    return process_value(obj)

            new_data = traverse(data)

            if modified:
                logger.info(f"Refracted PII in request to {flow.request.pretty_host}")
                flow.request.content = json.dumps(new_data).encode('utf-8')
                # Store mapping for the response
                self.mappings[flow.id] = mapping
                
                # Visual Indicator in Header
                flow.request.headers["X-TrustLayer-Status"] = "Sanitized"
                
                # --- AUDIT LOGGING ---
                try:
                    # Create a new session for this log
                    async with SessionLocal() as db:
                         request_id = str(uuid.uuid4())
                         for entity_type, count in final_items.items():
                             await create_audit_log(db, entity_type, count, request_id)
                             logger.info(f"Logged {count} {entity_type}")
                except Exception as e:
                    logger.error(f"Audit log failed: {e}")


        except Exception as e:
            logger.error(f"Error processing request: {e}")

    # Make response async too (good practice if request is async)
    async def response(self, flow: http.HTTPFlow):
        # Check if we have a mapping for this flow (meaning we redacted something)
        if flow.id in self.mappings:
            mapping = self.mappings[flow.id]
            try:
                if not flow.response.content:
                    return
                    
                content = flow.response.content.decode('utf-8')
                
                # De-Anonymize
                restored_content = deanonymize_text(content, mapping)
                
                if content != restored_content:
                    logger.info("Restored PII in response")
                    flow.response.content = restored_content.encode('utf-8')
                    
                del self.mappings[flow.id]
                
            except Exception as e:
                logger.error(f"Error processing response: {e}")

addons = [
    TrustLayerAddon()
]
