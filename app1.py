from flask import Flask, request, session, jsonify, render_template
import os
from datetime import datetime
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="templates1", static_folder="static1")
app.secret_key = "m1n2b3"

os.makedirs("db", exist_ok=True)
db       = TinyDB(os.path.join("db", "notes.json"), indent=4)
users_tb = db.table("users")
notes_tb = db.table("notes")
User     = Query()
Note     = Query()

def logged_in():
    return "user_id" in session

# ── Sinhroni klici – Flask vrne HTML stran ────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/note")
def note_page():
    return render_template("/note.html")
# ── Asinhroni klici – AJAX API ────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Vnesite uporabniško ime in geslo."}), 400
    if users_tb.search(User.username == username):
        return jsonify({"error": "Uporabniško ime je že zasedeno."}), 400
    users_tb.insert({
        "username": username,
        "password": generate_password_hash(password)
    })
    return jsonify({"ok": True})

@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    result   = users_tb.search(User.username == username)
    if result and check_password_hash(result[0]["password"], password):
        session["user_id"]  = result[0].doc_id
        session["username"] = result[0]["username"]
        return jsonify({"ok": True})
    return jsonify({"error": "Napačno uporabniško ime ali geslo."}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/me")
def me():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"username": session["username"]})

@app.route("/api/notes")
def get_notes():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    q       = request.args.get("q", "").strip().lower()
    results = notes_tb.search(Note.user_id == session["user_id"])
    if q:
        results = [n for n in results if q in n["title"].lower() or q in n["content"].lower()]
    results.sort(key=lambda n: n["created_at"], reverse=True)
    return jsonify([{"id": n.doc_id, "title": n["title"],
                     "content": n["content"], "created_at": n["created_at"]} for n in results])

@app.route("/api/notes/<int:note_id>")
def get_note(note_id):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    note = notes_tb.get(doc_id=note_id)
    if not note or note["user_id"] != session["user_id"]:
        return jsonify({"error": "Ne obstaja"}), 404
    return jsonify({"id": note.doc_id, "title": note["title"], "content": note["content"]})

@app.route("/api/notes", methods=["POST"])
def create_note():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data    = request.get_json()
    title   = data.get("title", "").strip()
    content = data.get("content", "").strip()
    if not title or not content:
        return jsonify({"error": "Naslov in vsebina sta obvezna."}), 400
    doc_id = notes_tb.insert({
        "user_id":    session["user_id"],
        "title":      title,
        "content":    content,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({"id": doc_id})

@app.route("/api/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data    = request.get_json()
    title   = data.get("title", "").strip()
    content = data.get("content", "").strip()
    notes_tb.update({"title": title, "content": content}, doc_ids=[note_id])
    return jsonify({"ok": True})

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    notes_tb.remove(doc_ids=[note_id])
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
