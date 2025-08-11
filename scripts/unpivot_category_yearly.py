# scripts/unpivot_category_yearly.py
import pandas as pd
import os

raw_file = r"G:\Projects\vahan-dashboard\data\category\category_yearly.xlsx"
processed_file = r"G:\Projects\vahan-dashboard\processed\category_yearly_clean.csv"

df = pd.read_excel(raw_file)

# Drop any empty or total columns
df = df.dropna(how="all")
if "Total" in df.columns:
    df = df.drop(columns=["Total"])

# Reshape if needed (unpivot years into rows)
df_long = df.melt(id_vars=["Category"], var_name="Year", value_name="Registrations")

# Save cleaned file
df_long.to_csv(processed_file, index=False)
print(f"✅ Saved: {processed_file}")
print(df_long.head())
