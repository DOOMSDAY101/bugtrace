def safe_text(text: str) -> str:
    if not text:
        return ""
    return text.encode("utf-8", "ignore").decode("utf-8")