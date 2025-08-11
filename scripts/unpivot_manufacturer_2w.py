# scripts/unpivot_manufacturer_2w.py
import pandas as pd
import glob
import os

# Path where your yearly 2W Excel files are stored
input_folder = r"G:\Projects\vahan-dashboard\data\manufacturers\2w"
output_file = r"G:\Projects\vahan-dashboard\processed\manufacturer_2w.csv"

all_data = []

# Loop through each file in the folder
for file in glob.glob(os.path.join(input_folder, "*.xlsx")):
    # Extract year from file name (e.g., '2w 2021.xlsx' -> 2021)
    year = os.path.basename(file).split()[1].split('.')[0]

    # Read Excel
    df = pd.read_excel(file)

    # Clean column names
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    # Melt the 2W categories into rows
    df_long = df.melt(
        id_vars=["Maker"],
        value_vars=["2WIC", "2WN", "2WT"],
        var_name="Category",
        value_name="Registrations"
    )

    # Add Year column
    df_long["Year"] = int(year)

    # Append to list
    all_data.append(df_long)

# Combine all years into one DataFrame
final_df = pd.concat(all_data, ignore_index=True)

# Save to CSV
os.makedirs(os.path.dirname(output_file), exist_ok=True)
final_df.to_csv(output_file, index=False)

print(f"✅ Saved: {output_file}")
print(final_df.head())
