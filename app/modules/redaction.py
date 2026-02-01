from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Configure NLP Engine to use small model (faster install)
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

# Initialize engines
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
anonymizer = AnonymizerEngine()

class RedactionResult:
    def __init__(self, text: str, items: dict, mapping: dict):
        self.text = text
        self.items = items # {entity_type: count}
        self.mapping = mapping # {token: original_value}

import re

# Regex for UUIDs (common source of false positives)
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
# Regex for MongoDB ObjectIDs or simple Hashes (24 hex chars)
HASH_PATTERN = re.compile(r'^[0-9a-f]{24,}$', re.IGNORECASE)

def redact_text(text: str) -> RedactionResult:
    # 0. Safeguard: Ignore machine IDs
    if len(text) > 20: 
        if UUID_PATTERN.match(text) or HASH_PATTERN.match(text):
             # It's an ID, not a sentence. Skip.
             return RedactionResult(text, {}, {})

    # 1. Analyze
    results = analyzer.analyze(text=text, language='en')
    
    # 2. Count entities and Build Mapping
    entity_counts = {}
    mapping = {}
    
    # We need to sort results by start index in reverse to replace without messing up indices
    sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
    
    # Manual replacement to build mapping (Presidio Deanonymize is complex, manual is robust for simple cases)
    # We will use simple sequential tokens: [PERSON_1], [EMAIL_1]
    
    working_text = text
    type_counters = {} # {PERSON: 1, EMAIL: 1}
    
    final_items = {} # For Audit log

    for res in sorted_results:
        entity_type = res.entity_type
        original_value = text[res.start:res.end]
        
        # Update counters
        type_counters[entity_type] = type_counters.get(entity_type, 0) + 1
        count = type_counters[entity_type]
        
        # Create Token
        token = f"[{entity_type}_{count}]"
        
        # Store Mapping
        mapping[token] = original_value
        
        # Replace in text (string slicing)
        working_text = working_text[:res.start] + token + working_text[res.end:]
        
        # Update Audit Counts
        final_items[entity_type] = final_items.get(entity_type, 0) + 1

    return RedactionResult(working_text, final_items, mapping)

def deanonymize_text(text: str, mapping: dict) -> str:
    """
    Restores the original values in the LLM response.
    """
    working_text = text
    for token, original_value in mapping.items():
        working_text = working_text.replace(token, original_value)
    return working_text
