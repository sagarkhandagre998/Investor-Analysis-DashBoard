# scripts/unpivot_category_monthly.py
"""
Reads combined category monthly Excel (wide format) and
produces a clean long table:
  Date, Year, Month, Category, Registrations

Input expected:
  - file: data/category/category_monthly_raw.xlsx
  - one sheet with columns like: S.No, Vehicle Category, Jan-2021, Feb-2021, ..., Total

Output:
  - processed/category_monthly_clean.csv
  - processed/category_monthly_clean.xlsx
"""
import pandas as pd
from pathlib import Path
import re

INPATH = Path("data/category/category_monthly_raw.xlsx")
OUTCSV = Path("processed/category_monthly_clean.csv")
OUTXLSX = Path("processed/category_monthly_clean.xlsx")

def find_category_col(df):
    for c in df.columns:
        if 'category' in str(c).lower() or 'vehicle' in str(c).lower():
            return c
    raise ValueError("Could not find category column. Ensure a column name contains 'Category' or 'Vehicle'.")

def parse_date_from_colname(colname):
    # many dashboards use formats like "Jan-2021", "Jan 2021", "Jan-21", "2021 Jan"
    s = str(colname).strip()
    # try direct parse with pandas
    try:
        dt = pd.to_datetime(s, format="%b-%Y", errors='coerce')
        if pd.notna(dt):
            return dt
        dt = pd.to_datetime(s, format="%b %Y", errors='coerce')
        if pd.notna(dt):
            return dt
    except:
        pass
    # fallback: extract month name and year by regex
    m = re.search(r'([A-Za-z]{3,9})\s*[-]?\s*(\d{2,4})', s)
    if m:
        month = m.group(1)
        year = m.group(2)
        # convert two-digit year to 20xx if needed
        if len(year) == 2:
            year = "20" + year
        try:
            return pd.to_datetime(f"{month} {year}", format="%b %Y", errors='coerce')
        except:
            try:
                return pd.to_datetime(f"{month} {year}", format="%B %Y", errors='coerce')
            except:
                return pd.NaT
    # last resort: try parse generally
    dt = pd.to_datetime(s, errors='coerce')
    return dt

def main():
    if not INPATH.exists():
        print("ERROR: expected file at", INPATH.resolve())
        return
    df = pd.read_excel(INPATH)
    cat_col = find_category_col(df)
    # Identify month columns: all columns except serial numbers and category and 'Total'
    month_cols = [c for c in df.columns if c not in (cat_col,) and 'total' not in str(c).lower() and 's.no' not in str(c).lower() and 'sno' not in str(c).lower()]
    # Melt to long format
    long = df.melt(id_vars=[cat_col], value_vars=month_cols, var_name="MonthRaw", value_name="Registrations")
    long = long.rename(columns={cat_col: "Category"})
    # Parse MonthRaw to datetime
    long['Date'] = long['MonthRaw'].apply(parse_date_from_colname)
    # Drop rows where Date could not be parsed or Registrations NaN
    long = long.dropna(subset=['Date'])
    long['Year'] = long['Date'].dt.year
    long['Month'] = long['Date'].dt.month
    # Clean registrations to numeric
    long['Registrations'] = pd.to_numeric(long['Registrations'], errors='coerce').fillna(0).astype(int)
    # Sort
    long = long.sort_values(['Category','Date']).reset_index(drop=True)
    # Save
    OUTCSV.parent.mkdir(parents=True, exist_ok=True)
    long.to_csv(OUTCSV, index=False)
    long.to_excel(OUTXLSX, index=False)
    print("Saved:", OUTCSV.resolve())
    print("Sample:")
    print(long.head().to_string(index=False))

if __name__ == "__main__":
    main()
