def chunk_text(text, chunk_size=250, overlap=60):
    """
    Splits text into chunks of 500 characters with 100 characters of overlap.
    """
    chunks = []
    start = 0
    # Remove extra whitespace and newlines for cleaner data
    clean_text = " ".join(text.split())

    while start < len(clean_text):
        end = start + chunk_size
        chunk = clean_text[start:end]
        chunks.append(chunk)
        start = end - overlap  # Slide back a bit for context

    return chunks
