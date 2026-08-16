/**
 * main.js - Global App Utilities, Comparison Store, and Home Page Interactions
 */

// =========================================================================
// 1. GLOBAL TOAST NOTIFICATION SYSTEM
// =========================================================================
window.showToast = function (message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  
  let icon = "&#8505;";
  if (type === "success") icon = "&#10003;";
  if (type === "error") icon = "&#9888;";

  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
};

// =========================================================================
// 2. GLOBAL COMPARISON STORAGE & FLOATING BAR
// =========================================================================
const CompareManager = {
  KEY: "projectfinder_compare_ids",

  getIds() {
    try {
      return JSON.parse(localStorage.getItem(this.KEY) || "[]");
    } catch {
      return [];
    }
  },

  add(id, name) {
    let ids = this.getIds();
    id = parseInt(id);
    if (!ids.includes(id)) {
      if (ids.length >= 4) {
        showToast("You can compare up to 4 repositories at once.", "error");
        return false;
      }
      ids.push(id);
      localStorage.setItem(this.KEY, JSON.stringify(ids));
      this.updateUI();
      showToast(`Added "${name || 'Repository'}" to comparison.`, "success");
      return true;
    }
    return false;
  },

  remove(id) {
    let ids = this.getIds();
    id = parseInt(id);
    ids = ids.filter((item) => item !== id);
    localStorage.setItem(this.KEY, JSON.stringify(ids));
    this.updateUI();
    showToast("Removed repository from comparison.", "info");
  },

  clear() {
    localStorage.removeItem(this.KEY);
    this.updateUI();
    showToast("Cleared comparison list.", "info");
  },

  has(id) {
    return this.getIds().includes(parseInt(id));
  },

  updateUI() {
    const ids = this.getIds();
    const navBadge = document.getElementById("nav-compare-count");
    if (navBadge) navBadge.textContent = ids.length;

    const bar = document.getElementById("floating-compare-bar");
    const countText = document.getElementById("compare-count-text");
    const launchBtn = document.getElementById("launch-compare-btn");

    if (bar && countText && launchBtn) {
      if (ids.length > 0) {
        countText.textContent = `${ids.length} ${ids.length === 1 ? "Repository" : "Repositories"}`;
        launchBtn.href = `/compare?ids=${ids.join(",")}`;
        bar.classList.add("show");
      } else {
        bar.classList.remove("show");
      }
    }

    // Sync all compare buttons on current page
    document.querySelectorAll(".btn-card-compare, .btn-compare-toggle").forEach((btn) => {
      const rid = parseInt(btn.dataset.repoId);
      if (this.has(rid)) {
        btn.classList.add("active");
        btn.innerHTML = `<span>&#10003;</span> Compared`;
      } else {
        btn.classList.remove("active");
        btn.innerHTML = `<span>&#9878;</span> Compare`;
      }
    });
  },
};

window.CompareManager = CompareManager;

// =========================================================================
// 3. HOME PAGE INTERACTION LOGIC
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
  CompareManager.updateUI();

  // Clear compare bar button
  const clearBtn = document.getElementById("clear-compare-btn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => CompareManager.clear());
  }

  // Home search form
  const homeSearchForm = document.getElementById("search-form");
  if (homeSearchForm) {
    homeSearchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = document.getElementById("q").value.trim();
      if (q) {
        window.location.href = `/results?q=${encodeURIComponent(q)}`;
      }
    });
  }

  // Skill Matcher Form
  const skillForm = document.getElementById("skill-match-form");
  const skillResultsContainer = document.getElementById("skill-results-container");
  const skillResultsBox = document.getElementById("skill-results");
  const skillCountBadge = document.getElementById("skill-results-count");
  const resetBtn = document.getElementById("reset-skill-form");

  if (skillForm) {
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        skillForm.reset();
        if (skillResultsContainer) skillResultsContainer.style.display = "none";
      });
    }

    skillForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const languages = Array.from(
        skillForm.querySelectorAll('input[name="language"]:checked')
      ).map((el) => el.value);

      const levelEl = skillForm.querySelector('input[name="level"]:checked');
      const level = levelEl ? levelEl.value : "";

      const domainEl = skillForm.querySelector('input[name="domain"]:checked');
      const domain = domainEl ? domainEl.value : "";

      if (skillResultsContainer) {
        skillResultsContainer.style.display = "block";
      }

      if (skillResultsBox) {
        skillResultsBox.innerHTML = `
          <div class="loading-state" style="grid-column: 1 / -1; padding: 40px 0;">
            <div class="spinner"></div>
            <p>Matching repositories across our Machine Learning index&hellip;</p>
          </div>
        `;
      }

      try {
        const res = await fetch("/api/skill-match", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ languages, level, domain }),
        });

        if (!res.ok) throw new Error("Server error");
        const repos = await res.json();

        if (skillCountBadge) {
          skillCountBadge.textContent = `${repos.length} matches found`;
        }

        renderRepoCards(repos, skillResultsBox);
      } catch (err) {
        if (skillResultsBox) {
          skillResultsBox.innerHTML = `<p class="error-msg" style="grid-column: 1 / -1; text-align: center; padding: 30px;">Failed to match repositories. Make sure Flask is running.</p>`;
        }
      }
    });
  }

  // Global delegate for compare button clicks
  document.body.addEventListener("click", (e) => {
    const btn = e.target.closest(".btn-card-compare, .btn-compare-toggle");
    if (btn) {
      e.preventDefault();
      e.stopPropagation();
      const rid = btn.dataset.repoId;
      const rname = btn.dataset.repoName;
      if (CompareManager.has(rid)) {
        CompareManager.remove(rid);
      } else {
        CompareManager.add(rid, rname);
      }
    }
  });
});

// =========================================================================
// 4. SHARED REPOSITORY CARD RENDERER
// =========================================================================
window.renderRepoCards = function (repos, container, isList = false) {
  if (!container) return;

  if (!repos || repos.length === 0) {
    container.innerHTML = `
      <div class="empty-state-box" style="grid-column: 1 / -1; text-align: center; padding: 50px 20px; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md);">
        <div style="font-size: 2.5rem; margin-bottom: 10px;">🔍</div>
        <h3>No Matching Repositories Found</h3>
        <p style="color: var(--text-dim); margin-top: 6px;">Try loosening your filters or searching for general keywords like "web", "ml", or "flask".</p>
      </div>
    `;
    return;
  }

  container.className = isList ? "repo-cards-list" : "repo-cards-grid";

  container.innerHTML = repos
    .map((repo) => {
      const diffClass = (repo.difficulty || "intermediate").toLowerCase();
      const isCompared = CompareManager.has(repo.id);

      return `
      <div class="repo-card">
        <div class="repo-card-top">
          <div>
            <a href="/repo/${repo.id}" class="repo-name">${escapeHtml(repo.name)}</a>
            <div class="repo-owner">by ${escapeHtml(repo.owner || "Unknown")}</div>
          </div>
          ${repo.match_percentage ? `<span class="match-badge">${repo.match_percentage}% Match</span>` : ""}
        </div>

        <p class="repo-desc">${escapeHtml(repo.description)}</p>

        <div class="repo-badges-strip">
          <span class="difficulty-badge difficulty-${diffClass}">
            ${diffClass === "beginner" ? "🟢 Beginner" : diffClass === "intermediate" ? "🟡 Intermediate" : "🔴 Advanced"}
          </span>
          ${repo.domain && repo.domain !== "Unknown" ? `<span class="domain-badge">🏢 ${escapeHtml(repo.domain)}</span>` : ""}
          <span class="lang-badge">🛠️ ${escapeHtml(repo.language)}</span>
        </div>

        <div class="repo-stats-row">
          <span class="repo-stat-item">⭐ <strong>${formatNumber(repo.stars)}</strong></span>
          <span class="repo-stat-item">🍴 <strong>${formatNumber(repo.forks)}</strong></span>
          <span class="repo-stat-item">💚 <strong>${repo.community_health}%</strong></span>
          <span class="repo-stat-item">Index: <strong>${repo.readiness_score}/100</strong></span>
        </div>

        <div class="repo-card-actions">
          <a href="/repo/${repo.id}" class="btn btn-sm btn-outline">View Details &rarr;</a>
          <button type="button" class="btn-card-compare ${isCompared ? "active" : ""}" data-repo-id="${repo.id}" data-repo-name="${escapeHtml(repo.name)}">
            ${isCompared ? "<span>&#10003;</span> Compared" : "<span>&#9878;</span> Compare"}
          </button>
        </div>
      </div>
    `;
    })
    .join("");
};

function formatNumber(n) {
  return Number(n || 0).toLocaleString("en-US");
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
