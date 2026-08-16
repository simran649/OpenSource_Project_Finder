/**
 * results.js - Faceted Search, Filtering, Sorting, and View Layouts
 */

document.addEventListener("DOMContentLoaded", () => {
  const stack = document.getElementById("results-stack");
  const countEl = document.getElementById("results-count-number");
  const searchForm = document.getElementById("search-form-results");
  const searchInput = document.getElementById("q-results");
  const queryDisplayText = document.getElementById("query-display-text");

  // Filters
  const diffRadios = document.querySelectorAll('input[name="filter-difficulty"]');
  const domRadios = document.querySelectorAll('input[name="filter-domain"]');
  const langSelect = document.getElementById("filter-language-select");
  const starsSlider = document.getElementById("min-stars-slider");
  const starsVal = document.getElementById("min-stars-val");
  const readmeCheckbox = document.getElementById("filter-has-readme");
  const clearFiltersBtn = document.getElementById("clear-all-filters");
  const sortSelect = document.getElementById("sort-by-select");

  // View toggles
  const gridBtn = document.getElementById("view-grid-btn");
  const listBtn = document.getElementById("view-list-btn");
  let isListView = false;

  // Initial State from URL
  let currentQuery = window.__INITIAL_QUERY__ || "";
  let currentDiff = window.__INITIAL_DIFF__ || "";
  let currentDom = window.__INITIAL_DOM__ || "";
  let currentLang = window.__INITIAL_LANG__ || "";
  let currentSort = window.__INITIAL_SORT__ || "relevance";
  let minStars = 0;
  let hasReadme = false;

  // Sync initial inputs
  if (currentDiff) {
    const r = document.querySelector(`input[name="filter-difficulty"][value="${currentDiff}"]`);
    if (r) r.checked = true;
  }
  if (currentDom) {
    const r = document.querySelector(`input[name="filter-domain"][value="${currentDom}"]`);
    if (r) r.checked = true;
  }
  if (currentLang && langSelect) langSelect.value = currentLang;
  if (currentSort && sortSelect) sortSelect.value = currentSort;

  // Fetch and render function
  async function fetchResults() {
    if (!stack) return;

    stack.innerHTML = `
      <div class="loading-state" style="grid-column: 1 / -1; padding: 60px 0; text-align: center;">
        <div class="spinner"></div>
        <p style="color: var(--text-dim);">Scanning index & computing ML difficulty weights&hellip;</p>
      </div>
    `;

    const params = new URLSearchParams();
    if (currentQuery) params.set("q", currentQuery);
    if (currentDiff) params.set("difficulty", currentDiff);
    if (currentDom) params.set("domain", currentDom);
    if (currentLang) params.set("language", currentLang);
    if (currentSort) params.set("sort", currentSort);
    if (minStars > 0) params.set("min_stars", minStars);
    if (hasReadme) params.set("has_readme", "true");

    try {
      const res = await fetch(`/api/search?${params.toString()}`);
      if (!res.ok) throw new Error("Search request failed");
      const repos = await res.json();

      if (countEl) countEl.textContent = repos.length;
      if (queryDisplayText) queryDisplayText.textContent = currentQuery || "All Repositories";

      renderRepoCards(repos, stack, isListView);
      CompareManager.updateUI();
    } catch (err) {
      stack.innerHTML = `
        <div class="error-msg" style="grid-column: 1 / -1; text-align: center; padding: 40px;">
          <p>Failed to retrieve repository records. Please check the server connection.</p>
        </div>
      `;
    }
  }

  // Event Listeners
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      currentQuery = searchInput.value.trim();
      fetchResults();
    });
  }

  diffRadios.forEach((r) => {
    r.addEventListener("change", () => {
      currentDiff = r.value;
      fetchResults();
    });
  });

  domRadios.forEach((r) => {
    r.addEventListener("change", () => {
      currentDom = r.value;
      fetchResults();
    });
  });

  if (langSelect) {
    langSelect.addEventListener("change", () => {
      currentLang = langSelect.value;
      fetchResults();
    });
  }

  if (starsSlider) {
    starsSlider.addEventListener("input", () => {
      minStars = parseInt(starsSlider.value);
      if (starsVal) starsVal.textContent = minStars;
    });
    starsSlider.addEventListener("change", () => {
      fetchResults();
    });
  }

  if (readmeCheckbox) {
    readmeCheckbox.addEventListener("change", () => {
      hasReadme = readmeCheckbox.checked;
      fetchResults();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      currentSort = sortSelect.value;
      fetchResults();
    });
  }

  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", () => {
      currentDiff = "";
      currentDom = "";
      currentLang = "";
      minStars = 0;
      hasReadme = false;
      currentSort = "relevance";

      const defDiff = document.querySelector('input[name="filter-difficulty"][value=""]');
      if (defDiff) defDiff.checked = true;

      const defDom = document.querySelector('input[name="filter-domain"][value=""]');
      if (defDom) defDom.checked = true;

      if (langSelect) langSelect.value = "";
      if (starsSlider) {
        starsSlider.value = 0;
        if (starsVal) starsVal.textContent = 0;
      }
      if (readmeCheckbox) readmeCheckbox.checked = false;
      if (sortSelect) sortSelect.value = "relevance";

      fetchResults();
    });
  }

  // View Layout Buttons
  if (gridBtn && listBtn) {
    gridBtn.addEventListener("click", () => {
      isListView = false;
      gridBtn.classList.add("active");
      listBtn.classList.remove("active");
      fetchResults();
    });

    listBtn.addEventListener("click", () => {
      isListView = true;
      listBtn.classList.add("active");
      gridBtn.classList.remove("active");
      fetchResults();
    });
  }

  // Initial Load
  fetchResults();
});
