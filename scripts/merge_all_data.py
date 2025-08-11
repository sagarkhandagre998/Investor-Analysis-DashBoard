# scripts/merge_all_data.py
import pandas as pd
import os

processed_folder = r"G:\Projects\vahan-dashboard\processed"

# Load category-wise data
category_monthly = pd.read_csv(os.path.join(processed_folder, "category_monthly_clean.csv"))
category_yearly = pd.read_csv(os.path.join(processed_folder, "category_yearly_clean.csv"))

# Load manufacturer-wise data
manufacturer_2w = pd.read_csv(os.path.join(processed_folder, "manufacturer_2w.csv"))
manufacturer_3w = pd.read_csv(os.path.join(processed_folder, "manufacturer_3w.csv"))
manufacturer_4w = pd.read_csv(os.path.join(processed_folder, "manufacturer_4w.csv"))

# Combine manufacturer datasets
manufacturer_all = pd.concat([manufacturer_2w, manufacturer_3w, manufacturer_4w], ignore_index=True)

# Save merged manufacturer dataset
manufacturer_all_file = os.path.join(processed_folder, "manufacturer_all.csv")
manufacturer_all.to_csv(manufacturer_all_file, index=False)

print(f"✅ Merged manufacturer data saved: {manufacturer_all_file}")
print(f"Manufacturers: {manufacturer_all['Maker'].nunique()} total makers")
print(manufacturer_all.head())

# Also save combined category files if needed
category_monthly.to_csv(os.path.join(processed_folder, "category_monthly_clean.csv"), index=False)
category_yearly.to_csv(os.path.join(processed_folder, "category_yearly_clean.csv"), index=False)

print("✅ Category files ready.")
