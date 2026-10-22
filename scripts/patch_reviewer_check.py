from pathlib import Path

POINTS_FILE = Path("msk_therapy_os/points.py")
text = POINTS_FILE.read_text(encoding="utf-8")

old_check = """        if rev.lower() in ("ai", "system", "automated", "unknown", "none"):
            raise ValueError(f"Reviewer '{rev}' is invalid. Human clinical governance requires qualified practitioner review, not automated systems.")"""

new_check = """        rev_words = set(rev.lower().replace('-', ' ').replace('_', ' ').split())
        invalid_tokens = {'ai', 'system', 'automated', 'unknown', 'none', 'bot', 'algorithm', 'gpt', 'llm'}
        if rev_words & invalid_tokens or rev.lower() in invalid_tokens:
            raise ValueError(f"Reviewer '{rev}' is invalid. Human clinical governance requires qualified practitioner review, not automated systems.")"""

assert old_check in text, "old_check not found"
text = text.replace(old_check, new_check, 1)
POINTS_FILE.write_text(text, encoding="utf-8")
print("Updated reviewer validation successfully!")
