# This looks into the services folder for your parser
from services.pdf_parser import extract_pdf_text
import os

# Use the exact path to one of the PDFs you successfully uploaded
pdf_path = "uploads/pdf/Group-Fitness-Descriptions-updated-1.26.24-1.pdf"

# Check if the file exists before trying to read it
if os.path.exists(pdf_path):
    print("File found! Starting extraction...")
    data = extract_pdf_text(pdf_path)

    for page in data:
        print(f"\n--- Content of Page {page['page']} ---")
        print(page['text'][:300])  # Shows the first 300 characters
else:
    print(f"Error: Could not find the file at {pdf_path}")
