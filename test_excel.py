from services.excel_parser import extract_questions
import os

# Use the exact path to the Excel file in your sidebar
excel_path = "uploads/excel/Questions.xlsx"

if os.path.exists(excel_path):
    print("Excel file found! Extracting questions...")
    questions = extract_questions(excel_path)

    print(f"\nFound {len(questions)} questions:")
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")
else:
    print(f"Error: Could not find the file at {excel_path}")
