from flask import Flask, request, session, jsonify, render_template
import os, uuid
from datetime import datetime
from tinydb import TinyDB, Query
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder="templates2", static_folder="static2")
app.secret_key = "m1n2b3"

UPLOAD_FOLDER = os.path.join("static2", "uploads")
ALLOWED_EXT   = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("db", exist_ok=True)

db          = TinyDB(os.path.join("db", "social.json"), indent=4)
users_tb    = db.table("users")
posts_tb    = db.table("posts")
likes_tb    = db.table("likes")
comments_tb = db.table("comments")
User    = Query()
Post    = Query()
Like    = Query()
Comment = Query()

def logged_in():
    return "user_id" in session

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

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

@app.route("/profile")
def profile_page():
    return render_template("profile.html")

# ── Asinhroni klici – AJAX API ────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if users_tb.search(User.username == username):
        return jsonify({"error": "Uporabniško ime je zasedeno."}), 400
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
    return jsonify({"error": "Napačni podatki."}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/me")
def me():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"user_id": session["user_id"], "username": session["username"]})

@app.route("/api/posts")
def get_posts():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    q        = request.args.get("q", "").strip().lower()
    uid      = session["user_id"]
    all_posts = posts_tb.all()
    if q:
        all_posts = [p for p in all_posts if p.get("text") and q in p["text"].lower()]
    all_posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    result = []
    for p in all_posts:
        author = users_tb.get(doc_id=p["user_id"])
        result.append({
            "id":         p.doc_id,
            "text":       p.get("text", ""),
            "image_path": p.get("image_path"),
            "created_at": p["created_at"],
            "username":   author["username"] if author else "?",
            "author_id":  p["user_id"],
            "like_count": len(likes_tb.search(Like.post_id == p.doc_id)),
            "user_liked": bool(likes_tb.search((Like.post_id == p.doc_id) & (Like.user_id == uid)))
        })
    return jsonify(result)

@app.route("/api/posts", methods=["POST"])
def create_post():
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    text       = request.form.get("text", "").strip()
    image      = request.files.get("image")
    image_path = None
    if image and image.filename and allowed_file(image.filename):
        ext      = image.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        image.save(os.path.join(UPLOAD_FOLDER, filename))
        image_path = f"uploads/{filename}"
    if not text and not image_path:
        return jsonify({"error": "Objava mora imeti besedilo ali sliko."}), 400
    posts_tb.insert({
        "user_id":    session["user_id"],
        "text":       text,
        "image_path": image_path,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({"ok": True})

@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    post = posts_tb.get(doc_id=post_id)
    if post and post["user_id"] == session["user_id"]:
        if post.get("image_path"):
            try:
                os.remove(os.path.join("static2", post["image_path"]))
            except FileNotFoundError:
                pass
        likes_tb.remove(Like.post_id == post_id)
        comments_tb.remove(Comment.post_id == post_id)
        posts_tb.remove(doc_ids=[post_id])
    return jsonify({"ok": True})

@app.route("/api/like/<int:post_id>", methods=["POST"])
def toggle_like(post_id):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    uid      = session["user_id"]
    existing = likes_tb.search((Like.post_id == post_id) & (Like.user_id == uid))
    if existing:
        likes_tb.remove((Like.post_id == post_id) & (Like.user_id == uid))
        liked = False
    else:
        likes_tb.insert({"post_id": post_id, "user_id": uid})
        liked = True
    count = len(likes_tb.search(Like.post_id == post_id))
    return jsonify({"liked": liked, "count": count})

@app.route("/api/comments/<int:post_id>")
def get_comments(post_id):
    raw = sorted(comments_tb.search(Comment.post_id == post_id),
                 key=lambda c: c.get("created_at", ""))
    result = []
    for c in raw:
        author = users_tb.get(doc_id=c["user_id"])
        result.append({"text": c["text"], "username": author["username"] if author else "?"})
    return jsonify(result)

@app.route("/api/comments/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Prazen komentar"}), 400
    comments_tb.insert({
        "post_id":    post_id,
        "user_id":    session["user_id"],
        "text":       text,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return jsonify({"text": text, "username": session["username"]})

@app.route("/api/profile/<username>")
def get_profile(username):
    if not logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    result = users_tb.search(User.username == username)
    if not result:
        return jsonify({"error": "Ne obstaja"}), 404
    user  = result[0]
    posts = sorted(posts_tb.search(Post.user_id == user.doc_id),
                   key=lambda p: p.get("created_at", ""), reverse=True)
    return jsonify({
        "username": user["username"],
        "posts": [{"id": p.doc_id, "text": p.get("text", ""),
                   "image_path": p.get("image_path"), "created_at": p["created_at"]}
                  for p in posts]
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
