/**
 * model_studio.js - Interactive Machine Learning Studio
 * Handles multi-model training, live metric dashboards, dynamic charts, hot-deployment, and sandbox inference.
 */

document.addEventListener("DOMContentLoaded", () => {
  // -----------------------------------------------------------------------
  // 1. TAB NAVIGATION
  // -----------------------------------------------------------------------
  const tabs = document.querySelectorAll(".studio-tab");
  const tabContents = document.querySelectorAll(".studio-tab-content");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tabContents.forEach((tc) => tc.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.dataset.tab;
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");
    });
  });

  // -----------------------------------------------------------------------
  // 2. DIFFICULTY TRAINER LOGIC
  // -----------------------------------------------------------------------
  const diffAlgoSelect = document.getElementById("diff-algo");
  const groupMaxDepth = document.getElementById("group-max-depth");
  const groupNEstimators = document.getElementById("group-n-estimators");

  const diffMaxDepth = document.getElementById("diff-max-depth");
  const diffMaxDepthVal = document.getElementById("diff-max-depth-val");

  const diffNEstimators = document.getElementById("diff-n-estimators");
  const diffNEstimatorsVal = document.getElementById("diff-n-estimators-val");

  const diffTestSize = document.getElementById("diff-test-size");
  const diffTestSizeVal = document.getElementById("diff-test-size-val");

  const trainDiffForm = document.getElementById("train-difficulty-form");
  const diffBtn = document.getElementById("btn-train-diff");
  const diffMetricsContainer = document.getElementById("diff-metrics-container");
  const diffDeployBox = document.getElementById("diff-deploy-box");
  const diffDeployAcc = document.getElementById("diff-deploy-acc");
  const btnDeployDiff = document.getElementById("btn-deploy-diff");
  const diffRunStatus = document.getElementById("diff-run-status");

  // Dynamic parameter visibility
  if (diffAlgoSelect) {
    diffAlgoSelect.addEventListener("change", () => {
      const val = diffAlgoSelect.value;
      if (val === "RandomForestClassifier" || val === "GradientBoostingClassifier") {
        if (groupNEstimators) groupNEstimators.style.display = "block";
        if (groupMaxDepth) groupMaxDepth.style.display = "block";
      } else if (val === "DecisionTreeClassifier") {
        if (groupNEstimators) groupNEstimators.style.display = "none";
        if (groupMaxDepth) groupMaxDepth.style.display = "block";
      } else {
        if (groupNEstimators) groupNEstimators.style.display = "none";
        if (groupMaxDepth) groupMaxDepth.style.display = "none";
      }
    });
  }

  // Slider value listeners
  if (diffMaxDepth && diffMaxDepthVal) {
    diffMaxDepth.addEventListener("input", () => (diffMaxDepthVal.textContent = diffMaxDepth.value));
  }
  if (diffNEstimators && diffNEstimatorsVal) {
    diffNEstimators.addEventListener("input", () => (diffNEstimatorsVal.textContent = diffNEstimators.value));
  }
  if (diffTestSize && diffTestSizeVal) {
    diffTestSize.addEventListener("input", () => (diffTestSizeVal.textContent = `${Math.round(diffTestSize.value * 100)}%`));
  }

  // Submit Difficulty Training
  if (trainDiffForm) {
    trainDiffForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const algo = diffAlgoSelect.value;
      const testSize = parseFloat(diffTestSize.value);
      const randomState = parseInt(document.getElementById("diff-random-state").value || 42);

      const params = {};
      if (algo === "DecisionTreeClassifier" || algo === "RandomForestClassifier" || algo === "GradientBoostingClassifier") {
        params.max_depth = parseInt(diffMaxDepth.value);
      }
      if (algo === "RandomForestClassifier" || algo === "GradientBoostingClassifier") {
        params.n_estimators = parseInt(diffNEstimators.value);
      }

      diffBtn.disabled = true;
      diffBtn.innerHTML = `<div class="spinner" style="width: 16px; height: 16px; margin: 0; display: inline-block;"></div> Training...`;
      diffRunStatus.textContent = "Fitting model & computing metrics...";
      diffMetricsContainer.innerHTML = `
        <div class="metrics-empty-state">
          <div class="spinner"></div>
          <p>Training ${algo} across features & computing cross-evaluation matrices...</p>
        </div>
      `;

      try {
        const res = await fetch("/api/train/difficulty", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ algorithm: algo, test_size: testSize, random_state: randomState, params }),
        });

        const data = await res.json();
        if (!data.success) throw new Error(data.error || "Training failed");

        renderDifficultyMetrics(data.result);
        diffRunStatus.textContent = `Completed in ${data.result.elapsed_seconds}s (${data.result.trained_at})`;

        if (diffDeployBox && diffDeployAcc) {
          diffDeployAcc.textContent = `${data.result.test_accuracy}%`;
          diffDeployBox.style.display = "flex";
        }

        showToast(`Difficulty Model trained successfully (${data.result.test_accuracy}% Accuracy)`, "success");
      } catch (err) {
        diffMetricsContainer.innerHTML = `<p class="error-msg" style="text-align: center; padding: 30px;">Error: ${escapeHtml(err.message)}</p>`;
        diffRunStatus.textContent = "Training Error";
        showToast(err.message, "error");
      } finally {
        diffBtn.disabled = false;
        diffBtn.innerHTML = `<span class="btn-icon">&#9654;</span> Train Difficulty Model`;
      }
    });
  }

  // Deploy Difficulty Model
  if (btnDeployDiff) {
    btnDeployDiff.addEventListener("click", async () => {
      btnDeployDiff.disabled = true;
      btnDeployDiff.textContent = "Deploying...";
      try {
        const res = await fetch("/api/train/activate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ difficulty: true, domain: false }),
        });
        const d = await res.json();
        if (!d.success) throw new Error(d.error);

        showToast("Difficulty model deployed and saved to disk (.pkl)!", "success");
        document.getElementById("active-diff-name").textContent = diffAlgoSelect.value;
        diffDeployBox.style.display = "none";
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        btnDeployDiff.disabled = false;
        btnDeployDiff.innerHTML = `<span>&#10003; Deploy & Activate Model</span>`;
      }
    });
  }

  // -----------------------------------------------------------------------
  // 3. DOMAIN NLP TRAINER LOGIC
  // -----------------------------------------------------------------------
  const domAlgoSelect = document.getElementById("dom-algo");
  const domMaxFeatures = document.getElementById("dom-max-features");
  const domMaxFeaturesVal = document.getElementById("dom-max-features-val");
  const domNgram = document.getElementById("dom-ngram");
  const domAlpha = document.getElementById("dom-alpha");
  const domAlphaVal = document.getElementById("dom-alpha-val");
  const domTestSize = document.getElementById("dom-test-size");
  const domTestSizeVal = document.getElementById("dom-test-size-val");

  const trainDomForm = document.getElementById("train-domain-form");
  const domBtn = document.getElementById("btn-train-dom");
  const domMetricsContainer = document.getElementById("dom-metrics-container");
  const domDeployBox = document.getElementById("dom-deploy-box");
  const domDeployAcc = document.getElementById("dom-deploy-acc");
  const btnDeployDom = document.getElementById("btn-deploy-dom");
  const domRunStatus = document.getElementById("dom-run-status");

  if (domMaxFeatures && domMaxFeaturesVal) {
    domMaxFeatures.addEventListener("input", () => (domMaxFeaturesVal.textContent = Number(domMaxFeatures.value).toLocaleString()));
  }
  if (domAlpha && domAlphaVal) {
    domAlpha.addEventListener("input", () => (domAlphaVal.textContent = domAlpha.value));
  }
  if (domTestSize && domTestSizeVal) {
    domTestSize.addEventListener("input", () => (domTestSizeVal.textContent = `${Math.round(domTestSize.value * 100)}%`));
  }

  // Submit Domain Training
  if (trainDomForm) {
    trainDomForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const algo = domAlgoSelect.value;
      const maxFeatures = parseInt(domMaxFeatures.value);
      const testSize = parseFloat(domTestSize.value);
      const randomState = 42;

      const params = {
        ngram_max: parseInt(domNgram.value),
        alpha: parseFloat(domAlpha.value),
      };

      domBtn.disabled = true;
      domBtn.innerHTML = `<div class="spinner" style="width: 16px; height: 16px; margin: 0; display: inline-block;"></div> Training NLP...`;
      domRunStatus.textContent = "Vectorizing text & fitting NLP classifier...";
      domMetricsContainer.innerHTML = `
        <div class="metrics-empty-state">
          <div class="spinner"></div>
          <p>Fitting TF-IDF vocabulary matrix and computing domain multi-class report...</p>
        </div>
      `;

      try {
        const res = await fetch("/api/train/domain", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ algorithm: algo, max_features: maxFeatures, test_size: testSize, random_state: randomState, params }),
        });

        const data = await res.json();
        if (!data.success) throw new Error(data.error || "Training failed");

        renderDomainMetrics(data.result);
        domRunStatus.textContent = `Completed in ${data.result.elapsed_seconds}s (${data.result.trained_at})`;

        if (domDeployBox && domDeployAcc) {
          domDeployAcc.textContent = `${data.result.test_accuracy}%`;
          domDeployBox.style.display = "flex";
        }

        showToast(`Domain NLP Model trained successfully (${data.result.test_accuracy}% Accuracy)`, "success");
      } catch (err) {
        domMetricsContainer.innerHTML = `<p class="error-msg" style="text-align: center; padding: 30px;">Error: ${escapeHtml(err.message)}</p>`;
        domRunStatus.textContent = "Training Error";
        showToast(err.message, "error");
      } finally {
        domBtn.disabled = false;
        domBtn.innerHTML = `<span class="btn-icon">&#9654;</span> Train Domain NLP Model`;
      }
    });
  }

  // Deploy Domain Model
  if (btnDeployDom) {
    btnDeployDom.addEventListener("click", async () => {
      btnDeployDom.disabled = true;
      btnDeployDom.textContent = "Deploying...";
      try {
        const res = await fetch("/api/train/activate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ difficulty: false, domain: true }),
        });
        const d = await res.json();
        if (!d.success) throw new Error(d.error);

        showToast("Domain NLP model deployed and saved to disk (.pkl)!", "success");
        document.getElementById("active-dom-name").textContent = domAlgoSelect.value;
        domDeployBox.style.display = "none";
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        btnDeployDom.disabled = false;
        btnDeployDom.innerHTML = `<span>&#10003; Deploy & Activate Model</span>`;
      }
    });
  }

  // -----------------------------------------------------------------------
  // 4. LIVE INFERENCE SANDBOX LOGIC
  // -----------------------------------------------------------------------
  const sbStars = document.getElementById("sb-stars");
  const sbStarsVal = document.getElementById("sb-stars-val");
  const sbForks = document.getElementById("sb-forks");
  const sbForksVal = document.getElementById("sb-forks-val");
  const sbIssues = document.getElementById("sb-issues");
  const sbIssuesVal = document.getElementById("sb-issues-val");
  const sbFiles = document.getElementById("sb-files");
  const sbFilesVal = document.getElementById("sb-files-val");

  if (sbStars && sbStarsVal) sbStars.addEventListener("input", () => (sbStarsVal.textContent = sbStars.value));
  if (sbForks && sbForksVal) sbForks.addEventListener("input", () => (sbForksVal.textContent = sbForks.value));
  if (sbIssues && sbIssuesVal) sbIssues.addEventListener("input", () => (sbIssuesVal.textContent = sbIssues.value));
  if (sbFiles && sbFilesVal) sbFiles.addEventListener("input", () => (sbFilesVal.textContent = sbFiles.value));

  const sandboxForm = document.getElementById("sandbox-form");
  const sbPredictBtn = document.getElementById("btn-sandbox-predict");
  const sbResDiff = document.getElementById("sb-res-diff");
  const sbResDom = document.getElementById("sb-res-dom");
  const sbDiffProbs = document.getElementById("sb-diff-probs");
  const sbDomProbs = document.getElementById("sb-dom-probs");

  async function runSandboxPrediction() {
    const payload = {
      repo_name: document.getElementById("sb-name").value,
      description: document.getElementById("sb-desc").value,
      readme_preview: document.getElementById("sb-readme").value,
      stars: parseFloat(sbStars.value),
      forks: parseFloat(sbForks.value),
      open_issues_count: parseFloat(sbIssues.value),
      file_count: parseFloat(sbFiles.value),
      contributors_count_page1: 2,
    };

    try {
      const res = await fetch("/api/model/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (sbResDiff) {
        sbResDiff.textContent = data.difficulty;
        sbResDiff.className = `pred-main-badge difficulty-${data.difficulty.toLowerCase()}`;
      }

      if (sbResDom) {
        sbResDom.textContent = data.domain;
      }

      // Confidence bars for Difficulty
      if (sbDiffProbs && data.difficulty_confidence) {
        sbDiffProbs.innerHTML = Object.entries(data.difficulty_confidence)
          .map(([lbl, pct]) => {
            const colorClass = lbl.includes("Beginner") ? "bg-emerald" : lbl.includes("Intermediate") ? "bg-amber" : "bg-danger";
            return `
            <div class="conf-bar-row">
              <span class="conf-name">${lbl}</span>
              <div class="conf-bar"><div class="conf-fill ${colorClass}" style="width: ${pct}%;"></div></div>
              <span class="conf-pct">${pct}%</span>
            </div>
          `;
          })
          .join("");
      }

      // Confidence bars for Domain
      if (sbDomProbs && data.domain_confidence) {
        sbDomProbs.innerHTML = Object.entries(data.domain_confidence)
          .map(([lbl, pct]) => `
            <div class="conf-bar-row">
              <span class="conf-name">${lbl}</span>
              <div class="conf-bar"><div class="conf-fill bg-indigo" style="width: ${pct}%;"></div></div>
              <span class="conf-pct">${pct}%</span>
            </div>
          `)
          .join("");
      }
    } catch (err) {
      console.error("Sandbox error:", err);
    }
  }

  if (sandboxForm) {
    sandboxForm.addEventListener("submit", (e) => {
      e.preventDefault();
      runSandboxPrediction();
    });
  }

  // -----------------------------------------------------------------------
  // 5. METRIC RENDERING HELPERS
  // -----------------------------------------------------------------------
  function renderDifficultyMetrics(result) {
    let html = `
      <div class="metrics-summary-grid">
        <div class="metric-tile">
          <div class="metric-tile-val highlight">${result.test_accuracy}%</div>
          <div class="metric-tile-lbl">Test Accuracy</div>
        </div>
        <div class="metric-tile">
          <div class="metric-tile-val">${result.train_accuracy}%</div>
          <div class="metric-tile-lbl">Train Accuracy</div>
        </div>
        <div class="metric-tile">
          <div class="metric-tile-val">${result.macro_f1}%</div>
          <div class="metric-tile-lbl">Macro F1 Score</div>
        </div>
        <div class="metric-tile">
          <div class="metric-tile-val">${result.test_samples}</div>
          <div class="metric-tile-lbl">Test Samples</div>
        </div>
      </div>
    `;

    // Confusion Matrix Heatmap
    if (result.confusion_matrix) {
      const labels = result.confusion_matrix.labels;
      const matrix = result.confusion_matrix.matrix;
      html += `
        <div class="cm-container">
          <div class="cm-title">📊 Confusion Matrix (Ground Truth vs Predicted Tier)</div>
          <table class="cm-table">
            <thead>
              <tr>
                <th>True \\ Pred</th>
                ${labels.map((l) => `<th>${l}</th>`).join("")}
              </tr>
            </thead>
            <tbody>
              ${matrix
                .map(
                  (row, rIdx) => `
                <tr>
                  <th>${labels[rIdx]}</th>
                  ${row
                    .map((val, cIdx) => {
                      const isDiagonal = rIdx === cIdx;
                      const bg = isDiagonal ? "rgba(16, 185, 129, 0.25)" : val > 0 ? "rgba(239, 68, 68, 0.15)" : "transparent";
                      return `<td class="cm-cell" style="background: ${bg}; color: ${isDiagonal ? "#34D399" : "#fff"};">${val}</td>`;
                    })
                    .join("")}
                </tr>
              `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    // Feature Importances
    if (result.feature_importances && result.feature_importances.length > 0) {
      const maxImp = Math.max(...result.feature_importances.map((f) => f.importance)) || 1;
      html += `
        <div class="feature-bars-container">
          <div class="cm-title">📈 Feature Importance Weights</div>
          ${result.feature_importances
            .map(
              (f) => `
            <div class="feat-bar-row">
              <span class="feat-name">${f.feature}</span>
              <div class="feat-track"><div class="feat-fill" style="width: ${(f.importance / maxImp) * 100}%;"></div></div>
              <span class="feat-val">${f.importance}</span>
            </div>
          `
            )
            .join("")}
        </div>
      `;
    }

    diffMetricsContainer.innerHTML = html;
  }

  function renderDomainMetrics(result) {
    let html = `
      <div class="metrics-summary-grid">
        <div class="metric-tile">
          <div class="metric-tile-val highlight">${result.test_accuracy}%</div>
          <div class="metric-tile-lbl">Test Accuracy</div>
        </div>
        <div class="metric-tile">
          <div class="metric-tile-val">${result.macro_f1}%</div>
          <div class="metric-tile-lbl">Macro F1 Score</div>
        </div>
        <div class="metric-tile">
          <div class="metric-tile-val">${result.max_features}</div>
          <div class="metric-tile-lbl">Vocabulary Size</div>
        </div>
        <div class="metric-tile">
          <div class="metric-tile-val">${result.test_samples}</div>
          <div class="metric-tile-lbl">Test Samples</div>
        </div>
      </div>
    `;

    // Classification Report Table
    if (result.class_metrics) {
      html += `
        <div class="cm-container">
          <div class="cm-title">📋 Per-Domain Classification Metrics</div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Domain Category</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1-Score</th>
                <th>Samples</th>
              </tr>
            </thead>
            <tbody>
              ${result.class_metrics
                .map(
                  (c) => `
                <tr>
                  <td><strong>${c.label}</strong></td>
                  <td>${(c.precision * 100).toFixed(1)}%</td>
                  <td>${(c.recall * 100).toFixed(1)}%</td>
                  <td><strong style="color: var(--emerald);">${(c.f1_score * 100).toFixed(1)}%</strong></td>
                  <td>${c.support}</td>
                </tr>
              `
                )
                .join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    // Top Keywords per Domain
    if (result.top_keywords) {
      html += `
        <div class="cm-container">
          <div class="cm-title">🏷️ Top Informative Vocabulary Keywords</div>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            ${Object.entries(result.top_keywords)
              .map(
                ([dom, kwList]) => `
              <div>
                <strong style="font-size: 0.85rem; color: #C7D2FE;">${dom}:</strong>
                <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
                  ${kwList.map((w) => `<span class="lang-badge" style="background: rgba(99,102,241,0.15); color: #fff;">${w}</span>`).join("")}
                </div>
              </div>
            `
              )
              .join("")}
          </div>
        </div>
      `;
    }

    domMetricsContainer.innerHTML = html;
  }
});
