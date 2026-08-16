"""
ml_engine.py - Core Machine Learning Engine for Open Source Project Finder
Provides training, evaluation, inference, hot-reloading, and dataset analytics.
"""

import os
import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report

DIFFICULTY_FEATURES = [
    "stars", "forks", "open_issues_count", "contributors_count_page1",
    "file_count", "description_len", "readme_len"
]
DIFFICULTY_LABELS = {0: "Beginner", 1: "Intermediate", 2: "Advanced"}
DIFFICULTY_REVERSE = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}

DOMAINS = [
    "Web Development",
    "Machine Learning / Data Science",
    "Cybersecurity",
    "Mobile Apps / Game Dev",
    "General Software Engineering"
]

class MLEngine:
    def __init__(self, data_path="dataset.csv"):
        self.data_path = data_path
        self.df = None
        self.scaler = None
        self.difficulty_model = None
        self.domain_vectorizer = None
        self.domain_model = None
        self.models_loaded = False
        
        # Training state and cached metadata
        self.active_difficulty_meta = {}
        self.active_domain_meta = {}
        self.staged_difficulty = None
        self.staged_domain = None
        
        self.load_data()
        self.load_saved_models()

    def load_data(self):
        try:
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path, engine='python', on_bad_lines='skip')
                self.df.fillna('', inplace=True)
                self.df = self.df.reset_index(drop=True)
                self.df['repo_id'] = self.df.index
                
                # Precompute feature columns
                self.df['description_len'] = self.df['description'].astype(str).apply(len)
                self.df['readme_len'] = self.df['readme_preview'].astype(str).apply(len)
                for col in ['stars', 'forks', 'open_issues_count', 'contributors_count_page1', 'file_count', 'community_health_percentage', 'watchers', 'open_pulls_count_page1']:
                    if col in self.df.columns:
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
                    else:
                        self.df[col] = 0

                # Compute ground truth labels for training if missing
                self.df['difficulty_label'] = self.df.apply(self._compute_difficulty_grade, axis=1)
                self.df['domain_label'] = self.df.apply(self._compute_domain_label, axis=1)
                self.df['combined_text'] = (
                    self.df['repo_name'].astype(str) + " " +
                    self.df['description'].astype(str) + " " +
                    self.df['readme_preview'].astype(str)
                )
                print(f"[MLEngine] INFO: Dataset loaded with {len(self.df)} repositories.")
            else:
                print(f"[MLEngine] WARN: Dataset file not found at {self.data_path}")
        except Exception as e:
            print(f"[MLEngine] ERROR: Error loading dataset: {e}")
            self.df = None

    def _compute_difficulty_grade(self, row):
        points = 0
        stars = float(row.get('stars', 0))
        forks = float(row.get('forks', 0))
        file_count = float(row.get('file_count', 0))
        contributors = float(row.get('contributors_count_page1', 0))
        readme_len = float(row.get('readme_len', 0))
        
        if stars > 15 or forks > 5: points += 1
        if file_count > 15: points += 1
        if contributors > 2: points += 1
        if readme_len > 800: points += 1

        if points <= 1:
            return 0  # Beginner
        elif points <= 2:
            return 1  # Intermediate
        else:
            return 2  # Advanced

    def _compute_domain_label(self, row):
        text = (str(row.get('repo_name', '')) + " " + str(row.get('description', '')) + " " + str(row.get('readme_preview', ''))).lower()
        if any(w in text for w in ['learning', 'predict', 'tensor', 'ai', 'neural', 'scikit', 'model', 'regression', 'dataset', 'nlp', 'deep learning', 'pytorch', 'keras', 'opencv']):
            return "Machine Learning / Data Science"
        elif any(w in text for w in ['cyber', 'security', 'hack', 'crypto', 'exploit', 'password', 'auth', 'vulnerability', 'penetration', 'firewall']):
            return "Cybersecurity"
        elif any(w in text for w in ['django', 'flask', 'web', 'html', 'css', 'website', 'http', 'api', 'server', 'dash', 'fastapi', 'react', 'frontend', 'backend', 'vue']):
            return "Web Development"
        elif any(w in text for w in ['game', 'pygame', 'play', 'steam', 'arcade', 'engine', 'unity', 'android', 'ios', 'mobile', 'flutter']):
            return "Mobile Apps / Game Dev"
        else:
            return "General Software Engineering"

    def load_saved_models(self):
        try:
            if (os.path.exists('scaler.pkl') and 
                os.path.exists('difficulty_model.pkl') and 
                os.path.exists('domain_vectorizer.pkl') and 
                os.path.exists('domain_model.pkl')):
                self.scaler = joblib.load('scaler.pkl')
                self.difficulty_model = joblib.load('difficulty_model.pkl')
                self.domain_vectorizer = joblib.load('domain_vectorizer.pkl')
                self.domain_model = joblib.load('domain_model.pkl')
                self.models_loaded = True
                
                self.active_difficulty_meta = {
                    "algorithm": type(self.difficulty_model).__name__,
                    "status": "Active (Loaded from disk)",
                    "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "features": DIFFICULTY_FEATURES,
                    "target_classes": list(DIFFICULTY_LABELS.values())
                }
                self.active_domain_meta = {
                    "algorithm": type(self.domain_model).__name__,
                    "status": "Active (Loaded from disk)",
                    "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "target_classes": DOMAINS
                }
                print("[MLEngine] INFO: Pre-trained ML Models loaded successfully!")
            else:
                self.models_loaded = False
                print("[MLEngine] WARN: One or more .pkl model files missing.")
        except Exception as e:
            self.models_loaded = False
            print(f"[MLEngine] ERROR: Error loading saved models: {e}")

    # =========================================================================
    # 1. DIFFICULTY MODEL TRAINING PIPELINE
    # =========================================================================
    def train_difficulty_model(self, algorithm="DecisionTreeClassifier", params=None, test_size=0.2, random_state=42):
        if self.df is None or len(self.df) == 0:
            raise ValueError("Dataset is not loaded.")
        
        params = params or {}
        start_time = time.time()

        X = self.df[DIFFICULTY_FEATURES].copy()
        y = self.df['difficulty_label'].copy()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=float(test_size), random_state=int(random_state), stratify=y
        )

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Algorithm Selection
        if algorithm == "RandomForestClassifier":
            n_estimators = int(params.get("n_estimators", 100))
            max_depth = int(params.get("max_depth", 8)) if params.get("max_depth") else None
            model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=int(random_state))
        elif algorithm == "LogisticRegression":
            C = float(params.get("C", 1.0))
            model = LogisticRegression(C=C, max_iter=1000, random_state=int(random_state))
        elif algorithm == "KNeighborsClassifier":
            n_neighbors = int(params.get("n_neighbors", 5))
            model = KNeighborsClassifier(n_neighbors=n_neighbors)
        elif algorithm == "GradientBoostingClassifier":
            n_estimators = int(params.get("n_estimators", 80))
            learning_rate = float(params.get("learning_rate", 0.1))
            model = GradientBoostingClassifier(n_estimators=n_estimators, learning_rate=learning_rate, random_state=int(random_state))
        else: # Default DecisionTree
            max_depth = int(params.get("max_depth", 5)) if params.get("max_depth") else None
            model = DecisionTreeClassifier(max_depth=max_depth, random_state=int(random_state))

        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        train_pred = model.predict(X_train_scaled)

        elapsed = round(time.time() - start_time, 3)

        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, support = precision_recall_fscore_support(y_test, y_pred, average=None, labels=[0, 1, 2], zero_division=0)
        macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2]).tolist()

        # Extract Feature Importances if available
        feature_importances = []
        if hasattr(model, 'feature_importances_'):
            for feat, imp in zip(DIFFICULTY_FEATURES, model.feature_importances_):
                feature_importances.append({"feature": feat, "importance": round(float(imp), 4)})
            feature_importances = sorted(feature_importances, key=lambda x: x['importance'], reverse=True)
        elif hasattr(model, 'coef_'):
            mean_coefs = np.mean(np.abs(model.coef_), axis=0)
            for feat, imp in zip(DIFFICULTY_FEATURES, mean_coefs):
                feature_importances.append({"feature": feat, "importance": round(float(imp), 4)})
            feature_importances = sorted(feature_importances, key=lambda x: x['importance'], reverse=True)

        class_metrics = []
        for code, label in DIFFICULTY_LABELS.items():
            class_metrics.append({
                "code": code,
                "label": label,
                "precision": round(float(prec[code]), 4),
                "recall": round(float(rec[code]), 4),
                "f1_score": round(float(f1[code]), 4),
                "support": int(support[code])
            })

        staged_result = {
            "model_type": "difficulty",
            "algorithm": algorithm,
            "params": params,
            "test_size": test_size,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "train_accuracy": round(float(train_acc * 100), 2),
            "test_accuracy": round(float(test_acc * 100), 2),
            "macro_precision": round(float(macro_prec * 100), 2),
            "macro_recall": round(float(macro_rec * 100), 2),
            "macro_f1": round(float(macro_f1 * 100), 2),
            "elapsed_seconds": elapsed,
            "confusion_matrix": {
                "labels": ["Beginner", "Intermediate", "Advanced"],
                "matrix": cm
            },
            "class_metrics": class_metrics,
            "feature_importances": feature_importances,
            "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Stage artifacts in memory for activation
        self.staged_difficulty = {
            "model": model,
            "scaler": scaler,
            "meta": staged_result
        }

        return staged_result

    # =========================================================================
    # 2. DOMAIN NLP MODEL TRAINING PIPELINE
    # =========================================================================
    def train_domain_model(self, algorithm="MultinomialNB", params=None, max_features=5000, ngram_range=(1, 2), test_size=0.2, random_state=42):
        if self.df is None or len(self.df) == 0:
            raise ValueError("Dataset is not loaded.")

        params = params or {}
        start_time = time.time()

        X = self.df['combined_text'].copy()
        y = self.df['domain_label'].copy()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=float(test_size), random_state=int(random_state), stratify=y
        )

        ngram_max = int(params.get("ngram_max", 2))
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=int(max_features),
            ngram_range=(1, ngram_max)
        )
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        if algorithm == "SGDClassifier":
            alpha = float(params.get("alpha", 0.0001))
            model = SGDClassifier(loss='log_loss', alpha=alpha, random_state=int(random_state))
        elif algorithm == "LogisticRegression":
            C = float(params.get("C", 1.0))
            model = LogisticRegression(C=C, max_iter=1000, random_state=int(random_state))
        elif algorithm == "RandomForestClassifier":
            n_estimators = int(params.get("n_estimators", 80))
            model = RandomForestClassifier(n_estimators=n_estimators, random_state=int(random_state))
        else: # Default MultinomialNB
            alpha = float(params.get("alpha", 0.1))
            model = MultinomialNB(alpha=alpha)

        model.fit(X_train_vec, y_train)
        y_pred = model.predict(X_test_vec)
        train_pred = model.predict(X_train_vec)

        elapsed = round(time.time() - start_time, 3)

        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, y_pred)
        target_domains = sorted(list(set(y)))
        prec, rec, f1, support = precision_recall_fscore_support(y_test, y_pred, average=None, labels=target_domains, zero_division=0)
        macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
        cm = confusion_matrix(y_test, y_pred, labels=target_domains).tolist()

        class_metrics = []
        for i, dom in enumerate(target_domains):
            class_metrics.append({
                "label": dom,
                "precision": round(float(prec[i]), 4),
                "recall": round(float(rec[i]), 4),
                "f1_score": round(float(f1[i]), 4),
                "support": int(support[i])
            })

        # Top keywords per class if available
        top_keywords = {}
        if hasattr(model, 'feature_log_prob_'):
            vocab = np.array(vectorizer.get_feature_names_out())
            for i, dom in enumerate(model.classes_):
                top_indices = np.argsort(model.feature_log_prob_[i])[::-1][:8]
                top_keywords[dom] = vocab[top_indices].tolist()

        staged_result = {
            "model_type": "domain",
            "algorithm": algorithm,
            "params": params,
            "test_size": test_size,
            "max_features": max_features,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "train_accuracy": round(float(train_acc * 100), 2),
            "test_accuracy": round(float(test_acc * 100), 2),
            "macro_precision": round(float(macro_prec * 100), 2),
            "macro_recall": round(float(macro_rec * 100), 2),
            "macro_f1": round(float(macro_f1 * 100), 2),
            "elapsed_seconds": elapsed,
            "confusion_matrix": {
                "labels": target_domains,
                "matrix": cm
            },
            "class_metrics": class_metrics,
            "top_keywords": top_keywords,
            "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.staged_domain = {
            "model": model,
            "vectorizer": vectorizer,
            "meta": staged_result
        }

        return staged_result

    # =========================================================================
    # 3. HOT DEPLOYMENT & PERSISTENCE
    # =========================================================================
    def activate_staged_models(self, activate_difficulty=True, activate_domain=True):
        activated = []
        if activate_difficulty and self.staged_difficulty:
            self.difficulty_model = self.staged_difficulty["model"]
            self.scaler = self.staged_difficulty["scaler"]
            self.active_difficulty_meta = self.staged_difficulty["meta"]
            self.active_difficulty_meta["status"] = "Active (Live in-memory)"
            joblib.dump(self.difficulty_model, 'difficulty_model.pkl')
            joblib.dump(self.scaler, 'scaler.pkl')
            activated.append("Difficulty Classifier")
            
        if activate_domain and self.staged_domain:
            self.domain_model = self.staged_domain["model"]
            self.domain_vectorizer = self.staged_domain["vectorizer"]
            self.active_domain_meta = self.staged_domain["meta"]
            self.active_domain_meta["status"] = "Active (Live in-memory)"
            joblib.dump(self.domain_model, 'domain_model.pkl')
            joblib.dump(self.domain_vectorizer, 'domain_vectorizer.pkl')
            activated.append("Technical Domain Classifier")

        self.models_loaded = True
        return {
            "success": True,
            "activated": activated,
            "message": f"Successfully activated and saved: {', '.join(activated)}"
        }

    # =========================================================================
    # 4. SINGLE INFERENCE & PREDICTION SANDBOX
    # =========================================================================
    def predict_single(self, repo_data):
        result = {
            "difficulty": "Unknown",
            "difficulty_confidence": {},
            "domain": "Unknown",
            "domain_confidence": {}
        }
        
        # 1. Difficulty prediction
        if self.difficulty_model and self.scaler:
            try:
                row_dict = {
                    "stars": float(repo_data.get("stars", 0) or 0),
                    "forks": float(repo_data.get("forks", 0) or 0),
                    "open_issues_count": float(repo_data.get("open_issues_count", 0) or 0),
                    "contributors_count_page1": float(repo_data.get("contributors_count_page1", 1) or 1),
                    "file_count": float(repo_data.get("file_count", 5) or 5),
                    "description_len": len(str(repo_data.get("description", ""))),
                    "readme_len": len(str(repo_data.get("readme_preview", "")))
                }
                feature_df = pd.DataFrame([row_dict], columns=DIFFICULTY_FEATURES)
                scaled = self.scaler.transform(feature_df)
                diff_code = int(self.difficulty_model.predict(scaled)[0])
                result["difficulty"] = DIFFICULTY_LABELS.get(diff_code, "Unknown")
                
                if hasattr(self.difficulty_model, 'predict_proba'):
                    probs = self.difficulty_model.predict_proba(scaled)[0]
                    result["difficulty_confidence"] = {
                        DIFFICULTY_LABELS.get(i, f"Class {i}"): round(float(p) * 100, 1)
                        for i, p in enumerate(probs)
                    }
            except Exception as e:
                print(f"[MLEngine] WARN: Single diff prediction error: {e}")

        # 2. Domain prediction
        if self.domain_model and self.domain_vectorizer:
            try:
                text = f"{repo_data.get('repo_name', '')} {repo_data.get('description', '')} {repo_data.get('readme_preview', '')}"
                vec = self.domain_vectorizer.transform([text])
                pred_domain = self.domain_model.predict(vec)[0]
                result["domain"] = pred_domain

                if hasattr(self.domain_model, 'predict_proba'):
                    probs = self.domain_model.predict_proba(vec)[0]
                    classes = self.domain_model.classes_
                    result["domain_confidence"] = {
                        cls: round(float(probs[i]) * 100, 1)
                        for i, cls in enumerate(classes)
                    }
            except Exception as e:
                print(f"[MLEngine] WARN: Single domain prediction error: {e}")

        return result

    # =========================================================================
    # 5. ENRICH REPO DICT FOR SEARCH / DETAILS
    # =========================================================================
    def enrich_repo(self, repo):
        if not self.models_loaded:
            repo["Difficulty Level"] = "Model Not Loaded"
            repo["Technical Domain"] = "Model Not Loaded"
            return repo
        try:
            desc = str(repo.get("description", ""))
            readme = str(repo.get("readme_preview", ""))
            feature_row = {
                "stars": float(repo.get("stars", 0) or 0),
                "forks": float(repo.get("forks", 0) or 0),
                "open_issues_count": float(repo.get("open_issues_count", 0) or 0),
                "contributors_count_page1": float(repo.get("contributors_count_page1", 1) or 1),
                "file_count": float(repo.get("file_count", 5) or 5),
                "description_len": len(desc),
                "readme_len": len(readme)
            }
            feat_df = pd.DataFrame([feature_row], columns=DIFFICULTY_FEATURES)
            scaled = self.scaler.transform(feat_df)
            diff_code = int(self.difficulty_model.predict(scaled)[0])
            repo["Difficulty Level"] = DIFFICULTY_LABELS.get(diff_code, "Unknown")
            
            if hasattr(self.difficulty_model, 'predict_proba'):
                probs = self.difficulty_model.predict_proba(scaled)[0]
                repo["difficulty_confidence"] = round(float(probs[diff_code]) * 100, 1)

            domain_text = f"{repo.get('repo_name', '')} {desc} {readme}"
            text_vec = self.domain_vectorizer.transform([domain_text])
            repo["Technical Domain"] = self.domain_model.predict(text_vec)[0]
        except Exception as e:
            repo["Difficulty Level"] = "Unknown"
            repo["Technical Domain"] = "Unknown"
        return repo

    # =========================================================================
    # 6. DATASET ANALYTICS & STATS
    # =========================================================================
    def get_dataset_stats(self):
        if self.df is None:
            return {}
        
        total_repos = len(self.df)
        
        # Language counts
        lang_counts = self.df['language'].replace('', 'Unknown').value_counts().head(10).to_dict()
        
        # Difficulty breakdown
        diff_counts = {
            "Beginner": int((self.df['difficulty_label'] == 0).sum()),
            "Intermediate": int((self.df['difficulty_label'] == 1).sum()),
            "Advanced": int((self.df['difficulty_label'] == 2).sum()),
        }
        
        # Domain breakdown
        domain_counts = self.df['domain_label'].value_counts().to_dict()

        # Summary numbers
        avg_stars = round(float(self.df['stars'].mean()), 1)
        avg_forks = round(float(self.df['forks'].mean()), 1)
        avg_files = round(float(self.df['file_count'].mean()), 1)
        avg_health = round(float(self.df['community_health_percentage'].mean()), 1) if 'community_health_percentage' in self.df.columns else 65.0

        return {
            "total_repositories": total_repos,
            "languages": lang_counts,
            "difficulty_distribution": diff_counts,
            "domain_distribution": domain_counts,
            "averages": {
                "stars": avg_stars,
                "forks": avg_forks,
                "file_count": avg_files,
                "community_health": avg_health
            }
        }
