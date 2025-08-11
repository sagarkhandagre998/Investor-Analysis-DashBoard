# scripts/unpivot_manufacturer_4w.py
import pandas as pd
import glob
import os

# Path where your yearly 4W Excel files are stored
input_folder = r"G:\Projects\vahan-dashboard\data\manufacturers\4W"
output_file = r"G:\Projects\vahan-dashboard\processed\manufacturer_4w.csv"

all_data = []

for file in glob.glob(os.path.join(input_folder, "*.xlsx")):
    # Extract year from file name (e.g., '4w 2021.xlsx' -> 2021)
    year = os.path.basename(file).split()[1].split('.')[0]

    # Read Excel
    df = pd.read_excel(file)

    # Clean column names
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    # Melt the 4W categories into rows
    df_long = df.melt(
        id_vars=["Maker"],
        value_vars=["4WIC", "LMV", "MMV", "HMV"],
        var_name="Category",
        value_name="Registrations"
    )

    # Add Year column
    df_long["Year"] = int(year)

    all_data.append(df_long)

# Combine all years into one DataFrame
final_df = pd.concat(all_data, ignore_index=True)

# Save to CSV
os.makedirs(os.path.dirname(output_file), exist_ok=True)
final_df.to_csv(output_file, index=False)

print(f"✅ Saved: {output_file}")
print(final_df.head())
