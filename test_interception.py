import json
from app.modules.redaction import redact_text

# Mock of the logic inside proxy_addon.py
def process_message(val):
    print(f"\n--- Testing Input: '{val}' ---")
    
    # EXACT LOGIC COPIED FROM proxy_addon.py
    if isinstance(val, str) and len(val) > 1:
        print(f"👀 [PROXY] Analyzing: {val}...")
        
        result = redact_text(val)
        
        # PROOF OF INTERCEPTION TAG
        val = val + " [🔒 TrustLayer Verified]"
        
        if result.items:
            print(f"🛡️ [PROXY] DETECTED PII: {result.items}")
            val_redacted = result.text + " [🛡️ REDACTED]"
            return val_redacted
        else:
            print(f"⚪ [PROXY] No PII found.")
            return val
    else:
        print("⏭️ Skipped (Too short)")
        return val

# Test Cases
print("🧪 RUNNING LOCAL LOGIC TEST")
print("===========================")

# Case 1: Simple Hello (Should get verified tag)
output1 = process_message("Hello")
print(f"✅ OUTPUT 1: {output1}")

# Case 2: PII (Should get PII redacted + tag?? Wait, logic returns early)
# Actually, looking at code: if PII found, it returns val_redacted. If NOT, it returns val (which has the tag).
output2 = process_message("My name is John Doe")
print(f"✅ OUTPUT 2: {output2}")
