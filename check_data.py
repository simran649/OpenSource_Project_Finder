import pandas as pd

df = pd.read_csv("data/archive/GitHub_repo_metadata.csv")

print("=" * 50)
print("dataset Shape")
print("=" * 50)
print(df.shape)

print("\n")

print("=" * 50)
print("Columns")
print("=" * 50)
print(df.columns)
print("\n")

print("=" * 50)
print("Data Types")
print("=" * 50)
print(df.dtypes)
print("\n")

print("=" * 50)
print("First Five Rows")
print("=" * 50)
print(df.head())
print("/n")

print("=" * 50)
print("Missing Values")
print("=" * 50)
print(df.isnull().sum())

print("=" * 50)
print("Duplicate Rows")
print("=" * 50)
print(df.duplicated().sum())
