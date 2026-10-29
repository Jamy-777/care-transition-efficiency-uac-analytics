import pandas as pd
import numpy as np
import json

df = pd.read_csv("cleaned_hhs_uac_data.csv")
df['Date'] = pd.to_datetime(df['Date'])

# 1. Little's Law / Dwell Time Estimates
# Length of Stay (LOS) in CBP custody: CBP Custody / Transfers (in days)
df['cbp_estimated_los_days'] = np.where(df['transfers_to_hhs'] > 0, df['cbp_custody'] / df['transfers_to_hhs'], np.nan)
# TVPRA Statutory Flag: Did estimated stay exceed 72 hours (3.0 days)?
df['tvpra_violation_risk'] = df['cbp_estimated_los_days'] > 3.0

# Length of Stay (LOS) in HHS care: HHS Care / Discharges (in days)
df['hhs_estimated_los_days'] = np.where(df['discharges_to_sponsors'] > 0, df['hhs_care'] / df['discharges_to_sponsors'], np.nan)

# 2. Bottleneck Classification
# Stage 1 Bottleneck (CBP-to-HHS): Transfer Efficiency < 40% AND cbp_custody > 75th percentile
cbp_custody_p75 = df['cbp_custody'].quantile(0.75)
df['stage_1_bottleneck'] = (df['transfer_efficiency_ratio'] < 0.40) & (df['cbp_custody'] > cbp_custody_p75)

# Stage 2 Bottleneck (HHS-to-Sponsor): Discharge Effectiveness < 1.5% AND hhs_care > 75th percentile
hhs_care_p75 = df['hhs_care'].quantile(0.75)
df['stage_2_bottleneck'] = (df['discharge_effectiveness'] < 0.015) & (df['hhs_care'] > hhs_care_p75)

# Dual Bottleneck: Both stages constricted
df['dual_bottleneck'] = df['stage_1_bottleneck'] & df['stage_2_bottleneck']

# 3. Monthly Aggregates & Trends
df['year_month'] = df['Date'].dt.to_period('M').astype(str)
monthly = df.groupby('year_month').agg({
    'apprehensions': 'sum',
    'transfers_to_hhs': 'sum',
    'discharges_to_sponsors': 'sum',
    'cbp_custody': 'mean',
    'hhs_care': 'mean',
    'transfer_efficiency_ratio': 'mean',
    'discharge_effectiveness': 'mean',
    'pipeline_throughput_rate': 'mean',
    'system_net_flow': 'sum',
    'cbp_estimated_los_days': 'mean',
    'hhs_estimated_los_days': 'mean',
    'stage_1_bottleneck': 'sum',
    'stage_2_bottleneck': 'sum'
}).reset_index()

# 4. Correlation Analysis
corr_cols = [
    'apprehensions', 'cbp_custody', 'transfers_to_hhs', 
    'hhs_care', 'discharges_to_sponsors', 
    'transfer_efficiency_ratio', 'discharge_effectiveness',
    'pipeline_throughput_rate', 'system_net_flow'
]
corr_matrix = df[corr_cols].corr()

# 5. Stagnation Periods (periods where net accumulation > 0 for 5+ consecutive days)
df['is_accumulating'] = df['system_net_flow'] > 0
# Identify blocks
df['block'] = (df['is_accumulating'] != df['is_accumulating'].shift()).cumsum()
accumulation_blocks = df[df['is_accumulating']].groupby('block').agg(
    start_date=('Date', 'min'),
    end_date=('Date', 'max'),
    duration_days=('Date', 'count'),
    total_net_backlog=('system_net_flow', 'sum'),
    avg_apprehensions=('apprehensions', 'mean'),
    avg_discharges=('discharges_to_sponsors', 'mean')
).query('duration_days >= 3').sort_values('duration_days', ascending=False)

# Convert results to clean JSON report
stats_summary = {
    "total_records": int(len(df)),
    "date_min": df['Date'].min().strftime('%Y-%m-%d'),
    "date_max": df['Date'].max().strftime('%Y-%m-%d'),
    "volume_totals": {
        "total_apprehensions": int(df['apprehensions'].sum()),
        "total_transfers_to_hhs": int(df['transfers_to_hhs'].sum()),
        "total_discharges_to_sponsors": int(df['discharges_to_sponsors'].sum()),
        "net_system_reduction": int(df['discharges_to_sponsors'].sum() - df['apprehensions'].sum())
    },
    "cbp_metrics": {
        "mean_custody": float(df['cbp_custody'].mean()),
        "median_custody": float(df['cbp_custody'].median()),
        "p95_custody": float(df['cbp_custody'].quantile(0.95)),
        "max_custody": float(df['cbp_custody'].max()),
        "mean_transfer_efficiency_ratio": float(df['transfer_efficiency_ratio'].mean()),
        "median_transfer_efficiency_ratio": float(df['transfer_efficiency_ratio'].median()),
        "p10_transfer_efficiency_ratio": float(df['transfer_efficiency_ratio'].quantile(0.10)),
        "mean_estimated_los_days": float(df['cbp_estimated_los_days'].mean()),
        "median_estimated_los_days": float(df['cbp_estimated_los_days'].median()),
        "tvpra_72h_risk_days_count": int(df['tvpra_violation_risk'].sum()),
        "tvpra_72h_risk_days_pct": float(df['tvpra_violation_risk'].mean() * 100),
        "stage_1_bottleneck_days": int(df['stage_1_bottleneck'].sum())
    },
    "hhs_metrics": {
        "mean_care": float(df['hhs_care'].mean()),
        "median_care": float(df['hhs_care'].median()),
        "max_care": float(df['hhs_care'].max()),
        "min_care": float(df['hhs_care'].min()),
        "mean_discharge_effectiveness": float(df['discharge_effectiveness'].mean()),
        "median_discharge_effectiveness": float(df['discharge_effectiveness'].median()),
        "p10_discharge_effectiveness": float(df['discharge_effectiveness'].quantile(0.10)),
        "mean_estimated_los_days": float(df['hhs_estimated_los_days'].mean()),
        "median_estimated_los_days": float(df['hhs_estimated_los_days'].median()),
        "stage_2_bottleneck_days": int(df['stage_2_bottleneck'].sum())
    },
    "pipeline_system_metrics": {
        "mean_throughput_rate": float(df['pipeline_throughput_rate'].mean()),
        "median_throughput_rate": float(df['pipeline_throughput_rate'].median()),
        "dual_bottleneck_days": int(df['dual_bottleneck'].sum()),
        "mean_outcome_stability_score": float(df['outcome_stability_score'].mean()),
        "min_outcome_stability_score": float(df['outcome_stability_score'].min())
    },
    "correlations": {
        "apprehensions_vs_cbp_custody": float(corr_matrix.loc['apprehensions', 'cbp_custody']),
        "cbp_custody_vs_transfers": float(corr_matrix.loc['cbp_custody', 'transfers_to_hhs']),
        "transfers_vs_discharges": float(corr_matrix.loc['transfers_to_hhs', 'discharges_to_sponsors']),
        "hhs_care_vs_discharges": float(corr_matrix.loc['hhs_care', 'discharges_to_sponsors']),
        "apprehensions_vs_transfer_eff": float(corr_matrix.loc['apprehensions', 'transfer_efficiency_ratio']),
        "hhs_care_vs_discharge_eff": float(corr_matrix.loc['hhs_care', 'discharge_effectiveness'])
    }
}

with open("analytics_summary.json", "w") as f:
    json.dump(stats_summary, f, indent=4)

# Save updated dataframe with flags
df.to_csv("cleaned_hhs_uac_data.csv", index=False)
monthly.to_csv("monthly_aggregated_metrics.csv", index=False)

print("Advanced analytics completed and exported!")
print(json.dumps(stats_summary, indent=2))

