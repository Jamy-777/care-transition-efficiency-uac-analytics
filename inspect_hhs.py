import pandas as pd

df_raw = pd.read_csv("HHS_Unaccompanied_Alien_Children_Program.csv")
print("Raw columns:", df_raw.columns)
print("Raw head:")
print(df_raw.head())
print("Raw hhs care non-null count:", df_raw['Children in HHS Care'].notnull().sum())
print("Raw hhs care sample values:", df_raw['Children in HHS Care'].dropna().head(10).tolist())

df_clean = pd.read_csv("cleaned_hhs_uac_data.csv")
print("Cleaned summary of hhs_care:")
print(df_clean['hhs_care'].describe())
print("Cleaned head:")
print(df_clean[['Date', 'apprehensions', 'cbp_custody', 'transfers_to_hhs', 'hhs_care', 'discharges_to_sponsors']].head(10))
