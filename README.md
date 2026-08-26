# 🔎 Open Source Project Finder

> An intelligent platform for discovering relevant open-source GitHub repositories based on user interests, skills, and search queries.

---

## 📌 About the Project

**Open Source Project Finder** is a project designed to help users discover open-source GitHub repositories that match their interests and skill level.

Instead of manually browsing through thousands of repositories, the system uses **Information Retrieval and Machine Learning techniques** to identify relevant projects and provide useful information about them.

The project combines:

- 🔍 Information Retrieval
- 🤖 Machine Learning
- 🌐 Flask Backend
- 🎨 Web Frontend
- 📊 GitHub Repository Metadata

---

## ✨ Key Features

- 🔎 Search for repositories using natural-language queries
- 📚 Rank repositories according to search relevance
- 🧹 Preprocess and clean repository data
- 🤖 Predict repository-related attributes using Machine Learning
- 🌐 Display results through a web interface
- 🔗 Provide direct GitHub repository links

---

## ⚙️ System Workflow

The overall system follows this workflow:

**User**

↓

**Search Query**

↓

**Text Preprocessing**

↓

**TF-IDF Vectorization**

↓

**Cosine Similarity**

↓

**Relevant Repositories**

↓

**Machine Learning**

↓

**Final Results**

↓

**Web Interface**

        


## 🔍 Information Retrieval

The Information Retrieval module allows users to search for repositories using text-based queries.

Repository information such as:

- Repository name
- Description
- README preview
- Programming language
- File information

is combined to create searchable repository text.

The text is processed using:

1. Tokenization
2. Stop-word removal
3. Lemmatization
4. TF-IDF vectorization
5. Cosine similarity

The repositories are then ranked according to their similarity to the user's search query.

## 🤖 Machine Learning

The Machine Learning module analyses repository characteristics and generates predictions that can help users understand the repositories they discover.

Repository metadata and engineered features are used for model training and prediction.

The trained models are stored as `.pkl` files and can be loaded by the application during execution.

---

## 📊 Dataset

The project uses a GitHub repository metadata dataset obtained from Kaggle.

### Original Dataset

- **Repositories:** 14,644
- **Attributes:** 25

The dataset contains information such as:

- Repository name
- Owner
- Description
- Stars
- Forks
- Watchers
- Contributors
- Programming language
- Open issues
- README information
- Repository files
- Repository activity

---

## 🧹 Dataset Preparation

The dataset was inspected and processed before being used by the other modules.

The preprocessing stage included:

- Dataset structure and data-type analysis
- Missing-value analysis
- Duplicate checking
- Handling missing values in important text fields
- Text cleaning
- Selection of relevant columns
- Duplicate repository checking using GitHub URLs
- Generation of a cleaned dataset

---

### Dataset Transformation

Original Dataset
14,644 repositories × 25 columns
              │
              ▼
        Data Inspection
              │
              ▼
       Data Preprocessing
              │
              ▼
      Relevant Columns
              │
              ▼
Cleaned Dataset
14,644 repositories × 22 columns

---

## 📊 Dataset Inspection

The check_data.py script was used to inspect the original dataset.

It checks:

- Dataset shape
- Column names
- Data types
- Sample records
- Missing values
- Duplicate rows

---

## 🧹 Dataset Preprocessing
The preprocess.py script performs the main preprocessing operations and generates the cleaned dataset used by the project.

---

## Project Structure

OpenSource_Project_Finder/
│
├── app.py
│
├── ir_module.py
├── search_engine.py
│
├── ml_engine.py
│
├── preprocess.py
├── check_data.py
│
├── dataset.csv
│
├── difficulty_model.pkl
├── domain_model.pkl
├── domain_vectorizer.pkl
├── scaler.pkl
│
├── static/
│   └── ...
│
├── templates/
│   └── ...
│
├── README.md
└── .gitignore
