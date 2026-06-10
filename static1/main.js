"index -----------------------------------------------"

async function load_notes() {
  const q    = document.getElementById("search") ? document.getElementById("search").value : "";
  const res  = await fetch("/api/notes?q=" + encodeURIComponent(q));
  const data = await res.json();
  render_notes(data);
}

function render_notes(notes) {
  const div = document.getElementById("noteList");
  if (!div) return;
  if (notes.length === 0) { div.innerHTML = "<p>Ni zapiskov.</p>"; return; }
  div.innerHTML = notes.map(n => `
    <div class="note-card">
      <strong>${n.title}</strong>
      <span>${n.created_at.slice(0, 10)}</span><br>
      <p>${n.content.slice(0, 100)}${n.content.length > 100 ? "..." : ""}</p>
      <button onclick="window.location.href='/note?id=${n.id}'">Uredi</button>
      <button onclick="delete_note(${n.id})">Izbriši</button>
    </div>
  `).join("");
}

async function delete_note(id) {
  if (!confirm("Izbriši ta zapisek?")) return;
  await fetch("/api/notes/" + id, { method: "DELETE" });
  load_notes();
}

async function logout() {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/login";
}

"login-------------------------------------------------------------"

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
  if (data.ok) {
    window.location.href = "/";
  } else {
    document.getElementById("msg").textContent = data.error;
  }
}

"register-------------------------------------------------------------------"

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
  if (data.ok) {
    window.location.href = "/login";
  } else {
    document.getElementById("msg").textContent = data.error;
  }
}

"note-----------------------------------------------------------------"

const params = new URLSearchParams(window.location.search);
const noteId = params.get("id");

// Naloži obstoječ zapisek če urejamo
if (noteId && document.getElementById("title")) {
  document.getElementById("pageTitle").textContent = "Uredi zapisek";

  fetch("/api/notes/" + noteId)
    .then(r => r.json())
    .then(data => {
      document.getElementById("title").value   = data.title;
      document.getElementById("content").value = data.content;
    });

  // Auto-save med pisanjem (AJAX)
  let saveTimer;
  function autosave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      document.getElementById("autosave").textContent = "Shranjujem...";
      await fetch("/api/notes/" + noteId, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title:   document.getElementById("title").value,
          content: document.getElementById("content").value
        })
      });
      document.getElementById("autosave").textContent = "✓ Shranjeno";
    }, 1500);
  }

  document.getElementById("title").oninput   = autosave;
  document.getElementById("content").oninput = autosave;
}

async function save() {
  const title   = document.getElementById("title") ? document.getElementById("title").value.trim() : null;
  const content = document.getElementById("content") ? document.getElementById("content").value.trim() : null;
  if (title === null) return;

  if (!title || !content) {
    document.getElementById("msg").textContent = "Naslov in vsebina sta obvezna.";
    return;
  }

  if (noteId) {
    await fetch("/api/notes/" + noteId, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content })
    });
  } else {
    await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content })
    });
  }
  window.location.href = "/";
}
