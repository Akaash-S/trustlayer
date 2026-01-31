import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMProxyError(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException, httpx.RemoteProtocolError)),
)
async def call_llm(prompt: str) -> str:
    """
    Forwards the sanitized prompt to the LLM.
    Supports retries and proper error handling.
    """
    # 1. Fallback for "Mock" or "Hackathon" keys
    if settings.OPENAI_API_KEY.startswith("sk-mock"):
        logger.info("Using Mock LLM Response")
        return f"[MOCK] Processed Safe Content: {prompt[:50]}..."

    # 2. Real Production Call
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 401:
                logger.error("Authentication failed with LLM provider")
                raise LLMProxyError("Invalid API Key configured.")
            
            response.raise_for_status()
            
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected response format: {data}")
                return "Error: Unexpected response from LLM provider."

    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API Error: {e.response.text}")
        raise LLMProxyError(f"Upstream Provider Error: {e.response.status_code}")
    except Exception as e:
        logger.exception("Critical error during LLM call")
        raise LLMProxyError(f"Internal Proxy Error: {str(e)}")
