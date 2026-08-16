from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import pandas as pd
from ml_engine import MLEngine
import ir_module

app = Flask(__name__)

# =========================================================================
# 1. INITIALIZE ML ENGINE & IR ENGINE
# =========================================================================
ml_engine = MLEngine(data_path="dataset.csv")

if ml_engine.df is not None:
    ir_vectorizer, ir_matrix = ir_module.initialize_ir(ml_engine.df)
else:
    ir_vectorizer, ir_matrix = None, None

def calculate_readiness_score(repo):
    """
    Computes a composite 'Contribution Readiness' score (0-100%)
    based on community health, readme availability, issues/stars ratio, and activity.
    """
    score = 40.0
    
    # Community health contribution (up to 30 pts)
    health = float(repo.get('community_health_percentage', 0) or 0)
    score += (health / 100.0) * 30.0
    
    # Has readme preview (15 pts)
    readme = str(repo.get('readme_preview', ''))
    if len(readme) > 200:
        score += 15.0
    elif len(readme) > 0:
        score += 8.0
        
    # Open issues & stars balance (15 pts)
    stars = float(repo.get('stars', 0) or 0)
    issues = float(repo.get('open_issues_count', 0) or 0)
    if stars > 10:
        score += 10.0
    if issues > 0 and issues < 500:
        score += 5.0

    return min(98, max(25, int(score)))

def normalize_repo(repo):
    """
    Converts a dataset row into the standardized shape expected by the frontend.
    """
    difficulty = str(repo.get("Difficulty Level", "Unknown"))
    domain = str(repo.get("Technical Domain", ""))

    topics = []
    if domain and domain not in ("Unknown", "Model Not Loaded"):
        topics.append(domain)
    lang = repo.get("language", "")
    if lang:
        topics.append(str(lang))

    stars = int(float(repo.get("stars", 0) or 0))
    forks = int(float(repo.get("forks", 0) or 0))
    contributors = int(float(repo.get("contributors_count_page1", 1) or 1))
    open_issues = int(float(repo.get("open_issues_count", 0) or 0))
    watchers = int(float(repo.get("watchers", 0) or 0))
    file_count = int(float(repo.get("file_count", 0) or 0))
    health = int(float(repo.get("community_health_percentage", 65) or 65))
    readiness = calculate_readiness_score(repo)

    return {
        "id": int(repo.get("repo_id", 0)),
        "name": str(repo.get("repo_name") or repo.get("name") or "Unknown"),
        "owner": str(repo.get("owner", "")),
        "description": str(repo.get("description", "") or "No description available."),
        "topics": topics,
        "language": str(repo.get("language", "Unknown") or "Unknown"),
        "stars": stars,
        "forks": forks,
        "contributors": contributors,
        "open_issues": open_issues,
        "watchers": watchers,
        "file_count": file_count,
        "community_health": health,
        "readiness_score": readiness,
        "difficulty": difficulty,
        "difficulty_confidence": repo.get("difficulty_confidence"),
        "domain": domain,
        "match_percentage": repo.get("match_percentage", None),
        "similarity_score": repo.get("similarity_score", None),
        "readme_summary": str(repo.get("readme_preview", "") or "No README preview available."),
        "github_url": str(repo.get("github_url", "")),
    }

# =========================================================================
# 2. PAGE ROUTES
# =========================================================================
@app.route('/')
def home():
    languages = []
    total_count = 0
    domains = [
        "Web Development",
        "Machine Learning / Data Science",
        "Cybersecurity",
        "Mobile Apps / Game Dev",
        "General Software Engineering"
    ]
    if ml_engine.df is not None:
        languages = sorted({str(l).strip() for l in ml_engine.df['language'].unique() if str(l).strip() and str(l) != 'nan'})
        total_count = len(ml_engine.df)
    return render_template(
        'index.html',
        languages=languages,
        domains=domains,
        total_count=total_count,
        models_loaded=ml_engine.models_loaded
    )

@app.route('/results')
def results_page():
    query = request.args.get('q', '')
    language = request.args.get('language', '')
    difficulty = request.args.get('difficulty', '')
    domain = request.args.get('domain', '')
    sort_by = request.args.get('sort', 'relevance')
    return render_template(
        'results.html',
        query=query,
        language=language,
        difficulty=difficulty,
        domain=domain,
        sort_by=sort_by
    )

@app.route('/repo/<int:repo_id>')
def repo_details(repo_id):
    repo = None
    similar_repos = []
    if ml_engine.df is not None and repo_id in ml_engine.df.index:
        raw = ml_engine.df.iloc[repo_id].to_dict()
        ml_engine.enrich_repo(raw)
        repo = normalize_repo(raw)
        
        # Get similar repos
        if ir_matrix is not None:
            raw_similar = ir_module.find_similar_repos(repo_id, ml_engine.df, ir_matrix, top_k=4)
            for s in raw_similar:
                ml_engine.enrich_repo(s)
                similar_repos.append(normalize_repo(s))

    return render_template('details.html', repo=repo, similar_repos=similar_repos)

@app.route('/model-studio')
def model_studio():
    return render_template(
        'model_studio.html',
        models_loaded=ml_engine.models_loaded,
        active_diff=ml_engine.active_difficulty_meta,
        active_dom=ml_engine.active_domain_meta
    )

@app.route('/dataset')
def dataset_explorer():
    stats = ml_engine.get_dataset_stats()
    return render_template('dataset_analytics.html', stats=stats)

@app.route('/compare')
def compare_page():
    ids_str = request.args.get('ids', '')
    repos = []
    if ids_str and ml_engine.df is not None:
        try:
            ids = [int(i.strip()) for i in ids_str.split(',') if i.strip().isdigit()]
            for rid in ids[:5]:
                if rid in ml_engine.df.index:
                    raw = ml_engine.df.iloc[rid].to_dict()
                    ml_engine.enrich_repo(raw)
                    repos.append(normalize_repo(raw))
        except Exception:
            pass
    return render_template('compare.html', repos=repos, ids_str=ids_str)

# =========================================================================
# 3. API ROUTES (SEARCH, FILTERING, DISCOVERY)
# =========================================================================
@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', '').strip()
    language = request.args.get('language', '').strip().lower()
    difficulty = request.args.get('difficulty', '').strip().lower()
    domain = request.args.get('domain', '').strip().lower()
    sort_by = request.args.get('sort', 'relevance').strip()
    min_stars = int(request.args.get('min_stars', 0) or 0)
    has_readme = request.args.get('has_readme', '').strip().lower()

    if ml_engine.df is None:
        return jsonify({"error": "Dataset not loaded."}), 500

    raw_candidates = []

    if query and ir_vectorizer is not None and ir_matrix is not None:
        raw_candidates = ir_module.smart_search(query, ml_engine.df, ir_vectorizer, ir_matrix, top_k=60)
    else:
        # Fallback to top repositories
        sample_df = ml_engine.df.head(60)
        for _, row in sample_df.iterrows():
            r = row.to_dict()
            r['match_percentage'] = 100
            raw_candidates.append(r)

    normalized = []
    for raw in raw_candidates:
        ml_engine.enrich_repo(raw)
        repo = normalize_repo(raw)

        # Apply Filters
        if language and repo['language'].lower() != language:
            continue
        if difficulty and repo['difficulty'].lower() != difficulty:
            continue
        if domain and domain not in repo['domain'].lower():
            continue
        if repo['stars'] < min_stars:
            continue
        if has_readme == 'true' and (not repo['readme_summary'] or repo['readme_summary'] == 'No README preview available.'):
            continue

        normalized.append(repo)

    # Sorting
    if sort_by == 'stars':
        normalized.sort(key=lambda x: x['stars'], reverse=True)
    elif sort_by == 'forks':
        normalized.sort(key=lambda x: x['forks'], reverse=True)
    elif sort_by == 'health':
        normalized.sort(key=lambda x: x['community_health'], reverse=True)
    elif sort_by == 'readiness':
        normalized.sort(key=lambda x: x['readiness_score'], reverse=True)

    return jsonify(normalized)

@app.route('/api/repo/<int:repo_id>')
def api_repo_details(repo_id):
    if ml_engine.df is None:
        return jsonify({"error": "Dataset not loaded."}), 500
    if repo_id not in ml_engine.df.index:
        return jsonify({"error": "Repository not found"}), 404
    raw = ml_engine.df.iloc[repo_id].to_dict()
    ml_engine.enrich_repo(raw)
    return jsonify(normalize_repo(raw))

@app.route('/api/repo/similar/<int:repo_id>')
def api_repo_similar(repo_id):
    if ml_engine.df is None or ir_matrix is None:
        return jsonify([])
    raw_similar = ir_module.find_similar_repos(repo_id, ml_engine.df, ir_matrix, top_k=6)
    results = []
    for s in raw_similar:
        ml_engine.enrich_repo(s)
        results.append(normalize_repo(s))
    return jsonify(results)

@app.route('/api/skill-match', methods=['POST'])
def api_skill_match():
    if ml_engine.df is None:
        return jsonify([])

    payload = request.get_json(force=True) or {}
    languages = [l.lower().strip() for l in payload.get('languages', []) if l.strip()]
    level = payload.get('level', '').strip().lower()
    domain = payload.get('domain', '').strip().lower()

    matches = ml_engine.df.copy()
    if languages:
        matches = matches[matches['language'].astype(str).str.lower().isin(languages)]

    results = []
    # Sample up to 60 candidates and filter by enriched ML attributes
    for _, row in matches.head(60).iterrows():
        raw = row.to_dict()
        ml_engine.enrich_repo(raw)
        
        if level and str(raw.get("Difficulty Level", "")).lower() != level:
            continue
        if domain and domain not in str(raw.get("Technical Domain", "")).lower():
            continue
            
        repo = normalize_repo(raw)
        results.append(repo)

    return jsonify(results)

# =========================================================================
# 4. API ROUTES (MACHINE LEARNING STUDIO & TRAINING)
# =========================================================================
@app.route('/api/train/difficulty', methods=['POST'])
def api_train_difficulty():
    try:
        data = request.get_json(force=True) or {}
        algorithm = data.get('algorithm', 'DecisionTreeClassifier')
        test_size = float(data.get('test_size', 0.2))
        random_state = int(data.get('random_state', 42))
        params = data.get('params', {})

        result = ml_engine.train_difficulty_model(
            algorithm=algorithm,
            params=params,
            test_size=test_size,
            random_state=random_state
        )
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/train/domain', methods=['POST'])
def api_train_domain():
    try:
        data = request.get_json(force=True) or {}
        algorithm = data.get('algorithm', 'MultinomialNB')
        max_features = int(data.get('max_features', 5000))
        test_size = float(data.get('test_size', 0.2))
        random_state = int(data.get('random_state', 42))
        params = data.get('params', {})

        result = ml_engine.train_domain_model(
            algorithm=algorithm,
            params=params,
            max_features=max_features,
            test_size=test_size,
            random_state=random_state
        )
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/train/activate', methods=['POST'])
def api_train_activate():
    try:
        data = request.get_json(force=True) or {}
        act_diff = data.get('difficulty', True)
        act_dom = data.get('domain', True)

        res = ml_engine.activate_staged_models(
            activate_difficulty=act_diff,
            activate_domain=act_dom
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/model/status', methods=['GET'])
def api_model_status():
    return jsonify({
        "models_loaded": ml_engine.models_loaded,
        "difficulty_model": ml_engine.active_difficulty_meta,
        "domain_model": ml_engine.active_domain_meta,
        "staged_difficulty": ml_engine.staged_difficulty["meta"] if ml_engine.staged_difficulty else None,
        "staged_domain": ml_engine.staged_domain["meta"] if ml_engine.staged_domain else None
    })

@app.route('/api/model/predict', methods=['POST'])
def api_model_predict():
    payload = request.get_json(force=True) or {}
    pred = ml_engine.predict_single(payload)
    return jsonify(pred)

@app.route('/api/dataset/stats', methods=['GET'])
def api_dataset_stats():
    stats = ml_engine.get_dataset_stats()
    return jsonify(stats)

@app.route('/api/dataset/sample', methods=['GET'])
def api_dataset_sample():
    if ml_engine.df is None:
        return jsonify({"total": 0, "rows": []})
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('q', '').strip().lower()

    filtered = ml_engine.df
    if search:
        mask = (
            filtered['repo_name'].astype(str).str.lower().str.contains(search) |
            filtered['description'].astype(str).str.lower().str.contains(search) |
            filtered['language'].astype(str).str.lower().str.contains(search)
        )
        filtered = filtered[mask]

    total = len(filtered)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    slice_df = filtered.iloc[start_idx:end_idx]

    rows = []
    for _, row in slice_df.iterrows():
        raw = row.to_dict()
        ml_engine.enrich_repo(raw)
        rows.append(normalize_repo(raw))

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "rows": rows
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
