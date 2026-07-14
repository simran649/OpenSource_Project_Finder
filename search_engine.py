import pandas as pd

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------
# Read the cleaned dataset
# ----------------------------

df = pd.read_csv("cleaned_github_repositories.csv")


# ----------------------------
# Combine useful text columns
# ----------------------------

df["text"] = (
    df["repo_name"] + " " +
    df["description"] + " " +
    df["readme_preview"] + " " +
    df["language"] + " " +
    df["file_list"]
)

# ----------------------------
# Create stop words and lemmatizer
# ----------------------------

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# ----------------------------
# Text preprocessing function
# ----------------------------

def preprocess(text):

    text = text.lower()

    words = word_tokenize(text)

    processed_words = []

    for word in words:

        if word.isalpha() and word not in stop_words:
            processed_words.append(
                lemmatizer.lemmatize(word)
            )

    return " ".join(processed_words)

# ----------------------------
# Preprocess all repositories
# ----------------------------

df["processed_text"] = df["text"].apply(preprocess)

# ----------------------------
# Create TF-IDF matrix
# ----------------------------

vectorizer = TfidfVectorizer()

tfidf_matrix = vectorizer.fit_transform(df["processed_text"])

print("TF-IDF Matrix Shape:", tfidf_matrix.shape)

# ----------------------------
# Take user query
# ----------------------------

query = input("\nEnter your search query: ")

# ----------------------------
# Preprocess the query
# ----------------------------

processed_query = preprocess(query)

# ----------------------------
# Convert query into TF-IDF vector
# ----------------------------

query_vector = vectorizer.transform([processed_query])

# ----------------------------
# Compute cosine similarity
# ----------------------------

similarity_scores = cosine_similarity(query_vector, tfidf_matrix)

# Get similarity scores as a 1D array
scores = similarity_scores.flatten()

# Get indices of repositories sorted by similarity (highest first)
top_indices = scores.argsort()[::-1][:5]

# Check if any repository actually matches

threshold = 0.05

if scores[top_indices[0]] < threshold:
    print("\nNo relevant repositories found for your search.")
else:
    print("\nTop 5 Matching Repositories:\n")

    max_score = scores[top_indices[0]]

    for index in top_indices:

        similarity = scores[index]

        # Rating based on relevance
        rating = (similarity / max_score) * 5
        star_icons = "⭐" * round(rating)

        print("Repository:", df.iloc[index]["repo_name"])
        print("Description:", df.iloc[index]["description"])
        print("Language:", df.iloc[index]["language"])
        print("Rating:", star_icons, f"({rating:.1f}/5)")
        print("GitHub URL:", df.iloc[index]["github_url"])
        print("Similarity Score:", round(similarity, 4))
        print("-" * 60)