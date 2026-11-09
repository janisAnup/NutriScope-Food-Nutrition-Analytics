
import pandas as pd

file_path = r"D:\CHRIST\2T\python_dataset\archive\en.openfoodfacts.org.products.tsv"

# Columns we want to investigate
candidate_columns = [
    "quantity",
    "additives_n",
    "labels_en",
    "pnns_groups_1",
    "pnns_groups_2",
    "main_category_en",
    "origins",
    "packaging",
    "alcohol_100g",
    "fiber_100g",
    "sodium_100g",
    "cholesterol_100g",
    "vitamin-c_100g",
    "calcium_100g",
    "caffeine_100g"
]

total_records = 0
valid_counts = {col: 0 for col in candidate_columns}

# Read data in chunks
chunks = pd.read_csv(
    file_path,
    sep="\t",
    usecols=candidate_columns,
    chunksize=50000,
    low_memory=False
)

for chunk in chunks:
    total_records += len(chunk)

    for col in candidate_columns:
        valid_counts[col] += chunk[col].notna().sum()

# Create summary
results = []

for col in candidate_columns:
    valid = valid_counts[col]
    missing = total_records - valid
    missing_percentage = (missing / total_records) * 100

    results.append({
        "Column": col,
        "Available": valid,
        "Missing": missing,
        "Missing %": round(missing_percentage, 2)
    })

summary = pd.DataFrame(results)

summary = summary.sort_values(
    by="Missing %",
    ascending=True
)

print("\nCOLUMN AVAILABILITY REPORT")
print(summary.to_string(index=False))

print("\nTotal records:", total_records)
