import pdfplumber


def extract_pdf_text(file_path):
    """
    Reads a PDF file and returns a list of dictionaries 
    containing the page number and the text found on that page.
    """
    pages_content = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages_content.append({
                        "page": i + 1,
                        "text": text
                    })
        return pages_content
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return []
