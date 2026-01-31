import httpx
from app.core.config import settings

async def call_llm(prompt: str) -> str:
    """
    Forwards the sanitized prompt to the LLM.
    If API key is mock, returns a dummy response.
    """
    if settings.OPENAI_API_KEY.startswith("sk-mock"):
        return f"Denied/Processed: This is a mocked response. Your safe input was: {prompt[:50]}..."
    
    # Real call to OpenAI (Example)
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
