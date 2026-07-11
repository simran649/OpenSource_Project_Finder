import pandas as pd

df = pd.read_csv("data/archive/GitHub_repo_metadata.csv")

print("Dataset loaded successfully.")
print("Original shape:", df.shape)

df["description"] = df["description"].fillna("No description available")
df["readme_preview"] = df["readme_preview"].fillna("No README preview available")
df["language"] = df["language"].fillna("Unknown")
df["file_list"] = df["file_list"].fillna("No file list available")

print("\nMissing values handled.")

print("\nRemaining missing values:")
print(df.isnull().sum())

text_columns = ["repo_name", "description", "readme_preview", "language", "file_list"]

for column in text_columns:
    df[column] = df[column].astype(str).str.strip()

print("\nText columns cleaned.")

# Select columns useful for the project
selected_columns = [
    "repo_name",
    "owner",
    "github_url",
    "description",
    "stars",
    "forks",
    "watchers",
    "open_issues_count",
    "open_pulls_count_page1",
    "contributors_count_page1",
    "release_count_page1",
    "created_at",
    "updated_at",
    "pushed_at",
    "has_readme",
    "community_health_percentage",
    "workflow_count",
    "language",
    "languages_breakdown",
    "file_count",
    "file_list",
    "readme_preview",
]

df = df[selected_columns]

print("\nUseful columns selected.")
print("New shape:", df.shape)

# Remove duplicate repositories based on GitHub URL
df = df.drop_duplicates(subset="github_url")

print("Duplicate repositories removed.")
print("Shape after duplicate removal:", df.shape)

# Save the cleaned dataset
output_path = "data/cleaned_github_repositories.csv"

df.to_csv(output_path, index=False)

print("\nCleaned dataset saved successfully.")
print("Saved at:", output_path)

cleaned_df = pd.read_csv(output_path)

print("\n--- CLEANED DATASET VERIFICATION ---")
print("Final shape:", cleaned_df.shape)
print("Duplicate repository URLs:", cleaned_df["github_url"].duplicated().sum())

print("\nMissing values in important columns:")
print(
    cleaned_df[["description", "readme_preview", "language", "file_list"]]
    .isnull()
    .sum()
)
