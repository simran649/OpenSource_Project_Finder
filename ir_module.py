import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Quietly download necessary dictionaries
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def preprocess(text):
    text = str(text).lower()
    words = word_tokenize(text)
    processed_words = []
    for word in words:
        if word.isalpha() and word not in stop_words:
            processed_words.append(lemmatizer.lemmatize(word))
    return " ".join(processed_words)

def initialize_ir(df):
    print("[IR] INFO: Building Smart Search Engine...")
    
    # Combine text columns to build the search index safely
    text_data = pd.Series("", index=df.index)
    possible_columns = ['name', 'repo_name', 'description', 'readme_preview', 'language', 'file_list']
    
    for col in possible_columns:
        if col in df.columns:
            text_data += df[col].astype(str) + " "
            
    processed_text = text_data.apply(preprocess)
    
    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    tfidf_matrix = vectorizer.fit_transform(processed_text)
    
    print("[IR] INFO: Smart Search Engine Ready!")
    return vectorizer, tfidf_matrix

def smart_search(query, df, vectorizer, tfidf_matrix, top_k=40):
    processed_query = preprocess(query)
    query_vector = vectorizer.transform([processed_query])
    
    similarity_scores = cosine_similarity(query_vector, tfidf_matrix)
    scores = similarity_scores.flatten()
    
    # Grab the top scoring indices
    top_indices = scores.argsort()[::-1][:top_k]
    
    results = []
    max_score = scores[top_indices[0]] if len(top_indices) > 0 and scores[top_indices[0]] > 0 else 1.0

    for index in top_indices:
        # Only return repos that have a match score above threshold
        if scores[index] > 0.015:
            repo_dict = df.iloc[index].to_dict()
            if 'repo_name' in repo_dict and 'name' not in repo_dict:
                repo_dict['name'] = repo_dict['repo_name']
            
            raw_sim = float(scores[index])
            normalized_pct = round((raw_sim / max_score) * 100, 1)
            repo_dict['similarity_score'] = round(raw_sim, 4)
            repo_dict['match_percentage'] = min(100, max(10, int(normalized_pct)))
            results.append(repo_dict)
            
    return results

def find_similar_repos(repo_id, df, tfidf_matrix, top_k=6):
    """
    Finds the most textually and semantically similar repositories to a given repo_id.
    """
    if repo_id not in df.index or tfidf_matrix is None:
        return []
    
    repo_vec = tfidf_matrix[repo_id]
    similarity_scores = cosine_similarity(repo_vec, tfidf_matrix).flatten()
    
    # Get top items excluding the repo itself
    top_indices = similarity_scores.argsort()[::-1]
    results = []
    for idx in top_indices:
        if idx == repo_id:
            continue
        if len(results) >= top_k:
            break
        if similarity_scores[idx] > 0.02:
            r = df.iloc[idx].to_dict()
            if 'repo_name' in r and 'name' not in r:
                r['name'] = r['repo_name']
            r['similarity_score'] = round(float(similarity_scores[idx]), 4)
            r['match_percentage'] = min(99, int(float(similarity_scores[idx]) * 100))
            results.append(r)
            
    return results