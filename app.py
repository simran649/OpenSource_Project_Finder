from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
import ir_module

app = Flask(__name__)

# ==========================================
# 1. LOAD DATA, IR ENGINE & ML MODELS
#    (this part is basically Member 4's original code, untouched)
# ==========================================
try:
    # NOTE: the original code had quoting=3 (QUOTE_NONE) here, which broke
    # column alignment on any row where description/file_list/readme_preview
    # contained a comma (very common). Removed so real quoted CSV fields
    # parse correctly.
    df = pd.read_csv('dataset.csv', engine='python', on_bad_lines='skip')
    df.fillna('', inplace=True)
    # give every row a stable row-number id so the frontend can link
    # to /repo/<id> for a details page
    df = df.reset_index(drop=True)
    df['repo_id'] = df.index
    print(f"✅ Dataset loaded! Found {len(df)} repositories.")

    ir_vectorizer, ir_matrix = ir_module.initialize_ir(df)
except Exception as e:
    df = None
    ir_vectorizer, ir_matrix = None, None
    print(f"⚠️ THE REAL ERROR IS: {e}")

try:
    scaler = joblib.load('scaler.pkl')
    difficulty_model = joblib.load('difficulty_model.pkl')
    domain_vectorizer = joblib.load('domain_vectorizer.pkl')
    domain_model = joblib.load('domain_model.pkl')
    models_loaded = True
    print("✅ ML Models loaded successfully!")
except Exception as e:
    models_loaded = False
    print("⚠️ Error loading ML Models (.pkl files missing).")


def to_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0


DIFFICULTY_FEATURES = [
    "stars", "forks", "open_issues_count", "contributors_count_page1",
    "file_count", "description_len", "readme_len",
]
DIFFICULTY_LABELS = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}


def enrich_with_ml(repo):
    """
    Adds 'Difficulty Level' and 'Technical Domain' to a repo dict, in place.

    IMPORTANT: the difficulty_model.pkl was trained (see ML.ipynb) on exactly
    these 7 numeric features, in this order:
        stars, forks, open_issues_count, contributors_count_page1,
        file_count, description_len, readme_len
    and predicts an integer 0/1/2 (Beginner/Intermediate/Advanced) —
    NOT a string. The domain_model.pkl was trained on the combined text
    "repo_name + description + readme_preview", not description alone.
    """
    if not models_loaded:
        repo["Difficulty Level"] = "Model Not Loaded"
        repo["Technical Domain"] = "Model Not Loaded"
        return repo
    try:
        desc = str(repo.get("description", ""))
        readme = str(repo.get("readme_preview", ""))

        feature_row = {
            "stars": to_float(repo.get("stars", 0)),
            "forks": to_float(repo.get("forks", 0)),
            "open_issues_count": to_float(repo.get("open_issues_count", 0)),
            "contributors_count_page1": to_float(repo.get("contributors_count_page1", 0)),
            "file_count": to_float(repo.get("file_count", 0)),
            "description_len": len(desc),
            "readme_len": len(readme),
        }
        feature_df = pd.DataFrame([feature_row], columns=DIFFICULTY_FEATURES)
        scaled_stats = scaler.transform(feature_df)
        diff_code = int(difficulty_model.predict(scaled_stats)[0])
        repo["Difficulty Level"] = DIFFICULTY_LABELS.get(diff_code, "Unknown")

        domain_text = f"{repo.get('repo_name', '')} {desc} {readme}"
        text_vec = domain_vectorizer.transform([domain_text])
        repo["Technical Domain"] = domain_model.predict(text_vec)[0]
    except Exception as e:
        print(f"⚠️ ML Error on a repo: {e}")
        repo["Difficulty Level"] = "Unknown"
        repo["Technical Domain"] = "Unknown"
    return repo


def normalize_repo(repo):
    """
    Converts a raw dataset row (dict) into the shape the frontend
    (main.js / results.js / templates) expects to render a card.
    This is the ONLY translation layer between your real data's
    column names and the UI — change this if column names change.
    """
    difficulty = str(repo.get("Difficulty Level", "Unknown"))
    domain = str(repo.get("Technical Domain", ""))

    topics = []
    if domain and domain not in ("Unknown", "Model Not Loaded"):
        topics.append(domain)
    lang = repo.get("language", "")
    if lang:
        topics.append(str(lang))

    return {
        "id": repo.get("repo_id", 0),
        "name": repo.get("repo_name") or repo.get("name") or "Unknown",
        "owner": repo.get("owner", ""),
        "description": repo.get("description", "") or "No description available.",
        "topics": topics,
        "language": repo.get("language", "Unknown") or "Unknown",
        "stars": int(to_float(repo.get("stars", 0))),
        "forks": int(to_float(repo.get("forks", 0))),
        "contributors": int(to_float(repo.get("contributors_count_page1", 0))),
        "open_issues": int(to_float(repo.get("open_issues_count", 0))),
        "difficulty": difficulty,
        "readme_summary": repo.get("readme_preview", "") or "No README preview available.",
        "github_url": repo.get("github_url", ""),
    }


# ==========================================
# 2. PAGE ROUTES (render actual HTML pages)
# ==========================================
@app.route('/')
def home():
    languages = []
    if df is not None:
        languages = sorted({str(l) for l in df['language'].unique() if str(l).strip()})
    return render_template('index.html', languages=languages)


@app.route('/results')
def results_page():
    query = request.args.get('q', '')
    return render_template('results.html', query=query)


@app.route('/repo/<int:repo_id>')
def repo_details(repo_id):
    repo = None
    if df is not None:
        match = df[df['repo_id'] == repo_id]
        if not match.empty:
            raw = match.iloc[0].to_dict()
            enrich_with_ml(raw)
            repo = normalize_repo(raw)
    return render_template('details.html', repo=repo)


# ==========================================
# 3. API ROUTES (JSON, used by main.js / results.js)
# ==========================================
@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', '')

    if not query:
        return jsonify([])

    if df is None or ir_vectorizer is None:
        return jsonify({"error": "System not fully initialized."}), 500

    raw_results = ir_module.smart_search(query, df, ir_vectorizer, ir_matrix)

    normalized = []
    for repo in raw_results:
        enrich_with_ml(repo)
        normalized.append(normalize_repo(repo))

    return jsonify(normalized)


@app.route('/api/repo/<int:repo_id>')
def api_repo_details(repo_id):
    if df is None:
        return jsonify({"error": "System not fully initialized."}), 500
    match = df[df['repo_id'] == repo_id]
    if match.empty:
        return jsonify({"error": "Repository not found"}), 404
    raw = match.iloc[0].to_dict()
    enrich_with_ml(raw)
    return jsonify(normalize_repo(raw))


@app.route('/api/skill-match', methods=['POST'])
def api_skill_match():
    if df is None:
        return jsonify([])

    payload = request.get_json(force=True) or {}
    languages = [l.lower() for l in payload.get('languages', [])]
    level = payload.get('level', '').lower()

    matches = df
    if languages:
        matches = matches[matches['language'].str.lower().isin(languages)]

    results = []
    # cap at 30 rows so we're not running the ML model on the whole dataset
    for _, row in matches.head(30).iterrows():
        raw = row.to_dict()
        enrich_with_ml(raw)
        if level and str(raw.get("Difficulty Level", "")).lower() != level:
            continue
        results.append(normalize_repo(raw))

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
