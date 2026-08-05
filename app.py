from flask import Flask, request, jsonify
import joblib
import pandas as pd
import ir_module

app = Flask(__name__)

# ==========================================
# 1. LOAD DATA, IR ENGINE & ML MODELS
# ==========================================
try:
    # Includes the 'skip bad lines' fix for broken rows
    df = pd.read_csv('dataset.csv', engine='python', on_bad_lines='skip', quoting=3)
    df.fillna('', inplace=True)
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

# ==========================================
# 2. ROUTES
# ==========================================
@app.route('/')
def index():
    return jsonify({"message": "GitScout Backend API is running successfully!"})
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
        
    if df is None or ir_vectorizer is None:
        return jsonify({"error": "System not fully initialized."})

    results = ir_module.smart_search(query, df, ir_vectorizer, ir_matrix)

    for repo in results:
        if models_loaded:
            try:
                # Bulletproof helper to prevent math crashes
                def to_float(val):
                    try:
                        return float(val)
                    except:
                        return 0.0

                stars = to_float(repo.get("stars", 0))
                forks = to_float(repo.get("forks", 0))
                # Fixed the column name mismatch here!
                issues = to_float(repo.get("open_issues_count", 0))
                
                stats = [[stars, forks, issues]]
                scaled_stats = scaler.transform(stats)
                repo["Difficulty Level"] = difficulty_model.predict(scaled_stats)[0]
                
                desc = str(repo.get("description", ""))
                text_vec = domain_vectorizer.transform([desc])
                repo["Technical Domain"] = domain_model.predict(text_vec)[0]
            except Exception as e:
                print(f"⚠️ ML Error on a repo: {e}")
                repo["Difficulty Level"] = "Unknown"
                repo["Technical Domain"] = "Unknown"
        else:
            repo["Difficulty Level"] = "Model Not Loaded"
            repo["Technical Domain"] = "Model Not Loaded"

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)