
import pandas as pd

file_path = r"D:\CHRIST\2T\python_dataset\archive\en.openfoodfacts.org.products.tsv"

# Read only the first 10 records
df = pd.read_csv(
    file_path,
    sep="\t",
    compression=None,
    nrows=10,
    low_memory=False
)

columns = [
    "code",
    "product_name",
    "brands",
    "categories_en",
    "countries_en",
    "created_datetime",
    "energy_100g",
    "fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g"
]

print("\nDATASET SAMPLE:")
print(df[columns].to_string())

print("\nDATA TYPES:")
print(df[columns].dtypes)

print("\nMISSING VALUES:")
print(df[columns].isnull().sum())
