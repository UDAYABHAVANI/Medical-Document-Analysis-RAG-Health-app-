from database.db import get_db
import pyodbc
from flask import current_app


def save_qa_history(user_id, question, answer, confidence, source):
    """Saves the question and Phi-3's answer to SQL Server."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 1. Insert Question and get the ID
        cursor.execute(
            "INSERT INTO questions (user_id, question_text) OUTPUT INSERTED.id VALUES (?, ?)",
            (user_id, question)
        )
        question_id = cursor.fetchone()[0]

        # 2. Insert Answer linked to that Question
        # 2. Insert Answer linked to that Question
        cursor.execute(
            """INSERT INTO answers 
           (question_id, answer_text, confidence, confidence_score, source_info, is_correct, is_verified) 
           VALUES (?, ?, ?, ?, ?, 0, 0)""",
            (question_id, answer, confidence, confidence, source)
        )
        conn.commit()
        print("✔ Q&A saved to SQL Server.")
    except Exception as e:
        print(f"❌ Database Error: {e}")
        conn.rollback()

# Add this to the bottom of services/history_service.py


# In services/history_service.py

def get_dashboard_data(user_id):
    # 1. SETUP CONNECTION
    conn_str = (
        "Driver={SQL Server};"
        "Server=.;"
        "Database=healthapp_db;"
        "Trusted_Connection=yes;"
    )

    stats = {'total_questions': 0, 'total_docs': 0}
    recent_activity = []

    print(f"DEBUG: Fetching dashboard data for User ID: {user_id}")

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # 2. GET TOTAL QUESTIONS
        cursor.execute(
            "SELECT COUNT(*) FROM questions WHERE user_id = ?", (user_id,))
        stats['total_questions'] = cursor.fetchone()[0]

        # 3. GET TOTAL DOCUMENTS
        # FIX: Changed 'a.source_doc' to 'a.source_info'
        cursor.execute("""
            SELECT COUNT(DISTINCT a.source_info) 
            FROM questions q 
            JOIN answers a ON q.id = a.question_id 
            WHERE q.user_id = ?
        """, (user_id,))
        stats['total_docs'] = cursor.fetchone()[0]

        # 4. GET RECENT ACTIVITY
        # FIX: Changed 'confidence' to 'confidence_score' (based on your history code)
        # FIX: Changed 'timestamp' back to 'asked_at' for the SQL selection
        query = """
            SELECT TOP 5 
                q.asked_at, 
                q.question_text, 
                a.confidence_score, 
                a.is_correct
            FROM questions q
            JOIN answers a ON q.id = a.question_id
            WHERE q.user_id = ?
            ORDER BY q.asked_at DESC
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()

        for row in rows:
            recent_activity.append({
                'timestamp': row[0],
                'question_text': row[1],
                'confidence_score': row[2],
                'is_correct': row[3]
            })

        conn.close()

    except Exception as e:
        print(f"❌ DASHBOARD ERROR: {e}")
        return 0, 0, []

    return stats['total_questions'], stats['total_docs'], recent_activity
