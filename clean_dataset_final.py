import pandas as pd

# --------------------------------------------------
# NUTRISCOPE - FINAL DATASET CLEANING
# --------------------------------------------------

file_path = r"D:\CHRIST\2T\python_dataset\archive\en.openfoodfacts.org.products.tsv"
output_path = r"D:\CHRIST\2T\python_dataset\archive\nutriscope_cleaned.csv"

# 16 original columns + 1 calculated energy column = 17 final columns
selected_columns = [
    "code",
    "product_name",
    "brands",
    "categories_en",
    "countries_en",
    "created_datetime",
    "energy_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "fiber_100g",
    "sodium_100g",
    "additives_n",
    "pnns_groups_1"
]

nutrient_columns = [
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "fiber_100g",
    "sodium_100g"
]

sampled_chunks = []
total_rows_read = 0
total_valid_rows = 0

print("Starting NutriScope dataset preparation...")
print("Reading the original TSV file in chunks of 50,000 rows.\n")

chunks = pd.read_csv(
    file_path,
    sep="\t",
    usecols=selected_columns,
    chunksize=50000,
    low_memory=False,
    dtype={"code": "string"}
)

for chunk_number, chunk in enumerate(chunks, start=1):

    total_rows_read += len(chunk)

    # Convert numerical fields safely
    numeric_columns = [
        "energy_100g",
        "fat_100g",
        "saturated-fat_100g",
        "carbohydrates_100g",
        "sugars_100g",
        "proteins_100g",
        "fiber_100g",
        "sodium_100g",
        "additives_n"
    ]

    for col in numeric_columns:
        chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

    # Convert product creation date
    chunk["created_datetime"] = pd.to_datetime(
        chunk["created_datetime"],
        errors="coerce",
        utc=True
    )

    # Remove records without a product name, valid date or energy value
    chunk = chunk.dropna(
        subset=["product_name", "created_datetime", "energy_100g"]
    )

    # Energy is in kJ per 100 g.
    # Retain zero values; remove negative or implausibly high values.
    chunk.loc[
        (chunk["energy_100g"] < 0) |
        (chunk["energy_100g"] > 4000),
        "energy_100g"
    ] = pd.NA

    chunk = chunk.dropna(subset=["energy_100g"])

    # Nutritional values are expressed per 100 g.
    # Values outside 0-100 are treated as invalid/missing.
    for col in nutrient_columns:
        chunk.loc[
            (chunk[col] < 0) | (chunk[col] > 100),
            col
        ] = pd.NA

    # Additive count must be non-negative.
    # Do not impose an arbitrary upper limit.
    chunk.loc[chunk["additives_n"] < 0, "additives_n"] = pd.NA

    # Fill missing categorical values with explicit labels
    categorical_columns = [
        "brands",
        "categories_en",
        "countries_en",
        "pnns_groups_1"
    ]

    for col in categorical_columns:
        chunk[col] = chunk[col].fillna("Unknown")

    total_valid_rows += len(chunk)

    # Take the same fraction from each chunk.
    # This keeps the sample approximately representative
    # across the complete source file.
    if len(chunk) > 0:
        sampled = chunk.sample(
            frac=0.25,
            random_state=42 + chunk_number
        )
        sampled_chunks.append(sampled)

    print(
        f"Processed chunk {chunk_number}: "
        f"{total_rows_read:,} source rows read"
    )

print("\nCombining sampled records...")

if not sampled_chunks:
    raise ValueError(
        "No valid records were found. Check the source dataset and columns."
    )

df = pd.concat(sampled_chunks, ignore_index=True)

# Select up to 50,000 records from the sampled candidates
if len(df) > 50000:
    df = df.sample(n=50000, random_state=42)

# Convert energy from kJ to kcal per 100 g
df["energy_kcal_100g"] = df["energy_100g"] / 4.184

# Arrange the final columns in a clear order
final_columns = [
    "code",
    "product_name",
    "brands",
    "categories_en",
    "countries_en",
    "created_datetime",
    "energy_100g",
    "energy_kcal_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "fiber_100g",
    "sodium_100g",
    "additives_n",
    "pnns_groups_1"
]

df = df[final_columns]

# Save the final dataset
df.to_csv(output_path, index=False)

# --------------------------------------------------
# FINAL DATASET REPORT
# --------------------------------------------------

print("\n" + "=" * 55)
print("NUTRISCOPE - FINAL DATASET REPORT")
print("=" * 55)

print(f"Total source records read: {total_rows_read:,}")
print(f"Valid records before sampling: {total_valid_rows:,}")
print(f"Final sampled records: {len(df):,}")
print(f"Total final columns: {len(df.columns)}")

print("\nFINAL COLUMN NAMES:")
for number, col in enumerate(df.columns, start=1):
    print(f"{number}. {col}")

print("\nMISSING VALUES:")
print(df.isnull().sum())

print("\nMISSING VALUE PERCENTAGES:")
print((df.isnull().mean() * 100).round(2))

print("\nENERGY STATISTICS (kcal per 100 g):")
print(df["energy_kcal_100g"].describe().round(2))

print("\nNUTRITIONAL SUMMARY:")
print(
    df[
        [
            "energy_kcal_100g",
            "fat_100g",
            "saturated-fat_100g",
            "carbohydrates_100g",
            "sugars_100g",
            "proteins_100g",
            "fiber_100g",
            "sodium_100g",
            "additives_n"
        ]
    ].describe().round(2)
)

print("\nFIRST FIVE RECORDS:")
print(df.head().to_string(index=False))

print("\nFINAL DATASET SAVED SUCCESSFULLY:")
print(output_path)
print("=" * 55)
