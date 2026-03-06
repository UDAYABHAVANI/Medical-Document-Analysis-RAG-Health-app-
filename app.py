import os
import time
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for
import pyodbc
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import Config
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime

# Service Imports
from services.pdf_parser import extract_pdf_text
from services.chunker import chunk_text
from services.qa_service import answer_question, index_pdf_chunks
from services.history_service import save_qa_history
from services.history_service import save_qa_history, get_dashboard_data

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

# Folder Setup
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db_connection():
    """
    Standard helper to connect to your SQL Server database.
    """
    conn_str = (
        "Driver={SQL Server};"
        "Server=.;"  # Replace with your server name from SSMS
        "Database=healthapp_db;"   # Replace with your actual database name
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)


def get_db():
    return pyodbc.connect(Config.DB_CONNECTION)


# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1])
    return None

# --- Helper Functions ---


def save_document_metadata(filename, file_type, path):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documents (filename, file_type, file_path, uploaded_by)
        VALUES (?, ?, ?, ?)
    """, (filename, file_type, path, current_user.id))
    conn.commit()
    conn.close()

# --- Routes ---


@app.route("/")
def home():
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed = generate_password_hash(password)
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except Exception as e:
            return f"Error: {e}"
    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[1], password):
            login_user(User(user[0], username))
            return redirect(url_for("dashboard"))
    return render_template("auth/login.html")


# In app.py

@app.route('/dashboard')
@login_required
def dashboard():
    # Call our new helper function
    total_q, total_docs, recent = get_dashboard_data(current_user.id)

    return render_template('dashboard.html',
                           total_questions=total_q,
                           total_docs=total_docs,
                           recent_activity=recent)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/history")
@login_required
def history():
    conn = get_db_connection()
    cursor = conn.cursor()

    # We select 'confidence' specifically because that's where your real data is
    query = """
        SELECT q.asked_at, q.question_text, a.answer_text,
               a.confidence, a.source_info, a.id, u.username,
               a.is_correct, a.is_verified
        FROM questions q
        JOIN answers a ON q.id = a.question_id
        JOIN users u ON q.user_id = u.id
    """

    # Fetch Global History
    cursor.execute(query + " ORDER BY q.asked_at DESC")
    rows = cursor.fetchall()

    # Map SQL Server rows to a list of dictionaries for the template
    columns = [column[0] for column in cursor.description]
    global_history = [dict(zip(columns, row)) for row in rows]

    # Filter for My History
    my_history = [
        item for item in global_history if item['username'] == current_user.username]

    conn.close()
    return render_template("history.html", my_history=my_history, global_history=global_history)


@app.route("/ask", methods=["GET", "POST"])
@login_required
def ask():
    answer, question, source, conf = None, None, None, None

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            clean_question = question.strip()

            # --- STEP 1: CHECK CACHE ---
            conn = get_db_connection()
            cursor = conn.cursor()

            # Find the most recent answer to this exact question
            cursor.execute("""
                SELECT TOP 1 a.answer_text, a.confidence, a.source_info
                FROM questions q
                JOIN answers a ON q.id = a.question_id
                WHERE q.question_text = ? 
                ORDER BY q.asked_at DESC
            """, (clean_question,))

            row = cursor.fetchone()
            conn.close()

            if row:
                # OPTION A: CACHE HIT (Found in DB)
                print("⚡ CACHE HIT: Serving from Database.")
                answer = row[0]
                conf = row[1]
                source = row[2]

                # IMPORTANT: Save this interaction so it shows in YOUR dashboard history
                save_qa_history(current_user.id, clean_question,
                                answer, conf, source)

            else:
                # OPTION B: CACHE MISS (Ask AI)
                print("🧠 CACHE MISS: Generating new answer...")
                ans, meta, confidence = answer_question(clean_question)

                answer = ans
                conf = confidence

                # Safety Check: Handle cases where no source is found
                if meta and len(meta) > 0:
                    # 1. Get the Document Name
                    doc_name = meta[0]['document']

                    # 2. Extract all unique page numbers from the Top 5 results
                    unique_pages = sorted(
                        list(set(int(m['page']) for m in meta)))

                    # 3. Join them into a string (e.g., "5, 8, 12")
                    pages_str = ", ".join(map(str, unique_pages))

                    source = f"{doc_name} (Pages: {pages_str})"
                else:
                    source = "Unknown Source"
                # Save to History
                save_qa_history(current_user.id, clean_question,
                                answer, conf, source)

            return render_template("ask.html", question=clean_question, answer=answer, source=source, conf=conf)

    return render_template("ask.html")


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # CRITICAL: This defines file_ext for the logic below
            file_ext = filename.rsplit('.', 1)[1].lower()

            # Create specific subfolders for storage
            subfolder = 'pdf' if file_ext == 'pdf' else 'excel'
            target_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(target_dir, exist_ok=True)

            file_path = os.path.join(target_dir, filename)
            file.save(file_path)

            if file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
                df = df.fillna('')  # Fix empty cells
                new_results = []

                for index, row in df.iterrows():
                    # 1. Safety conversion for text
                    q_text = str(row['Question']).strip()
                    if not q_text or q_text.lower() == 'nan':
                        continue

                    # 2. CRITICAL FIX: The 3rd variable is ALREADY the score
                    # Do not call it 'distances', call it 'conf_score'
                    ans, meta, conf_score = answer_question(q_text)

                    # 3. Use the score directly. Do NOT do [0] or math on it.
                    conf = conf_score

                    # 4. Safe source formatting
                    if meta and len(meta) > 0:
                        src = f"{meta[0]['document']} (Page {meta[0]['page']})"
                    else:
                        src = "Unknown Source"

                    # 5. Save and Append
                    save_qa_history(current_user.id, q_text, ans, conf, src)

                    new_results.append({
                        'question': q_text,
                        'answer': ans,
                        'confidence': conf,
                        'source': src
                    })

                    # Optional: Sleep to prevent crashing on low-RAM systems
                    time.sleep(2.0)
                # --- NEW CODE STARTS HERE ---
                # 1. Create a DataFrame from the results
                report_df = pd.DataFrame(new_results)

                # 2. Define a unique filename for this user
                report_filename = f'analysis_report_{current_user.id}.xlsx'
                report_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], '..', 'static', report_filename)

                # 3. Save the Excel file to the static folder
                report_df.to_excel(report_path, index=False)

                # 4. Pass the filename to the template
                return render_template('upload_results.html', results=new_results, report_file=report_filename)
                # --- NEW CODE ENDS HERE ---

            # Add this right after the Excel 'if' block ends
            elif file_ext == 'pdf':
                save_document_metadata(filename, "PDF", file_path)
                pages = extract_pdf_text(file_path)

                all_chunks = []
                for page in pages:
                    chunks = chunk_text(page["text"])
                    for c in chunks:
                        all_chunks.append({"text": c, "page": page["page"]})

                # This indexes the PDF so the AI can answer your Excel questions!
                index_pdf_chunks(all_chunks, filename)

                return redirect(url_for('ask'))

    return render_template('upload.html')


@app.route("/update_answer/<int:answer_id>", methods=['POST'])
@login_required
def update_answer(answer_id):
    # 1. Capture the checkbox status ('on' if checked, None if not)
    is_correct = 1 if request.form.get('is_correct') else 0

    # 2. Capture the updated AI answer text
    new_text = request.form.get('answer_text')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 3. Update BOTH columns so Team History and User History stay identical
        cursor.execute("""
            UPDATE answers 
            SET answer_text = ?, 
                is_correct = ?, 
                is_verified = ? 
            WHERE id = ?
        """, (new_text, is_correct, is_correct, answer_id))

        conn.commit()
    except Exception as e:
        print(f"Update failed: {e}")
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('history'))


@app.route('/download_results', methods=['POST'])
@login_required
def download_results():
    # Get the results data sent from the webpage
    results = request.json.get('results', [])

    # Create a file-like buffer for the PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # PDF Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, "Medical AI Analysis Report")
    p.setFont("Helvetica", 10)
    p.drawString(100, height - 70,
                 f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    y = height - 100
    for res in results:
        if y < 100:  # Create a new page if we run out of space
            p.showPage()
            y = height - 50

        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, f"Q: {res['question']}")
        y -= 20

        p.setFont("Helvetica", 10)
        # Wrap text logic could be added here for very long answers
        p.drawString(100, y, f"A: {res['answer'][:100]}...")
        y -= 15
        p.drawString(
            100, y, f"Confidence: {res['confidence']}% | Source: {res['source']}")
        y -= 30  # Space between entries

    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="Medical_Report.pdf", mimetype='application/pdf')


@app.route("/delete_history/<int:answer_id>", methods=['POST'])
@login_required
def delete_history(answer_id):
    conn = get_db_connection()  # Use your SQL connection helper
    cursor = conn.cursor()

    try:
        # 1. Find the question_id linked to this answer
        cursor.execute(
            "SELECT question_id FROM answers WHERE id = ?", (answer_id,))
        row = cursor.fetchone()

        if row:
            q_id = row[0]
            # 2. Delete the answer (Foreign Key)
            cursor.execute("DELETE FROM answers WHERE id = ?", (answer_id,))
            # 3. Delete the parent question
            cursor.execute("DELETE FROM questions WHERE id = ?", (q_id,))

        conn.commit()
    except Exception as e:
        print(f"Delete Error: {e}")
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('history'))

# --- NEW ROUTE FOR UPLOADED FILES PAGE ---


@app.route('/uploaded-files')
@login_required
def uploaded_files():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_root = os.path.join(base_dir, 'uploads')

    files_data = []

    # We need to look inside these two specific folders
    subfolders = ['pdf', 'excel']

    print(f"DEBUG: Root upload path is: {upload_root}")

    if os.path.exists(upload_root):
        for sub in subfolders:
            # Construct full path to the subfolder (e.g., uploads/pdf)
            folder_path = os.path.join(upload_root, sub)

            # Check if this subfolder exists before trying to read it
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    # Only show actual files (skip system files)
                    if filename.lower().endswith(('.pdf', '.xlsx', '.xls')):
                        filepath = os.path.join(folder_path, filename)
                        try:
                            mod_time = os.path.getmtime(filepath)
                            date_obj = datetime.fromtimestamp(mod_time)

                            files_data.append({
                                'source_doc': filename,
                                'last_used': date_obj,
                                'question_count': sub.upper()  # Shows "PDF" or "EXCEL"
                            })
                        except Exception as e:
                            print(f"Error reading {filename}: {e}")
    else:
        print("DEBUG: Uploads folder does not exist!")

    # Sort by newest first
    files_data.sort(key=lambda x: x['last_used'], reverse=True)

    return render_template('uploaded_files.html', files=files_data)


if __name__ == "__main__":
    app.run(debug=True)
