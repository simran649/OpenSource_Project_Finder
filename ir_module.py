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
    print("⏳ Building Smart Search Engine... (This may take a minute)")
    
    # Combine text columns to build the search index safely
    text_data = pd.Series("", index=df.index)
    possible_columns = ['name', 'repo_name', 'description', 'readme_preview', 'language', 'file_list']
    
    for col in possible_columns:
        if col in df.columns:
            text_data += df[col].astype(str) + " "
            
    processed_text = text_data.apply(preprocess)
    
    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    tfidf_matrix = vectorizer.fit_transform(processed_text)
    
    print("✅ Smart Search Engine Ready!")
    return vectorizer, tfidf_matrix

def smart_search(query, df, vectorizer, tfidf_matrix):
    processed_query = preprocess(query)
    query_vector = vectorizer.transform([processed_query])
    
    similarity_scores = cosine_similarity(query_vector, tfidf_matrix)
    scores = similarity_scores.flatten()
    
    # Grab the top 15 highest scoring indices
    top_indices = scores.argsort()[::-1][:15]
    
    results = []
    for index in top_indices:
        # Only return repos that have a match score above 0.02
        if scores[index] > 0.02:
            repo_dict = df.iloc[index].to_dict()
            # Standardize the name key for the frontend
            if 'repo_name' in repo_dict and 'name' not in repo_dict:
                repo_dict['name'] = repo_dict['repo_name']
            results.append(repo_dict)
            
    return results