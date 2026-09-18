# core_api/app/services/pii_scrubber.py
import re

PATTERNS = [
    re.compile(r"\b\d{12,19}\b"),                      # card/account numbers
    re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),   # IBAN-like
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),               # SSN-like
]

def scrub_pii(text: str) -> str:
    """Removes PII patterns BEFORE any persistence or ML processing."""
    cleaned = text
    for pattern in PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    return cleaned

def normalize_description(text: str) -> str:
    text = scrub_pii(text)
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text