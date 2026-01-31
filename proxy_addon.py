import json
import logging
from mitmproxy import http
from app.modules.redaction import redact_text, deanonymize_text

# Configure simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustLayerProxy")

class TrustLayerAddon:
    def __init__(self):
        self.mappings = {} # {flow_id: mapping_dict}
        logger.info("🛡️ TrustLayer DLP Proxy Active")

    def request(self, flow: http.HTTPFlow):
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
            # Structure usually: {"messages": [{"content": {"parts": ["text"]}}]}
            modified = False
            mapping = {}
            
            # Recursive search for strings to redact (Simplified for Hackathon)
            # In a real DLP, we'd traverse the whole JSON tree carefully.
            # Here we just look for common "prompt" keys or dump the whole structure if small.
            
            # Helper to redact a string value and store mapping
            def process_value(val):
                nonlocal modified, mapping
                if isinstance(val, str) and len(val) > 5:
                    result = redact_text(val)
                    if result.items:
                        modified = True
                        mapping.update(result.mapping)
                        return result.text
                return val

            # Deep traverse to find text fields
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
                
                # Visual Indicator in Header (so user knows)
                flow.request.headers["X-TrustLayer-Status"] = "Sanitized"

        except Exception as e:
            logger.error(f"Error processing request: {e}")

    def response(self, flow: http.HTTPFlow):
        # Check if we have a mapping for this flow (meaning we redacted something)
        if flow.id in self.mappings:
            mapping = self.mappings[flow.id]
            try:
                if not flow.response.content:
                    return
                    
                content = flow.response.content.decode('utf-8')
                
                # De-Anonymize the whole body text
                # (Simple string replacement is okay here since tokens are unique)
                restored_content = deanonymize_text(content, mapping)
                
                if content != restored_content:
                    logger.info("Restored PII in response")
                    flow.response.content = restored_content.encode('utf-8')
                    
                # Cleanup
                del self.mappings[flow.id]
                
            except Exception as e:
                logger.error(f"Error processing response: {e}")

addons = [
    TrustLayerAddon()
]
