import ollama


def generate_answer(context, question):
    """
    Sends the retrieved medical context and question to TinyLlama.
    Refined for better accuracy with small parameter models.
    """
    response = ollama.chat(
        model='tinyllama',
        messages=[
            {
                'role': 'system',
                'content': (
                    "You are a professional Medical Assistant. Use the provided Context to "
                    "answer the Question accurately. If the Question asks for a definition, "
                    "provide the exact definition from the text. If the answer is not in "
                    "the Context, say 'I cannot find this in the medical records.' "
                    "Be concise and do not hallucinate."
                )
            },
            {
                'role': 'user',
                'content': f"CONTEXT FROM PDF:\n{context}\n\nUSER QUESTION: {question}"
            }
        ]
    )
    return response['message']['content'].strip()
