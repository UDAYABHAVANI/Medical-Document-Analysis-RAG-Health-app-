from sentence_transformers import SentenceTransformer

# This model is small and fast for local development
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(text):
    """Converts a string of text into a numerical list (embedding)."""
    return model.encode(text).tolist()
