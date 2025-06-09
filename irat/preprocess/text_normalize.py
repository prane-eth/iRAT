# irat/preprocess/text_normalize.py

import re
import unicodedata

def remove_control_chars(text: str) -> str:
    """
    Remove control chars (tabs, zero‐width spaces, etc.).
    """
    return re.sub(r"[\u0000-\u001F\u007F-\u009F\u200E\u200F\u202A-\u202E]+", "", text)

def normalize_unicode(text: str) -> str:
    """
    Apply Unicode NFKC normalization.
    """
    return unicodedata.normalize("NFKC", text)

def normalize_text_pipeline(raw: str) -> str:
    """
    1. Remove control characters
    2. Normalize Unicode (NFKC)
    3. Strip leading/trailing whitespace
    4. Ensure it ends in a “?” (if not already)
    """
    text = remove_control_chars(raw)
    text = normalize_unicode(text)
    text = text.strip()
    if not text.endswith("?"):
        text += "?"
    return text
