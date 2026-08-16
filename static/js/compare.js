/**
 * compare.js - Repository Comparison Matrix Interactions
 */

document.addEventListener("DOMContentLoaded", () => {
  const removeButtons = document.querySelectorAll(".btn-remove-compare");

  removeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = parseInt(btn.dataset.id);
      CompareManager.remove(id);

      // Re-navigate to updated compare url or reload
      const remainingIds = CompareManager.getIds();
      if (remainingIds.length > 0) {
        window.location.href = `/compare?ids=${remainingIds.join(",")}`;
      } else {
        window.location.href = `/compare`;
      }
    });
  });
});
