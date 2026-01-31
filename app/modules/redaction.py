from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Initialize engines
# Note: Ensure spacy model is downloaded: python -m spacy download en_core_web_lg
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

class RedactionResult:
    def __init__(self, text: str, items: dict):
        self.text = text
        self.items = items # {entity_type: count}

def redact_text(text: str) -> RedactionResult:
    # 1. Analyze
    results = analyzer.analyze(text=text, language='en')
    
    # 2. Count entities for Audit
    entity_counts = {}
    for res in results:
        entity_counts[res.entity_type] = entity_counts.get(res.entity_type, 0) + 1

    # 3. Anonymize
    # We want to replace with [ENTITY_TYPE]
    operators = {
        "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
        "DEFAULT": OperatorConfig("replace", {"new_value": "[PII]"}),
    }
    
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators
    )

    return RedactionResult(anonymized_result.text, entity_counts)
