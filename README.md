# OPEN SOURCE PROJECT FINDER

**An Information Retrieval and Machine Learning Project**

Open Source Project Finder is a system designed to help users discover relevant open-source GitHub repositories based on their interests and search queries.

The project uses **Information Retrieval techniques and Machine Learning** to search, rank, and analyse GitHub repositories.

---

## Project Workflow

User Search Query  
↓  
Text Preprocessing  
↓  
TF-IDF and Cosine Similarity  
↓  
Repository Ranking  
↓  
Difficulty Prediction  
↓  
Relevant Open Source Projects

---

## Dataset

The project uses a GitHub repository metadata dataset obtained from Kaggle.

### Original Dataset

- Repositories: 14,644
- Features: 25

The dataset contains repository metadata such as repository name, description, programming language, stars, forks, contributors, README content, issues, and repository activity information.

---

## Dataset Preparation

The dataset was analysed and cleaned before being used by the Information Retrieval and Machine Learning modules.

The following preprocessing steps were performed:

- Analysed dataset structure and data types.
- Checked missing values.
- Checked duplicate rows.
- Handled missing values in important text columns.
- Removed leading and trailing whitespace from text fields.
- Selected relevant repository features.
- Checked duplicate repositories using GitHub URLs.
- Generated a cleaned dataset for further processing.

### Final Dataset

- Repositories: 14,644
- Features: 22
- Duplicate repository URLs: 0
- Missing values in selected important text columns: 0

The cleaned dataset is generated as:

`data/cleaned_github_repositories.csv`

---

## Dataset Fields

| Field | Description |
| --- | --- |
| repo_name | Name of the GitHub repository |
| owner | Repository owner |
| github_url | GitHub repository URL |
| description | Repository description |
| stars | Number of stars |
| forks | Number of forks |
| watchers | Number of watchers |
| open_issues_count | Number of open issues |
| open_pulls_count_page1 | Number of open pull requests collected |
| contributors_count_page1 | Number of contributors collected |
| release_count_page1 | Number of releases collected |
| created_at | Repository creation date |
| updated_at | Repository last update date |
| pushed_at | Date of the latest code push |
| has_readme | Indicates whether a README exists |
| community_health_percentage | Repository community health score |
| workflow_count | Number of GitHub Actions workflows |
| language | Primary programming language |
| languages_breakdown | Programming languages used |
| file_count | Number of repository files collected |
| file_list | Repository file information |
| readme_preview | Preview of README content |

---

## Current Project Structure

```text
OpenSourceProjectFinder/
│
├── data/
│   ├── archive/
│   │   └── GitHub_repo_metadata.csv
│   │
│   └── cleaned_github_repositories.csv
│
├── check_data.py
├── preprocess.py
├── README.md
└── .gitignore
