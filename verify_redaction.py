from app.modules.redaction import redact_text

text = "My name is John Doe and my email is john.doe@example.com. Call me at 555-0199."
print(f"Original: {text}")

result = redact_text(text)
print(f"Redacted: {result.text}")
print(f"Entities: {result.items}")

expected_tokens = ["[PERSON]", "[EMAIL]", "[PHONE]"]
if all(token in result.text for token in expected_tokens):
    print("SUCCESS: All entities redacted.")
else:
    print("FAILURE: Some entities missed.")
