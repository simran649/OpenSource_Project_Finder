// ============================================================
// main.js — runs on the HOME page (index.html)
// Beginner notes are left in on purpose — read the comments!
// ============================================================

// ---- 1. Search form: typing a query and hitting "Pull card"
//         just sends you to /results?q=whatever-you-typed ----
const searchForm = document.getElementById("search-form");
if (searchForm) {
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = document.getElementById("q").value.trim();
    // redirect the browser to the results page with ?q= in the URL
    window.location.href = `/results?q=${encodeURIComponent(query)}`;
  });
}

// ---- 2. Quick tag chips just fill the search box and submit ----
document.querySelectorAll(".tag-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const q = chip.dataset.query;
    window.location.href = `/results?q=${encodeURIComponent(q)}`;
  });
});

// ---- 3. Skill-match form: this one calls our API directly with
//         fetch() and draws the results without leaving the page ----
const skillForm = document.getElementById("skill-match-form");
const skillResultsBox = document.getElementById("skill-results");

if (skillForm) {
  skillForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // grab all checked language boxes
    const languages = Array.from(
      skillForm.querySelectorAll('input[name="language"]:checked')
    ).map((el) => el.value);

    // grab the chosen radio level
    const level = skillForm.querySelector('input[name="level"]:checked').value;

    skillResultsBox.innerHTML = `<p class="loading-msg">Matching your card&hellip;</p>`;

    try {
      // This POSTs to /api/skill-match — Team Member 4 & 3's job.
      // Right now app.py fakes it. Later, same URL, real ML model.
      const res = await fetch("/api/skill-match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ languages, level }),
      });

      if (!res.ok) throw new Error("Server error");

      const repos = await res.json();
      renderRepoCards(repos, skillResultsBox);
    } catch (err) {
      skillResultsBox.innerHTML = `<p class="error-msg">Couldn't fetch matches. Is the Flask server running?</p>`;
    }
  });
}

// ============================================================
// Shared helper — turns a list of repo objects into HTML cards.
// Used by both main.js (skill match) and results.js (search).
// ============================================================
function renderRepoCards(repos, container) {
  if (!repos || repos.length === 0) {
    container.innerHTML = `<p class="empty-msg">No matching repositories in the drawer. Try different terms.</p>`;
    return;
  }

  container.innerHTML = repos
    .map(
      (repo) => `
    <a class="repo-card" href="/repo/${repo.id}">
      <div class="repo-card-top">
        <span class="repo-name">${escapeHtml(repo.name)}</span>
        <span class="repo-owner">by ${escapeHtml(repo.owner)}</span>
      </div>
      <p class="repo-desc">${escapeHtml(repo.description)}</p>
      <div class="repo-meta">
        <span>&#9733; <strong>${formatNumber(repo.stars)}</strong> stars</span>
        <span>&#8942; <strong>${formatNumber(repo.forks)}</strong> forks</span>
        <span><strong>${escapeHtml(repo.language)}</strong></span>
        <span><strong>${escapeHtml(repo.difficulty)}</strong></span>
      </div>
      <div class="repo-topics">
        ${repo.topics.map((t) => `<span class="topic-pill">${escapeHtml(t)}</span>`).join("")}
      </div>
    </a>
  `
    )
    .join("");
}

function formatNumber(n) {
  return n.toLocaleString("en-US");
}

// very small helper to avoid accidentally injecting raw HTML from data
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
