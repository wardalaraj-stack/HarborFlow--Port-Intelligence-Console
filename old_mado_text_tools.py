"""Regex sanitization, stable-sequence, and incident-index functions."""
import re

##################################################
# Regex sanitization patterns and replacements  
##################################################
CONTAINER_PATTERN = r"\b[A-Za-z]{4}\d{7}\b"
SEAL_PATTERN = r"\bSEAL-\d{6}\b"
EMAIL_PATTERN = (
    r"(?<![\w._%+@-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    r"(?![\w_%+@-]|\.(?=[\w.%+@-]))"
)


def sanitize_text(text):
    result = re.sub(
        CONTAINER_PATTERN, "[CONTAINER]", text, flags=re.IGNORECASE
    )
    result = re.sub(
        SEAL_PATTERN, "[SEAL]", result, flags=re.IGNORECASE
    )
    result = re.sub(EMAIL_PATTERN, "[EMAIL]", result)

    return result, result != text

##################################################
# Regex end
##################################################

# Task 9 - Search Incident Reports | Implemented by Mado Sallom
def normalize_words(text):
    """Convert text into lowercase words without punctuation."""
    return re.findall(r"\w+", text.lower())
