let searchTimer;
let currentCity = {};

// ── Iskanje mesta med tipkanjem (AJAX) ────────────────────────────────────────

function search_city() {
  clearTimeout(searchTimer);
  const q = document.getElementById("citySearch").value.trim();
  if (q.length < 2) { document.getElementById("suggestions").innerHTML = ""; return; }

  searchTimer = setTimeout(async () => {
    const res  = await fetch("/api/geocode?q=" + encodeURIComponent(q));
    const data = await res.json();
    const div  = document.getElementById("suggestions");

    if (data.length === 0) { div.innerHTML = "<p>Ni zadetkov.</p>"; return; }
    div.innerHTML = data.map(d =>
      `<div class="suggestion" onclick="load_weather('${d.city}','${d.country}',${d.lat},${d.lon})">
        ${d.city}, ${d.country}
      </div>`
    ).join("");
  }, 350);
}

// ── Naloži vreme za izbrano mesto (AJAX) ──────────────────────────────────────

async function load_weather(city, country, lat, lon) {
  currentCity = { city, country, lat, lon };
  document.getElementById("suggestions").innerHTML = "";
  document.getElementById("citySearch").value = city;
  document.getElementById("weatherResult").innerHTML = "<p>Nalagam...</p>";

  const res  = await fetch(`/api/weather?city=${encodeURIComponent(city)}&country=${encodeURIComponent(country)}&lat=${lat}&lon=${lon}`);
  const data = await res.json();

  if (data.error) {
    document.getElementById("weatherResult").innerHTML = "<p>Napaka: " + data.error + "</p>";
    return;
  }

  const c = data.current;
  document.getElementById("weatherResult").innerHTML = `
    <div class="card">
      <h2>${data.city}, ${data.country}
        <button onclick="toggle_fav()" id="favBtn">☆ Priljubi</button>
      </h2>
      <p><strong>${c.temp}°C</strong> — ${c.desc}</p>
      <p>Občutek: ${c.feels_like}°C | Vlaga: ${c.humidity}% | Veter: ${c.wind} km/h | Padavine: ${c.precip} mm</p>
      <hr>
      <h3>7-dnevna napoved</h3>
      <table>
        <tr><th>Dan</th><th>Max</th><th>Min</th><th>Opis</th><th>Padavine</th></tr>
        ${data.daily.map(d => `
          <tr>
            <td>${d.date}</td><td>${d.max}°C</td><td>${d.min}°C</td>
            <td>${d.desc}</td><td>${d.precip} mm</td>
          </tr>
        `).join("")}
      </table>
    </div>
  `;
  load_sidebar();
}

// ── Dodaj/odstrani priljubljeno (AJAX) ────────────────────────────────────────

async function toggle_fav() {
  const res  = await fetch("/api/favorite", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(currentCity)
  });
  const data = await res.json();
  document.getElementById("favBtn").textContent =
    data.status === "added" ? "★ Priljubljeno" : "☆ Priljubi";
  load_sidebar();
}

// ── Naloži priljubljena in nedavna mesta ──────────────────────────────────────

async function load_sidebar() {
  const [favRes, recentRes] = await Promise.all([
    fetch("/api/favorites"),
    fetch("/api/recent")
  ]);
  const favs   = await favRes.json();
  const recent = await recentRes.json();

  document.getElementById("favSection").innerHTML = favs.length === 0 ? "" :
    "<h3>⭐ Priljubljena</h3>" +
    favs.map(f =>
      `<button class="chip" onclick="load_weather('${f.city}','${f.country}',${f.lat},${f.lon})">
        ${f.city}
      </button>`
    ).join("");

  document.getElementById("recentSection").innerHTML = recent.length === 0 ? "" :
    "<h3>🕐 Nedavna</h3>" +
    recent.map(r =>
      `<button class="chip" onclick="load_weather('${r.city}','${r.country}',${r.lat},${r.lon})">
        ${r.city}
      </button>`
    ).join("");
}

async function clear_history() {
  await fetch("/api/clear-history", { method: "POST" });
  load_sidebar();
}
