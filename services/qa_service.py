from services.chroma_service import search_documents
from llm.ollama_client import generate_answer
from services.embedding_service import generate_embedding
from services.chroma_service import add_document
import uuid
from services.chroma_service import search_documents

from llm.ollama_client import generate_answer


def index_pdf_chunks(chunks, document_name):
    """
    Takes the chunks we created on Week 2, Day 5, and
    stores them in our new Vector Database.
    """
    for chunk in chunks:
        # Generate the numerical representation
        emb = generate_embedding(chunk["text"])
        chunk_id = str(uuid.uuid4())

        # Store with metadata (document name and page number)
        add_document(
            chunk_id,
            emb,
            chunk["text"],
            {
                "document": document_name,
                "page": chunk["page"]
            }
        )
    print(f"Successfully indexed {len(chunks)} chunks from {document_name}!")

# --- Part 2: Question Retrieval and Answering logic ---


def answer_question(question):
    """
    Retrieves context, filters out 'junk' pages, and generates an answer.
    """
    # 1. Convert question to embedding
    query_emb = generate_embedding(question)

    # 2. INCREASED top_k to 6 (Catch more options to filter from)
    results = search_documents(query_emb, top_k=5)

    raw_docs = results["documents"][0]
    raw_metas = results["metadatas"][0]
    raw_dists = results["distances"][0]

    # 3. THE JUNK FILTER
    ignored_phrases = [
        "learning objectives",
        "at the end of this chapter",
        "table of contents",
        "key terms",
        "chapter outline",
        "glossary"
        "references",       # <--- NEW
        "bibliography",     # <--- NEW
        "citations",        # <--- NEW
        "works cited",      # <--- NEW
        "suggested reading"  # <--- NEW
        "retrieved from",   # Catches web citations
        "http",             # Catches URLs
        "https",            # Catches URLs
        "doi.org",          # Catches scientific paper links
        "vol.",             # Catches journal volume numbers
    ]

    valid_docs = []
    valid_metas = []
    valid_dists = []

    # Loop through and pick only "clean" text
    for i, doc_text in enumerate(raw_docs):
        if any(bad_phrase in doc_text.lower() for bad_phrase in ignored_phrases):
            continue  # Skip junk!

        valid_docs.append(doc_text)
        valid_metas.append(raw_metas[i])
        valid_dists.append(raw_dists[i])

        if len(valid_docs) >= 3:
            break

    # Fallback if everything was filtered
    if not valid_docs and raw_docs:
        valid_docs = [raw_docs[0]]
        valid_metas = [raw_metas[0]]
        valid_dists = [raw_dists[0]]

    # 4. Construct Context
    context = "\n---\n".join(valid_docs)

    # 5. Generate Answer
    answer = generate_answer(context, question)

    # 6. CALCULATE CONFIDENCE (Matches your old code)
    # Get the best distance from our VALID list
    best_dist = valid_dists[0] if valid_dists else 0.5

    # Do the math here so app.py doesn't have to
    confidence = round((1 - float(best_dist)) * 100, 1)

    # Return the exact same 3 items your app expects
    return answer, valid_metas, confidence
