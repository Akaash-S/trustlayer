# Standalone Test for Stream Modifier Logic
# (No mitmproxy dependency required)

class MockProxy:
    def __init__(self):
        # Sample mapping: We want to turn [PERSON_1] back into Sachin
        self.mappings = {"flow_123": {"[PERSON_1]": "Sachin"}}

    # THE EXACT LOGIC FROM proxy_addon.py
    def make_stream_modifier(self, flow_id):
        # Closure to capture the flow_id
        # chunk is bytes (NOT iterable of bytes)
        def modifier(chunk):
            # Simulate pop (we use get for repeated testing, usually it's pop)
            mapping = self.mappings.get(flow_id, {}) 
            
            try:
                # Attempt decode (ignore errors for partial bytes)
                text = chunk.decode("utf-8", "ignore")
                
                modified = False
                for safe, real in mapping.items():
                    if safe in text:
                        text = text.replace(safe, real)
                        modified = True
                
                if modified:
                    print(f"   ✨ Replaced text: '{text}'")
                
                # Note: This yields a generator. Mitmproxy iterates it.
                yield text.encode("utf-8")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                yield chunk # Fallback (Return original bytes)
        return modifier

print("🧪 TESTING STREAM MODIFIER (Local Simulation)")
print("===========================================")

proxy = MockProxy()
modifier = proxy.make_stream_modifier("flow_123")

# Test Case 1: Normal Text requiring Replacement
print("\n1. Testing: 'Hello my name is [PERSON_1]'")
input_chunk = b"Hello my name is [PERSON_1]"
# The modifier returns a generator, we need to iterate it (like mitmproxy does)
output_gen = modifier(input_chunk)
output = next(output_gen)

print(f"   Input bytes: {input_chunk}")
print(f"   Output bytes: {output}")

if output == b"Hello my name is Sachin":
    print("✅ TEST PASSED: Replacement worked!")
else:
    print("❌ TEST FAILED: Replacement incorrect.")

# Test Case 2: Partial/Binary-like data (Should just pass through)
print("\n2. Testing: Simple text 'Hello'")
input_chunk = b"Hello"
output = next(modifier(input_chunk))
print(f"   Output bytes: {output}")

if output == b"Hello":
    print("✅ TEST PASSED: Passthrough worked!")
