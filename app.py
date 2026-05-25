from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os, sqlite3, csv

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "rgpd_evidences.db")
UPLOAD_DIR = os.path.join(APP_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "RGPD_Production_2026_Secure_Key"

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = bcrypt.generate_password_hash("Admin@2026!").decode("utf-8")

CATEGORIES = [
    "Registre des traitements",
    "Analyse d'impact DPIA/AIPD",
    "Consentement",
    "Contrats sous-traitants",
    "Sécurité technique",
    "Gestion des droits des personnes",
    "Violation de données",
    "Formation et sensibilisation",
    "Politique de confidentialité",
    "Preuves d'audit"
]
STATUSES = ["À collecter", "En cours", "Validée", "À mettre à jour", "Expirée", "Critique"]

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS evidences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        owner TEXT,
        status TEXT NOT NULL,
        document_date TEXT,
        review_date TEXT,
        legal_basis TEXT,
        file_name TEXT,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and bcrypt.check_password_hash(ADMIN_PASSWORD_HASH, password):
            login_user(User(username))
            return redirect(url_for("dashboard"))

        flash("Identifiant ou mot de passe incorrect.")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    conn = db()
    total = conn.execute("SELECT COUNT(*) c FROM evidences").fetchone()["c"]
    by_status = conn.execute("SELECT status, COUNT(*) c FROM evidences GROUP BY status").fetchall()
    by_category = conn.execute("SELECT category, COUNT(*) c FROM evidences GROUP BY category").fetchall()
    latest = conn.execute("SELECT * FROM evidences ORDER BY id DESC LIMIT 8").fetchall()
    conn.close()
    return render_template("dashboard.html", total=total, by_status=by_status, by_category=by_category, latest=latest)

@app.route("/evidences")
@login_required
def evidences():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()

    sql = "SELECT * FROM evidences WHERE 1=1"
    params = []

    if q:
        sql += " AND (title LIKE ? OR description LIKE ? OR owner LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND category = ?"
        params.append(category)
    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY id DESC"

    conn = db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template("evidences.html", evidences=rows, categories=CATEGORIES, statuses=STATUSES, q=q, selected_category=category, selected_status=status)

@app.route("/evidence/new", methods=["GET", "POST"])
@login_required
def new_evidence():
    if request.method == "POST":
        f = request.files.get("file")
        file_name = None

        if f and f.filename:
            file_name = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_DIR, file_name))

        conn = db()
        conn.execute("""
            INSERT INTO evidences
            (title, category, description, owner, status, document_date, review_date, legal_basis, file_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["title"],
            request.form["category"],
            request.form.get("description"),
            request.form.get("owner"),
            request.form["status"],
            request.form.get("document_date"),
            request.form.get("review_date"),
            request.form.get("legal_basis"),
            file_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()

        flash("Évidence ajoutée avec succès.")
        return redirect(url_for("evidences"))

    return render_template("form.html", categories=CATEGORIES, statuses=STATUSES)

@app.route("/evidence/<int:evidence_id>/delete", methods=["POST"])
@login_required
def delete_evidence(evidence_id):
    conn = db()
    item = conn.execute("SELECT file_name FROM evidences WHERE id = ?", (evidence_id,)).fetchone()

    if item and item["file_name"]:
        path = os.path.join(UPLOAD_DIR, item["file_name"])
        if os.path.exists(path):
            os.remove(path)

    conn.execute("DELETE FROM evidences WHERE id = ?", (evidence_id,))
    conn.commit()
    conn.close()

    flash("Évidence supprimée.")
    return redirect(url_for("evidences"))

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

@app.route("/export")
@login_required
def export_csv():
    export_path = os.path.join(APP_DIR, "export_evidences_rgpd.csv")
    conn = db()
    rows = conn.execute("SELECT * FROM evidences ORDER BY id DESC").fetchall()
    conn.close()

    with open(export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["ID", "Titre", "Catégorie", "Description", "Responsable", "Statut", "Date document", "Date revue", "Base légale", "Fichier", "Créé le"])
        for r in rows:
            writer.writerow([r["id"], r["title"], r["category"], r["description"], r["owner"], r["status"], r["document_date"], r["review_date"], r["legal_basis"], r["file_name"], r["created_at"]])

    return send_from_directory(APP_DIR, "export_evidences_rgpd.csv", as_attachment=True)


if __name__ == "__main__":
    import os
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
