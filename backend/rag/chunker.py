def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end].strip())
        if end == length:
            break
        start = end - overlap
    return [c for c in chunks if c]
