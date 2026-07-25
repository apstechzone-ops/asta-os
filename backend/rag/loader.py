from pathlib import Path


def load_text(source_path: str) -> str:
    path = Path(source_path)
    suffix = path.suffix.lower()

    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    raise ValueError(f"Unsupported document type: {suffix}")
