// ============================================================
// results.js — runs ONLY on the results page (results.html)
// Depends on renderRepoCards() from main.js (loaded first in base.html)
// ============================================================

const stack = document.getElementById("results-stack");
const query = window.__INITIAL_QUERY__ || "";

async function loadResults(q) {
  stack.innerHTML = `<p class="loading-msg">Pulling cards from the drawer&hellip;</p>`;
  try {
    // Same endpoint Team Member 2's IR module will eventually power.
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) throw new Error("Server error");
    const repos = await res.json();
    renderRepoCards(repos, stack);
  } catch (err) {
    stack.innerHTML = `<p class="error-msg">Couldn't reach the server. Make sure app.py is running.</p>`;
  }
}

loadResults(query);

// Also wire up the "search again" box on this page
const resultsSearchForm = document.getElementById("search-form-results");
if (resultsSearchForm) {
  resultsSearchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const newQuery = document.getElementById("q").value.trim();
    window.location.href = `/results?q=${encodeURIComponent(newQuery)}`;
  });
}
