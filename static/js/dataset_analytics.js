/**
 * dataset_analytics.js - Paginated & Searchable Dataset Browser
 */

document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.getElementById("dataset-table-body");
  const searchInput = document.getElementById("dataset-search-input");
  const prevBtn = document.getElementById("btn-prev-page");
  const nextBtn = document.getElementById("btn-next-page");
  const paginationInfo = document.getElementById("pagination-info");

  let currentPage = 1;
  let currentSearch = "";
  let totalPages = 1;

  async function loadDatasetPage() {
    if (!tableBody) return;

    tableBody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 30px;">
          <div class="spinner" style="width: 24px; height: 24px;"></div>
          <span style="color: var(--text-dim);">Loading dataset records...</span>
        </td>
      </tr>
    `;

    try {
      const res = await fetch(`/api/dataset/sample?page=${currentPage}&per_page=15&q=${encodeURIComponent(currentSearch)}`);
      const data = await res.json();

      totalPages = data.total_pages || 1;
      if (paginationInfo) {
        paginationInfo.textContent = `Showing page ${data.page} of ${totalPages} (${data.total.toLocaleString()} total)`;
      }

      if (prevBtn) prevBtn.disabled = currentPage <= 1;
      if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

      if (!data.rows || data.rows.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 30px; color: var(--text-dim);">No repositories matched your search query.</td></tr>`;
        return;
      }

      tableBody.innerHTML = data.rows
        .map((repo) => {
          const diffClass = (repo.difficulty || "intermediate").toLowerCase();
          const isComp = CompareManager.has(repo.id);

          return `
          <tr>
            <td><a href="/repo/${repo.id}" style="font-family: var(--font-mono); font-weight: 600; color: #fff;">${escapeHtml(repo.name)}</a></td>
            <td><span style="color: var(--text-dim); font-family: var(--font-mono); font-size: 0.8rem;">${escapeHtml(repo.owner)}</span></td>
            <td><span class="lang-badge">${escapeHtml(repo.language)}</span></td>
            <td>
              <span class="difficulty-badge difficulty-${diffClass}">
                ${diffClass === "beginner" ? "🟢 Beginner" : diffClass === "intermediate" ? "🟡 Intermediate" : "🔴 Advanced"}
              </span>
            </td>
            <td><span class="domain-badge">${escapeHtml(repo.domain || "General")}</span></td>
            <td>⭐ ${repo.stars.toLocaleString()}</td>
            <td>🍴 ${repo.forks.toLocaleString()}</td>
            <td>
              <div style="display: flex; gap: 6px;">
                <a href="/repo/${repo.id}" class="btn btn-sm btn-outline">View</a>
                <button type="button" class="btn-card-compare ${isComp ? "active" : ""}" data-repo-id="${repo.id}" data-repo-name="${escapeHtml(repo.name)}">
                  ${isComp ? "✓" : "+ Compare"}
                </button>
              </div>
            </td>
          </tr>
        `;
        })
        .join("");
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 30px; color: var(--danger);">Failed to load dataset records.</td></tr>`;
    }
  }

  // Search input with debounce
  let debounceTimeout;
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => {
        currentSearch = searchInput.value.trim();
        currentPage = 1;
        loadDatasetPage();
      }, 300);
    });
  }

  // Pagination buttons
  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        loadDatasetPage();
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      if (currentPage < totalPages) {
        currentPage++;
        loadDatasetPage();
      }
    });
  }

  loadDatasetPage();
});
