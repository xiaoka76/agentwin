"""Filter PowerShell CLIXML noise from stderr/stdout."""
import re

CLIXML_PATTERN = re.compile(r"#< CLIXML\r?\n.*?</Objs>", re.DOTALL)
PROGRESS_PATTERN = re.compile(r"<Obj S=\"progress\".*?</Obj>", re.DOTALL)


def clean(text: str) -> str:
    """Remove CLIXML blocks, progress records, and empty lines from text."""
    if not text:
        return text
    text = CLIXML_PATTERN.sub("", text)
    text = PROGRESS_PATTERN.sub("", text)
    # Remove pure empty/whitespace-only lines to save output budget
    lines = [line for line in text.split("\n") if line.strip()]
    return "\n".join(lines)
