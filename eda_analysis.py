import pandas as pd
import numpy as np

file_path = "HHS_Unaccompanied_Alien_Children_Program.csv"

# Load the dataset
df = pd.read_csv(file_path)

# Clean column names
df.columns = [c.strip().replace('*', '') for c in df.columns]

# Drop completely empty rows and rows without valid date
df = df.dropna(subset=['Date'])
df = df[df['Date'].astype(str).str.strip() != '']

# Parse Date
df['Date'] = pd.to_datetime(df['Date'], format='%B %d, %Y', errors='coerce')
df = df.dropna(subset=['Date'])
df = df.sort_values('Date').reset_index(drop=True)

# Standardize column names
col_map = {
    'Children apprehended and placed in CBP custody': 'apprehensions',
    'Children in CBP custody': 'cbp_custody',
    'Children transferred out of CBP custody': 'transfers_to_hhs',
    'Children in HHS Care': 'hhs_care',
    'Children discharged from HHS Care': 'discharges_to_sponsors'
}

for col in col_map.keys():
    if col in df.columns:
        # Unconditionally clean commas and whitespace
        df[col] = df[col].astype(str).str.replace(',', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

df = df.rename(columns=col_map)

# Add derived process metrics according to project specifications:
# 1. Transfer Efficiency Ratio = Transfers ÷ CBP Custody
# Measures CBP -> HHS speed
df['transfer_efficiency_ratio'] = np.where(df['cbp_custody'] > 0, df['transfers_to_hhs'] / df['cbp_custody'], np.nan)

# 2. Discharge Effectiveness = Discharges ÷ HHS Care
# Measures Placement success / outflow rate from HHS care
df['discharge_effectiveness'] = np.where(df['hhs_care'] > 0, df['discharges_to_sponsors'] / df['hhs_care'], np.nan)

# 3. Pipeline Throughput Rate = Total exits ÷ Total entries (discharges / apprehensions)
# Measures overall system movement / exit-to-entry parity
df['pipeline_throughput_rate'] = np.where(df['apprehensions'] > 0, df['discharges_to_sponsors'] / df['apprehensions'], np.nan)

# 4. Backlog Accumulation Rate & Net System Flows
# CBP net intake = apprehensions - transfers_to_hhs
df['cbp_net_flow'] = df['apprehensions'] - df['transfers_to_hhs']
# HHS net intake = transfers_to_hhs - discharges_to_sponsors
df['hhs_net_flow'] = df['transfers_to_hhs'] - df['discharges_to_sponsors']
# Overall pipeline net flow = apprehensions - discharges_to_sponsors
df['system_net_flow'] = df['apprehensions'] - df['discharges_to_sponsors']

# Backlog accumulation rate: when net flow > 0, backlog builds up; when net flow < 0, backlog clears.
df['cumulative_backlog'] = df['system_net_flow'].cumsum()

# 5. Outcome Stability Score:
# 7-day rolling coefficient of variation of discharges (rolling std / rolling mean)
# Inverted/stabilized score: 1 / (1 + CV) so higher is more stable, or standard rolling stability
df['discharge_rolling_7d_mean'] = df['discharges_to_sponsors'].rolling(7, min_periods=1).mean()
df['discharge_rolling_7d_std'] = df['discharges_to_sponsors'].rolling(7, min_periods=1).std().fillna(0)
df['discharge_volatility_cv'] = np.where(
    df['discharge_rolling_7d_mean'] > 0, 
    df['discharge_rolling_7d_std'] / df['discharge_rolling_7d_mean'], 
    0
)
# Outcome Stability Score between 0 and 100%
df['outcome_stability_score'] = 100 * (1 / (1 + df['discharge_volatility_cv']))

# 6. Temporal Features
df['day_of_week'] = df['Date'].dt.day_name()
df['day_of_week_num'] = df['Date'].dt.dayofweek
df['is_weekend'] = df['day_of_week_num'] >= 5
df['year_month'] = df['Date'].dt.to_period('M').astype(str)
df['year'] = df['Date'].dt.year
df['month'] = df['Date'].dt.month

# 7-day rolling averages for smooth trend analytics
df['transfer_eff_7d_ma'] = df['transfer_efficiency_ratio'].rolling(7, min_periods=1).mean()
df['discharge_eff_7d_ma'] = df['discharge_effectiveness'].rolling(7, min_periods=1).mean()
df['throughput_7d_ma'] = df['pipeline_throughput_rate'].rolling(7, min_periods=1).mean()

# Save cleaned dataset
df.to_csv("cleaned_hhs_uac_data.csv", index=False)
print("Saved cleaned_hhs_uac_data.csv with shape:", df.shape)

# Print detailed summary statistics
print("\n=== CORE KPI METRICS SUMMARY ===")
print("Date Range:", df['Date'].min().strftime('%Y-%m-%d'), "to", df['Date'].max().strftime('%Y-%m-%d'))
print("Total Reporting Days:", len(df))
print("\n--- Volume Totals ---")
print(f"Total Apprehensions (Intake): {df['apprehensions'].sum():,.0f}")
print(f"Total Transfers to HHS:       {df['transfers_to_hhs'].sum():,.0f}")
print(f"Total Discharges to Sponsors: {df['discharges_to_sponsors'].sum():,.0f}")
print(f"Average CBP Active Custody:   {df['cbp_custody'].mean():.1f} children")
print(f"Average HHS Active Care:      {df['hhs_care'].mean():,.1f} children")
print(f"Peak HHS Active Care:         {df['hhs_care'].max():,.0f} children (on {df.loc[df['hhs_care'].idxmax(), 'Date'].strftime('%Y-%m-%d')})")
print(f"Min HHS Active Care:          {df['hhs_care'].min():,.0f} children (on {df.loc[df['hhs_care'].idxmin(), 'Date'].strftime('%Y-%m-%d')})")

print("\n--- KPI Ratios ---")
print(f"Transfer Efficiency Ratio (Mean): {df['transfer_efficiency_ratio'].mean():.3f} ({df['transfer_efficiency_ratio'].mean()*100:.1f}%)")
print(f"Transfer Efficiency Ratio (Median): {df['transfer_efficiency_ratio'].median():.3f}")
print(f"Discharge Effectiveness (Mean):   {df['discharge_effectiveness'].mean():.4f} ({df['discharge_effectiveness'].mean()*100:.2f}%)")
print(f"Discharge Effectiveness (Median): {df['discharge_effectiveness'].median():.4f}")
print(f"Pipeline Throughput (Mean):       {df['pipeline_throughput_rate'].mean():.2f}")
print(f"Pipeline Throughput (Median):     {df['pipeline_throughput_rate'].median():.2f}")
print(f"Average Outcome Stability Score:  {df['outcome_stability_score'].mean():.1f}%")

print("\n--- Day of Week Transition Patterns ---")
dow_agg = df.groupby('day_of_week')[['apprehensions', 'transfers_to_hhs', 'cbp_custody', 'transfer_efficiency_ratio', 'discharges_to_sponsors', 'discharge_effectiveness']].mean()
# Order by Monday-Sunday
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
print(dow_agg.reindex([d for d in dow_order if d in dow_agg.index]))

print("\n--- Annual Breakdown ---")
annual_agg = df.groupby('year').agg({
    'apprehensions': ['sum', 'mean'],
    'transfers_to_hhs': ['sum', 'mean'],
    'discharges_to_sponsors': ['sum', 'mean'],
    'cbp_custody': 'mean',
    'hhs_care': 'mean',
    'transfer_efficiency_ratio': 'mean',
    'discharge_effectiveness': 'mean',
    'pipeline_throughput_rate': 'mean'
})
print(annual_agg)
