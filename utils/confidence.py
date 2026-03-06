def calculate_confidence(distance_score):
    """
    ChromaDB distance to percentage.
    Lower distance = Higher confidence.
    """
    # Assuming cosine distance where 0 is identical and 1 is different
    confidence = (1 - distance_score) * 100
    return round(max(0, min(100, confidence)), 2)  # Keep it between 0-100%
