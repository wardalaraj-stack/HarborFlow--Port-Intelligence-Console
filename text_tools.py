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

##################################################
# Task 7 - Longest stable event sequence
##################################################

def longest_stable_sequence(events):
    last_seen = {}
    left = 0
    best_start = 0
    best_length = 0

    for right, event in enumerate(events):
        #right is basicly the inhdex of each event "counter"
        if event in last_seen and last_seen[event] >= left:
            left = last_seen[event] + 1

        last_seen[event] = right

        # Update the longest stable sequence if the current one is longer
        current_length = right - left + 1

        if current_length > best_length:
            best_length = current_length
            best_start = left

    return best_length, events[best_start:best_start + best_length]


# Task 9: Search incident reports (integrated from the existing team branch)
def normalize_words(text):
    """Convert text into lowercase words without punctuation."""
    return re.findall(r"\w+", text.lower())
