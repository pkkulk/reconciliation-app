import re
import pandas as pd
def extract_partner_pin(description: str) -> str:
    """
    Extracts the 11-digit partner pin from the end of the description string.
    Returns None if not found.
    """
    match_xxp = re.search(r'XXP(\d{8})', str(description))
    if match_xxp:
        return match_xxp.group(1)
    matches_end = re.findall(r'(\d{8,12})\s*$', str(description))
    if matches_end:
        return matches_end[-1] 
    return None
