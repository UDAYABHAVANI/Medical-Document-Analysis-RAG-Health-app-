import pandas as pd


def extract_questions(file_path):
    """
    Reads an Excel file and extracts questions from the first column.
    Forces all data to strings to prevent 'float' errors in the UI.
    """
    try:
        # 1. Read the Excel file
        df = pd.read_excel(file_path)

        # 2. Check if the file is empty
        if df.empty:
            return []

        # 3. Target the first column and force it to be STRING type
        # .astype(str) turns NaN (floats) into the literal text "nan"
        questions_raw = df.iloc[:, 0].astype(str).tolist()

        # 4. Clean the list:
        # - Remove rows that are the text 'nan' (from empty Excel cells)
        # - Remove rows that are just empty strings or whitespace
        questions = [
            q.strip() for q in questions_raw
            if q.lower() != 'nan' and q.strip() != ''
        ]

        return questions

    except Exception as e:
        print(f"❌ Error extracting Excel: {e}")
        return []
