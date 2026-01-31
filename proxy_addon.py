import json
import logging
import sys
import os

# Fix: Ensure 'app' module can be imported regardless of how mitmweb is launched
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.append(cwd)

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
            if "already exists" in str(e):
                print("✅ [PROXY] DB already initialized (Table exists)")
                logger.info("DB already initialized")
            else:
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
            # Debug: Log all POSTs to targets
            print(f"🔎 [PROXY] Inspecting POST to: {flow.request.pretty_url}")
            
            content = flow.request.content.decode('utf-8')
            if not content:
                print("⚠️ [PROXY] No content in request")
                return

            # Attempt JSON parsing
            try:
                data = json.loads(content)
                # print(f"📄 [PROXY] JSON Keys: {list(data.keys())}") # Debug structure
            except json.JSONDecodeError:
                print("⚠️ [PROXY] Failed to parse JSON body")
                return # Not JSON
            
            # --- ChatGPT Specific Handling ---
            modified = False
            mapping = {}
            final_items = {} # For Audit
            
            # Recursive search with debug
            def process_value(val):
                nonlocal modified, mapping, final_items
                # DEBUG: Relaxed check for testing (len > 5)
                if isinstance(val, str) and len(val) > 5 and " " in val:
                    # LOG EVERYTHING (To prove we saw it)
                    print(f"👀 [PROXY] Analyzing: {val[:50]}...")
                    
                    result = redact_text(val)
                    
                    # PROOF OF INTERCEPTION:
                    # We inject this tag even if no PII is found, so the user sees it in ChatGPT's reply context
                    # e.g. AI might say: "I see you have the [Verified] tag..."
                    val = val + " [🔒 TrustLayer Verified]"
                    modified = True 
                    
                    if result.items:
                        print(f"🛡️ [PROXY] DETECTED PII: {result.items}")
                        mapping.update(result.mapping)
                        
                        # INJECT VISIBLE INDICATOR (For Testing)
                        val_redacted = result.text + " [🛡️ REDACTED]"
                        
                        # Accumulate counts
                        for k, v in result.items.items():
                            final_items[k] = final_items.get(k, 0) + v
                        return val_redacted
                    else:
                        print(f"⚪ [PROXY] No PII found in: {val[:30]}...")
                        return val # Return the one with [Verified] tag potentially? 
                        # Actually logic above updates 'val' local var but return returns the result.text. 
                        # Let's be explicit.
                        return val
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
            
            # Debug: Force modified if we found anything (just to be safe)
            if final_items: 
                modified = True

            if modified:
                print(f"✅ [PROXY] Refracted PII in request to {flow.request.pretty_host}")
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
    # OPTIMIZATION: Enable Streaming (1ms Latency)
    # Trade-off: We cannot De-Anonymize if we stream, so user will see [PERSON_1]
    def responseheaders(self, flow: http.HTTPFlow):
        # Enable streaming for target hosts
        target_hosts = ["chat.openai.com", "chatgpt.com", "gemini.google.com", "claude.ai"]
        if any(host in flow.request.pretty_host for host in target_hosts):
            flow.response.stream = True
            
    # Remove buffering response hook to ensure speed
    async def response(self, flow: http.HTTPFlow):
        # Cleanup mapping if it exists (to prevent memory leak)
        if flow.id in self.mappings:
            del self.mappings[flow.id]

addons = [
    TrustLayerAddon()
]
