let currentUserId = null;

// ── Feed ──────────────────────────────────────────────────────────────────────

async function load_posts() {
  const q    = document.getElementById("search") ? document.getElementById("search").value : "";
  const res  = await fetch("/api/posts?q=" + encodeURIComponent(q));
  const data = await res.json();
  render_posts(data);
}

function render_posts(posts) {
  const feed = document.getElementById("feed");
  if (!feed) return;
  if (posts.length === 0) { feed.innerHTML = "<p>Ni objav.</p>"; return; }

  feed.innerHTML = posts.map(p => `
    <div class="card" id="post-${p.id}">
      <a href="/profile?u=${p.username}"><strong>@${p.username}</strong></a>
      <span style="color:gray; font-size:0.85em"> ${p.created_at}</span>
      ${p.author_id === currentUserId
        ? `<button onclick="delete_post(${p.id})" style="float:right">Izbriši</button>`
        : ""}
      ${p.text ? `<p>${p.text}</p>` : ""}
      ${p.image_path ? `<img src="/static/${p.image_path}" style="max-width:100%">` : ""}
      <div>
        <button onclick="toggle_like(${p.id})" id="like-btn-${p.id}"
          style="${p.user_liked ? 'color:red' : ''}">
          ❤️ <span id="like-count-${p.id}">${p.like_count}</span>
        </button>
        <button onclick="toggle_comments(${p.id})">💬 Komentarji</button>
      </div>
      <div id="comments-${p.id}" style="display:none; margin-top:8px">
        <div id="comments-list-${p.id}"></div>
        <input type="text" id="comment-input-${p.id}" placeholder="Komentar...">
        <button onclick="add_comment(${p.id})">Pošlji</button>
      </div>
    </div>
  `).join("");
}

async function new_post() {
  const form = new FormData();
  form.append("text", document.getElementById("postText").value);
  const img = document.getElementById("postImage").files[0];
  if (img) form.append("image", img);

  const res  = await fetch("/api/posts", { method: "POST", body: form });
  const data = await res.json();
  if (data.ok) {
    document.getElementById("postText").value  = "";
    document.getElementById("postImage").value = "";
    load_posts();
  } else {
    document.getElementById("postMsg").textContent = data.error;
  }
}

async function delete_post(id) {
  if (!confirm("Izbriši?")) return;
  await fetch("/api/posts/" + id, { method: "DELETE" });
  load_posts();
}

async function toggle_like(id) {
  const res  = await fetch("/api/like/" + id, { method: "POST" });
  const data = await res.json();
  document.getElementById("like-count-" + id).textContent = data.count;
  document.getElementById("like-btn-"   + id).style.color = data.liked ? "red" : "";
}

async function toggle_comments(id) {
  const div = document.getElementById("comments-" + id);
  if (div.style.display === "none") {
    div.style.display = "";
    const res  = await fetch("/api/comments/" + id);
    const data = await res.json();
    const list = document.getElementById("comments-list-" + id);
    list.innerHTML = data.length === 0 ? "<p>Ni komentarjev.</p>"
      : data.map(c => `<p><strong>@${c.username}</strong>: ${c.text}</p>`).join("");
  } else {
    div.style.display = "none";
  }
}

async function add_comment(id) {
  const input = document.getElementById("comment-input-" + id);
  const text  = input.value.trim();
  if (!text) return;
  const res  = await fetch("/api/comments/" + id, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  });
  const data = await res.json();
  const list = document.getElementById("comments-list-" + id);
  list.insertAdjacentHTML("beforeend",
    `<p><strong>@${data.username}</strong>: ${data.text}</p>`);
  input.value = "";
}

// ── Auth ──────────────────────────────────────────────────────────────────────

async function login() {
  const res  = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("username").value,
      password: document.getElementById("password").value
    })
  });
  const data = await res.json();
  if (data.ok) { window.location.href = "/"; }
  else { document.getElementById("msg").textContent = data.error; }
}

async function register() {
  const res  = await fetch("/api/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: document.getElementById("username").value,
      password: document.getElementById("password").value
    })
  });
  const data = await res.json();
  if (data.ok) { window.location.href = "/login"; }
  else { document.getElementById("msg").textContent = data.error; }
}

async function logout() {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
}

// ── Profil ────────────────────────────────────────────────────────────────────

const profileParams = new URLSearchParams(window.location.search);
const profileUser   = profileParams.get("u");

if (profileUser && document.getElementById("profileName")) {
  fetch("/api/profile/" + profileUser)
    .then(r => r.json())
    .then(data => {
      document.getElementById("profileName").textContent = "@" + data.username;
      document.getElementById("postCount").textContent   = data.posts.length + " objav";
      const div = document.getElementById("profilePosts");
      div.innerHTML = data.posts.length === 0 ? "<p>Ni objav.</p>"
        : data.posts.map(p => `
          <div class="card">
            ${p.text ? `<p>${p.text}</p>` : ""}
            ${p.image_path ? `<img src="/static/${p.image_path}" style="max-width:100%">` : ""}
            <small style="color:gray">${p.created_at.slice(0,10)}</small>
          </div>
        `).join("");
    });
}
