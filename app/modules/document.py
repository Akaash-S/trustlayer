import tika
from tika import parser

# Initialize Tika
tika.initVM()

def extract_text(file_path: str = None, file_buffer: bytes = None) -> str:
    """
    Extract text from a file path or bytes buffer using Tika.
    """
    try:
        if file_buffer:
            parsed = parser.from_buffer(file_buffer)
        elif file_path:
            parsed = parser.from_file(file_path)
        else:
            return ""
            
        return parsed.get("content", "").strip()
    except Exception as e:
        print(f"Error parsing document: {e}")
        return ""
