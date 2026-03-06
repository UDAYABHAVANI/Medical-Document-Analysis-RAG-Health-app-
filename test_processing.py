from services.pdf_parser import extract_pdf_text
from services.chunker import chunk_text
import os

pdf_path = "uploads\pdf\Group-Fitness-Descriptions-updated-1.26.24-1.pdf"

if os.path.exists(pdf_path):
    # 1. Extract the text page by page
    pages = extract_pdf_text(pdf_path)

    all_chunks = []

    # 2. Process each page into chunks
    for page in pages:
        chunks = chunk_text(page["text"])
        for c in chunks:
            all_chunks.append({
                "text": c,
                "page": page["page"]
            })

    # 3. Print the first 3 chunks to see the result
    print(f"Total chunks created: {len(all_chunks)}")
    for i in range(min(3, len(all_chunks))):
        print(f"\n--- Chunk {i+1} (from Page {all_chunks[i]['page']}) ---")
        print(all_chunks[i]['text'])
else:
    print("Error: PDF file not found.")
