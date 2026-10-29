"""
Care Transition Efficiency & Placement Outcome Analytics
Unaccompanied Alien Children (UAC) Program Pipeline Analytics Dashboard
Developed for HHS ORR & Interagency Policy Evaluation
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# Set page configuration
st.set_page_config(
    page_title="UAC Care Transition & Placement Analytics",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Federal Policy & Analytics Theme)
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.80rem;
        color: #475569;
        margin-top: 4px;
    }
    .alert-pill-red {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .alert-pill-green {
        background-color: #dcfce7;
        color: #166534;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .alert-pill-yellow {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    /* Section Headers */
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-top: 15px;
        margin-bottom: 12px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA LOADING & PREPARATION WITH CACHING
# ---------------------------------------------------------
@st.cache_data
def load_and_process_data():
    raw_path = "HHS_Unaccompanied_Alien_Children_Program.csv"
    clean_path = "cleaned_hhs_uac_data.csv"
    
    if os.path.exists(clean_path):
        df = pd.read_csv(clean_path)
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        df = pd.read_csv(raw_path)
        df.columns = [c.strip().replace('*', '') for c in df.columns]
        df = df.dropna(subset=['Date'])
        df = df[df['Date'].astype(str).str.strip() != '']
        df['Date'] = pd.to_datetime(df['Date'], format='%B %d, %Y', errors='coerce')
        df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)
        
        col_map = {
            'Children apprehended and placed in CBP custody': 'apprehensions',
            'Children in CBP custody': 'cbp_custody',
            'Children transferred out of CBP custody': 'transfers_to_hhs',
            'Children in HHS Care': 'hhs_care',
            'Children discharged from HHS Care': 'discharges_to_sponsors'
        }
        for col in col_map.keys():
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df = df.rename(columns=col_map)
        
        # Derived Metrics
        df['transfer_efficiency_ratio'] = np.where(df['cbp_custody'] > 0, df['transfers_to_hhs'] / df['cbp_custody'], np.nan)
        df['discharge_effectiveness'] = np.where(df['hhs_care'] > 0, df['discharges_to_sponsors'] / df['hhs_care'], np.nan)
        df['pipeline_throughput_rate'] = np.where(df['apprehensions'] > 0, df['discharges_to_sponsors'] / df['apprehensions'], np.nan)
        df['cbp_net_flow'] = df['apprehensions'] - df['transfers_to_hhs']
        df['hhs_net_flow'] = df['transfers_to_hhs'] - df['discharges_to_sponsors']
        df['system_net_flow'] = df['apprehensions'] - df['discharges_to_sponsors']
        df['cumulative_backlog'] = df['system_net_flow'].cumsum()
        
        # Little's Law Dwell Time in days
        df['cbp_estimated_los_days'] = np.where(df['transfers_to_hhs'] > 0, df['cbp_custody'] / df['transfers_to_hhs'], np.nan)
        df['tvpra_violation_risk'] = df['cbp_estimated_los_days'] > 3.0
        df['hhs_estimated_los_days'] = np.where(df['discharges_to_sponsors'] > 0, df['hhs_care'] / df['discharges_to_sponsors'], np.nan)
        
        # Stability Score
        df['discharge_rolling_7d_mean'] = df['discharges_to_sponsors'].rolling(7, min_periods=1).mean()
        df['discharge_rolling_7d_std'] = df['discharges_to_sponsors'].rolling(7, min_periods=1).std().fillna(0)
        df['discharge_volatility_cv'] = np.where(df['discharge_rolling_7d_mean'] > 0, df['discharge_rolling_7d_std'] / df['discharge_rolling_7d_mean'], 0)
        df['outcome_stability_score'] = 100 * (1 / (1 + df['discharge_volatility_cv']))
        
        # Temporal
        df['day_of_week'] = df['Date'].dt.day_name()
        df['year_month'] = df['Date'].dt.to_period('M').astype(str)
        df['year'] = df['Date'].dt.year
    
    return df

df_full = load_and_process_data()

# ---------------------------------------------------------
# SIDEBAR CONTROLS & THRESHOLD ALERTS
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Seal_of_the_United_States_Department_of_Health_and_Human_Services.svg/300px-Seal_of_the_United_States_Department_of_Health_and_Human_Services.svg.png", width=70)
    st.title("Control Center")
    st.markdown("**UAC Care Pipeline Analytics System**")
    st.markdown("---")
    
    # Date Filtering
    st.subheader("📅 Date Selection")
    min_date = df_full['Date'].min().to_pydatetime()
    max_date = df_full['Date'].max().to_pydatetime()
    
    date_preset = st.selectbox(
        "Quick Period Filter",
        ["Full Pipeline History (2023 - 2025)", "Calendar Year 2023", "Calendar Year 2024", "Calendar Year 2025", "Custom Date Range"]
    )
    
    if date_preset == "Calendar Year 2023":
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
    elif date_preset == "Calendar Year 2024":
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
    elif date_preset == "Calendar Year 2025":
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)
    elif date_preset == "Custom Date Range":
        start_date, end_date = st.date_input(
            "Select Custom Range",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    else:
        start_date, end_date = min_date, max_date
        
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Filter dataset
    mask = (df_full['Date'] >= start_dt) & (df_full['Date'] <= end_dt)
    df = df_full.loc[mask].copy().reset_index(drop=True)
    
    st.markdown("---")
    # Threshold Configuration
    st.subheader("⚙️ Policy Alert Thresholds")
    transfer_alert_thresh = st.slider(
        "CBP Transfer Efficiency Alert Threshold (%)",
        min_value=10, max_value=100, value=50, step=5,
        help="Alert triggers when daily transfers out of CBP fall below this percentage of active CBP custody."
    ) / 100.0
    
    discharge_alert_thresh = st.slider(
        "HHS Discharge Effectiveness Threshold (%)",
        min_value=0.5, max_value=5.0, value=1.5, step=0.1,
        help="Alert triggers when daily discharges to sponsors fall below this percentage of active HHS care load."
    ) / 100.0
    
    tvpra_threshold_days = st.slider(
        "TVPRA Custody Dwell Limit (Days)",
        min_value=1.0, max_value=5.0, value=3.0, step=0.5,
        help="Trafficking Victims Protection Reauthorization Act specifies statutory 72-hour (3 days) transfer limit."
    )
    
    st.markdown("---")
    # Metric View Mode
    st.subheader("📊 Metric Display Mode")
    metric_view = st.radio(
        "Data Smoothing",
        ["Raw Daily Observations", "7-Day Rolling Moving Average", "30-Day Rolling Moving Average"],
        index=1
    )
    
    st.markdown("---")
    st.caption("Interagency Analytics Engine v3.4 | Unified Mentor")

# ---------------------------------------------------------
# DYNAMIC THRESHOLD ALERTS & KPI EVALUATION
# ---------------------------------------------------------
# Calculate dynamic flags on current filtered data
df['transfer_alert'] = df['transfer_efficiency_ratio'] < transfer_alert_thresh
df['discharge_alert'] = df['discharge_effectiveness'] < discharge_alert_thresh
df['tvpra_alert'] = df['cbp_estimated_los_days'] > tvpra_threshold_days

total_days = len(df)
transfer_alert_days = df['transfer_alert'].sum()
discharge_alert_days = df['discharge_alert'].sum()
tvpra_alert_days = df['tvpra_alert'].sum()

# ---------------------------------------------------------
# HEADER & EXECUTIVE SUMMARY BANNER
# ---------------------------------------------------------
st.title("Care Transition Efficiency & Placement Outcome Analytics")
st.markdown("""
**Cross-Agency Pipeline Flow Intelligence for the UAC Program**  
*Evaluating CBP Apprehension $\\rightarrow$ HHS Sheltering $\\rightarrow$ Sponsor Reunification Performance Dynamics*
""")

# Visual Alert Notifications
if tvpra_alert_days > 0 or transfer_alert_days > 0:
    col_a1, col_a2 = st.columns([1, 1])
    with col_a1:
        if tvpra_alert_days > 0:
            st.warning(f"⚠️ **TVPRA Statutory Compliance Risk**: {tvpra_alert_days} of {total_days} reporting days ({tvpra_alert_days/total_days*100:.1f}%) had estimated CBP custody dwell times exceeding {tvpra_threshold_days:.1f} days (statutory 72-hr limit).")
        else:
            st.success("✅ **TVPRA Compliance**: CBP custody dwell time remained within the statutory limit during this period.")
    with col_a2:
        if transfer_alert_days > 0 or discharge_alert_days > 0:
            st.error(f"🚨 **Pipeline Constriction Warning**: {transfer_alert_days} days breached the CBP Transfer Efficiency threshold (< {transfer_alert_thresh*100:.0f}%), and {discharge_alert_days} days breached the HHS Discharge Effectiveness threshold (< {discharge_alert_thresh*100:.1f}%).")
        else:
            st.success("✅ **Throughput Normal**: Transition and discharge efficiency metrics operated above established alert thresholds.")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# HIGH-LEVEL KPI SCORECARD
# ---------------------------------------------------------
kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)

avg_trans_eff = df['transfer_efficiency_ratio'].mean()
avg_disc_eff = df['discharge_effectiveness'].mean()
avg_throughput = df['pipeline_throughput_rate'].mean()
net_accum = df['system_net_flow'].sum()
avg_stability = df['outcome_stability_score'].mean()
avg_hhs_load = df['hhs_care'].mean()

with kpi_col1:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Transfer Efficiency</div>
        <div class="metric-value">{avg_trans_eff*100:.1f}%</div>
        <div class="metric-sub">Mean daily transfers / CBP custody</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Discharge Effectiveness</div>
        <div class="metric-value">{avg_disc_eff*100:.2f}%</div>
        <div class="metric-sub">Daily exits / active HHS care</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Pipeline Throughput</div>
        <div class="metric-value">{avg_throughput:.2f}x</div>
        <div class="metric-sub">Total exits ÷ Total entries ratio</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    backlog_pill = "alert-pill-green" if net_accum <= 0 else "alert-pill-red"
    backlog_text = f"{net_accum:+,.0f}" if net_accum != 0 else "0"
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Net Backlog Delta</div>
        <div class="metric-value">{backlog_text}</div>
        <div class="metric-sub"><span class="{backlog_pill}">Inflows vs Exits Balance</span></div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col5:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Outcome Stability</div>
        <div class="metric-value">{avg_stability:.1f}%</div>
        <div class="metric-sub">Placement consistency score</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col6:
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-title">Average HHS Census</div>
        <div class="metric-value">{avg_hhs_load:,.0f}</div>
        <div class="metric-sub">Peak: {df['hhs_care'].max():,.0f} children</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# MAIN INTERACTIVE TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🌊 Care Pipeline Flow",
    "⚡ Transition & Discharge Panels",
    "🚧 Bottleneck & Delay Detection",
    "📅 Temporal & Pattern Analysis",
    "🎯 Outcome Stability & Volatility",
    "🔮 Policy What-If Simulator",
    "📋 Data Explorer & Export"
])

# ---------------------------------------------------------
# TAB 1: CARE PIPELINE FLOW VISUALIZATION
# ---------------------------------------------------------
with tab1:
    st.markdown("<div class=\"section-header\">Care Pipeline End-to-End Flow Modeling</div>", unsafe_allow_html=True)
    st.markdown("""
    This module tracks children transitioning across three operational stages:
    **Stage 1: CBP Apprehension & Custody** $\\rightarrow$ 
    **Stage 2: Transfer to HHS Care & Case Management** $\\rightarrow$ 
    **Stage 3: Discharge & Safe Placement with Vetted Sponsors**.
    """)
    
    col_flow1, col_flow2 = st.columns([3, 2])
    
    with col_flow1:
        st.subheader("Pipeline Flow Sankey Diagram")
        # Aggregate flows for selected timeframe
        tot_apprehensions = df['apprehensions'].sum()
        tot_transfers = df['transfers_to_hhs'].sum()
        tot_discharges = df['discharges_to_sponsors'].sum()
        end_cbp = df.iloc[-1]['cbp_custody']
        end_hhs = df.iloc[-1]['hhs_care']
        
        # Build Sankey Nodes and Links
        # Nodes: 0: Apprehensions, 1: CBP Custody, 2: HHS Care, 3: Sponsor Discharges, 4: Active CBP, 5: Active HHS
        node_labels = [
            f"1. Border Apprehensions<br>({tot_apprehensions:,.0f})",
            f"2. CBP Custody Processing<br>(Flow: {tot_transfers:,.0f})",
            f"3. HHS Shelter & Care<br>(Census: {avg_hhs_load:,.0f})",
            f"4. Sponsor Placement / Exits<br>({tot_discharges:,.0f})",
            f"Current CBP Census<br>({end_cbp:,.0f})",
            f"Current HHS Census<br>({end_hhs:,.0f})"
        ]
        
        node_colors = ["#3b82f6", "#f59e0b", "#8b5cf6", "#10b981", "#ef4444", "#6366f1"]
        
        sources = [0, 1, 2, 1, 2]
        targets = [1, 2, 3, 4, 5]
        values = [
            tot_apprehensions,
            tot_transfers,
            tot_discharges,
            max(1, end_cbp),
            max(1, end_hhs)
        ]
        
        sankey_fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=25,
                line=dict(color="black", width=0.5),
                label=node_labels,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=["rgba(59, 130, 246, 0.4)", "rgba(245, 158, 11, 0.4)", "rgba(16, 185, 129, 0.4)", "rgba(239, 68, 68, 0.3)", "rgba(99, 102, 241, 0.3)"]
            )
        )])
        sankey_fig.update_layout(
            font=dict(size=12, family="sans-serif"),
            height=460,
            margin=dict(l=20, r=20, t=25, b=25)
        )
        st.plotly_chart(sankey_fig, use_container_width=True)
    
    with col_flow2:
        st.subheader("Stage Volume & Conversion Waterfall")
        # Waterfall breakdown
        waterfall_fig = go.Figure(go.Waterfall(
            name="Pipeline Transition",
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=["Apprehensions (Inflow)", "CBP Transfers to HHS", "HHS Sponsor Discharges", "Net Cumulative Balance"],
            textposition="outside",
            text=[f"{tot_apprehensions:+,.0f}", f"{-tot_transfers:+,.0f}", f"{-tot_discharges:+,.0f}", f"{net_accum:,.0f}"],
            y=[tot_apprehensions, -tot_transfers, -tot_discharges, 0],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#10b981"}},
            increasing={"marker": {"color": "#ef4444"}},
            totals={"marker": {"color": "#3b82f6"}}
        ))
        waterfall_fig.update_layout(
            height=460,
            showlegend=False,
            margin=dict(l=20, r=20, t=25, b=25),
            yaxis=dict(title="Volume of Children")
        )
        st.plotly_chart(waterfall_fig, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Dynamic Stage Inventory Comparison: CBP Custody vs HHS Care")
    # Dual line chart of active loads
    fig_census = go.Figure()
    fig_census.add_trace(go.Scatter(
        x=df['Date'], y=df['hhs_care'],
        name="Children in HHS Care (Right Axis)",
        line=dict(color="#1e3a8a", width=2.5),
        yaxis="y2"
    ))
    fig_census.add_trace(go.Scatter(
        x=df['Date'], y=df['cbp_custody'],
        name="Children in CBP Custody (Left Axis)",
        line=dict(color="#f59e0b", width=2),
        fill='tozeroy',
        fillcolor='rgba(245, 158, 11, 0.1)',
        yaxis="y"
    ))
    fig_census.update_layout(
        height=380,
        margin=dict(l=40, r=40, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="Date"),
        yaxis=dict(title="Active CBP Custody (Children)", side="left", showgrid=True),
        yaxis2=dict(title="Active HHS Care (Children)", side="right", overlaying="y", showgrid=False)
    )
    st.plotly_chart(fig_census, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: TRANSITION & DISCHARGE EFFICIENCY PANELS
# ---------------------------------------------------------
with tab2:
    st.markdown("<div class=\"section-header\">Transition Efficiency & Discharge Effectiveness Panels</div>", unsafe_allow_html=True)
    st.markdown("""
    - **Transfer Efficiency Ratio** = $\\frac{\\text{Daily Transfers Out of CBP}}{\\text{Active CBP Custody}}$ : Evaluates CBP-to-HHS handover velocity.
    - **Discharge Effectiveness Index** = $\\frac{\\text{Daily Discharges to Sponsors}}{\\text{Active HHS Care Load}}$ : Measures child reunification throughput per unit of shelter capacity.
    """)
    
    col_te1, col_te2 = st.columns(2)
    
    # Calculate smoothed lines based on sidebar toggle
    if metric_view == "7-Day Rolling Moving Average":
        y_trans = df['transfer_efficiency_ratio'].rolling(7, min_periods=1).mean()
        y_disc = df['discharge_effectiveness'].rolling(7, min_periods=1).mean()
        smoothing_label = "(7-Day Moving Average)"
    elif metric_view == "30-Day Rolling Moving Average":
        y_trans = df['transfer_efficiency_ratio'].rolling(30, min_periods=1).mean()
        y_disc = df['discharge_effectiveness'].rolling(30, min_periods=1).mean()
        smoothing_label = "(30-Day Moving Average)"
    else:
        y_trans = df['transfer_efficiency_ratio']
        y_disc = df['discharge_effectiveness']
        smoothing_label = "(Raw Daily Observations)"
        
    with col_te1:
        st.subheader(f"Transfer Efficiency Ratio {smoothing_label}")
        fig_te = go.Figure()
        fig_te.add_trace(go.Scatter(
            x=df['Date'], y=y_trans * 100,
            name="Transfer Efficiency Ratio (%)",
            line=dict(color="#0284c7", width=2)
        ))
        fig_te.add_hline(
            y=transfer_alert_thresh * 100, line_dash="dash", line_color="#dc2626",
            annotation_text=f"Alert Threshold ({transfer_alert_thresh*100:.0f}%)",
            annotation_position="bottom right"
        )
        fig_te.update_layout(
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Transfer Efficiency Ratio (%)")
        )
        st.plotly_chart(fig_te, use_container_width=True)
        
        st.info(f"""
        **CBP Handover Insights:**
        - **Period Average**: {avg_trans_eff*100:.1f}% daily transfer rate.
        - **10th Percentile (Severe Slump)**: {df['transfer_efficiency_ratio'].quantile(0.10)*100:.1f}%.
        - **Alert Breach Days**: {transfer_alert_days} days below {transfer_alert_thresh*100:.0f}%.
        """)

    with col_te2:
        st.subheader(f"Discharge Effectiveness Index {smoothing_label}")
        fig_de = go.Figure()
        fig_de.add_trace(go.Scatter(
            x=df['Date'], y=y_disc * 100,
            name="Discharge Effectiveness (%)",
            line=dict(color="#10b981", width=2)
        ))
        fig_de.add_hline(
            y=discharge_alert_thresh * 100, line_dash="dash", line_color="#dc2626",
            annotation_text=f"Alert Threshold ({discharge_alert_thresh*100:.1f}%)",
            annotation_position="top right"
        )
        fig_de.update_layout(
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Discharge Effectiveness (% of HHS Care)")
        )
        st.plotly_chart(fig_de, use_container_width=True)
        
        st.info(f"""
        **HHS Placement Insights:**
        - **Period Average**: {avg_disc_eff*100:.2f}% daily placement rate.
        - **10th Percentile (Severe Slump)**: {df['discharge_effectiveness'].quantile(0.10)*100:.2f}%.
        - **Alert Breach Days**: {discharge_alert_days} days below {discharge_alert_thresh*100:.1f}%.
        """)

    st.markdown("---")
    st.subheader("Statistical Distribution of Efficiency Ratios")
    col_dist1, col_dist2 = st.columns(2)
    with col_dist1:
        hist_te = px.histogram(
            df, x="transfer_efficiency_ratio", nbins=35,
            title="Transfer Efficiency Ratio Histogram & Density",
            labels={"transfer_efficiency_ratio": "Transfer Ratio"},
            color_discrete_sequence=["#0284c7"],
            marginal="box"
        )
        hist_te.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(hist_te, use_container_width=True)
        
    with col_dist2:
        hist_de = px.histogram(
            df, x="discharge_effectiveness", nbins=35,
            title="Discharge Effectiveness Index Histogram & Density",
            labels={"discharge_effectiveness": "Discharge Ratio"},
            color_discrete_sequence=["#10b981"],
            marginal="box"
        )
        hist_de.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(hist_de, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: BOTTLENECK & DELAY DETECTION
# ---------------------------------------------------------
with tab3:
    st.markdown("<div class=\"section-header\">Bottleneck & Queue Delay Detection Engine</div>", unsafe_allow_html=True)
    st.markdown("""
    A bottleneck occurs when stage inflows exceed exit capacity, generating a queue buildup. 
    This tab evaluates **Net Pipeline Intake Flow**, **Cumulative System Backlog**, and **TVPRA 72-Hour Legal Compliance Dwell Time**.
    """)
    
    col_bn1, col_bn2 = st.columns(2)
    
    with col_bn1:
        st.subheader("Daily Net Flow (Apprehensions vs Discharges)")
        # Bar chart with positive (red=buildup) and negative (green=clearance)
        df['flow_color'] = np.where(df['system_net_flow'] > 0, '#ef4444', '#10b981')
        fig_net = go.Figure()
        fig_net.add_trace(go.Bar(
            x=df['Date'], y=df['system_net_flow'],
            marker_color=df['flow_color'],
            name="Daily Net Flow"
        ))
        fig_net.update_layout(
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Net Daily Change (+ Buildup / - Clearance)")
        )
        st.plotly_chart(fig_net, use_container_width=True)
        
    with col_bn2:
        st.subheader("Cumulative System Backlog Trajectory")
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=df['Date'], y=df['cumulative_backlog'],
            mode="lines",
            line=dict(color="#6366f1", width=3),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.15)",
            name="Cumulative Net Backlog"
        ))
        fig_cum.update_layout(
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Cumulative Net Children Added/(Discharged)")
        )
        st.plotly_chart(fig_cum, use_container_width=True)
        
    st.markdown("---")
    st.subheader("⚖️ TVPRA Statutory Compliance: CBP Estimated Custody Dwell Time")
    st.markdown(f"""
    Under the **Trafficking Victims Protection Reauthorization Act (TVPRA) of 2008 (8 U.S.C. § 1232)**, unaccompanied children in CBP custody 
    must be transferred to HHS care **within 72 hours (3.0 days)** of apprehension except under exceptional circumstances.
    """)
    
    fig_tvpra = go.Figure()
    fig_tvpra.add_trace(go.Scatter(
        x=df['Date'], y=df['cbp_estimated_los_days'],
        mode="lines",
        line=dict(color="#f59e0b", width=2),
        name="Estimated CBP Dwell Time (Days)"
    ))
    fig_tvpra.add_hline(
        y=tvpra_threshold_days, line_dash="solid", line_color="#dc2626", line_width=2.5,
        annotation_text=f"TVPRA Statutory Cap ({tvpra_threshold_days:.1f} Days)",
        annotation_position="top right"
    )
    # Highlight points above limit
    violations_df = df[df['cbp_estimated_los_days'] > tvpra_threshold_days]
    if len(violations_df) > 0:
        fig_tvpra.add_trace(go.Scatter(
            x=violations_df['Date'], y=violations_df['cbp_estimated_los_days'],
            mode="markers",
            marker=dict(color="#dc2626", size=7, symbol="circle"),
            name="Compliance Risk Exceedances"
        ))
        
    fig_tvpra.update_layout(
        height=380,
        margin=dict(l=30, r=20, t=30, b=30),
        xaxis=dict(title="Date"),
        yaxis=dict(title="Estimated Custody Dwell (Days)", range=[0, min(12, df['cbp_estimated_los_days'].quantile(0.99) * 1.5)])
    )
    st.plotly_chart(fig_tvpra, use_container_width=True)

# ---------------------------------------------------------
# TAB 4: TEMPORAL & PATTERN ANALYSIS
# ---------------------------------------------------------
with tab4:
    st.markdown("<div class=\"section-header\">Temporal & Operational Rhythm Analysis</div>", unsafe_allow_html=True)
    st.markdown("Examining operational synchronization across days of the week, weekends vs. weekdays, and monthly trends.")
    
    col_dow1, col_dow2 = st.columns(2)
    
    # Day of Week Aggregation
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_summary = df.groupby('day_of_week').agg({
        'apprehensions': 'mean',
        'transfers_to_hhs': 'mean',
        'discharges_to_sponsors': 'mean',
        'transfer_efficiency_ratio': lambda x: x.mean() * 100,
        'discharge_effectiveness': lambda x: x.mean() * 100
    }).reindex([d for d in dow_order if d in df['day_of_week'].unique()]).reset_index()
    
    with col_dow1:
        st.subheader("Day-of-Week Transition Speed (% Rates)")
        fig_dow_rate = go.Figure()
        fig_dow_rate.add_trace(go.Bar(
            x=dow_summary['day_of_week'], y=dow_summary['transfer_efficiency_ratio'],
            name="CBP Transfer Efficiency (%)", marker_color="#0284c7"
        ))
        fig_dow_rate.add_trace(go.Bar(
            x=dow_summary['day_of_week'], y=dow_summary['discharge_effectiveness'] * 10,
            name="HHS Discharge Index (x10 %)", marker_color="#10b981"
        ))
        fig_dow_rate.update_layout(
            height=360,
            barmode="group",
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Day of Week"),
            yaxis=dict(title="Efficiency Index (%)")
        )
        st.plotly_chart(fig_dow_rate, use_container_width=True)
        
    with col_dow2:
        st.subheader("Day-of-Week Volume Movements (Average Children)")
        fig_dow_vol = go.Figure()
        fig_dow_vol.add_trace(go.Bar(
            x=dow_summary['day_of_week'], y=dow_summary['apprehensions'],
            name="Apprehensions", marker_color="#3b82f6"
        ))
        fig_dow_vol.add_trace(go.Bar(
            x=dow_summary['day_of_week'], y=dow_summary['transfers_to_hhs'],
            name="Transfers to HHS", marker_color="#f59e0b"
        ))
        fig_dow_vol.add_trace(go.Bar(
            x=dow_summary['day_of_week'], y=dow_summary['discharges_to_sponsors'],
            name="Discharges to Sponsors", marker_color="#10b981"
        ))
        fig_dow_vol.update_layout(
            height=360,
            barmode="group",
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Day of Week"),
            yaxis=dict(title="Average Children Count")
        )
        st.plotly_chart(fig_dow_vol, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Month-over-Month Velocity & Seasonal Dynamics")
    monthly_df = df.groupby('year_month').agg({
        'apprehensions': 'sum',
        'transfers_to_hhs': 'sum',
        'discharges_to_sponsors': 'sum',
        'transfer_efficiency_ratio': 'mean',
        'discharge_effectiveness': 'mean'
    }).reset_index()
    
    fig_mom = go.Figure()
    fig_mom.add_trace(go.Scatter(
        x=monthly_df['year_month'], y=monthly_df['apprehensions'],
        name="Monthly Apprehensions", line=dict(color="#ef4444", width=2.5)
    ))
    fig_mom.add_trace(go.Scatter(
        x=monthly_df['year_month'], y=monthly_df['transfers_to_hhs'],
        name="Monthly Transfers", line=dict(color="#f59e0b", width=2)
    ))
    fig_mom.add_trace(go.Scatter(
        x=monthly_df['year_month'], y=monthly_df['discharges_to_sponsors'],
        name="Monthly Sponsor Discharges", line=dict(color="#10b981", width=2.5)
    ))
    fig_mom.update_layout(
        height=380,
        margin=dict(l=30, r=20, t=30, b=30),
        xaxis=dict(title="Year-Month", tickangle=45),
        yaxis=dict(title="Total Monthly Children Count")
    )
    st.plotly_chart(fig_mom, use_container_width=True)

# ---------------------------------------------------------
# TAB 5: OUTCOME STABILITY & VOLATILITY ANALYSIS
# ---------------------------------------------------------
with tab5:
    st.markdown("<div class=\"section-header\">Outcome Stability & Anomaly Analysis</div>", unsafe_allow_html=True)
    st.markdown("""
    Evaluating the reliability and volatility of child placements over time. 
    Sudden drops in discharge effectiveness indicate case management bottlenecks, legal stalls, or background vetting backlogs.
    """)
    
    col_st1, col_st2 = st.columns(2)
    
    with col_st1:
        st.subheader("Outcome Stability Score (%)")
        fig_stab = go.Figure()
        fig_stab.add_trace(go.Scatter(
            x=df['Date'], y=df['outcome_stability_score'],
            line=dict(color="#8b5cf6", width=2),
            fill="tozeroy",
            fillcolor="rgba(139, 92, 246, 0.1)",
            name="Stability Score"
        ))
        fig_stab.update_layout(
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Stability Score (0 - 100%)", range=[40, 100])
        )
        st.plotly_chart(fig_stab, use_container_width=True)
        
    with col_st2:
        st.subheader("Discharge Volatility (Coefficient of Variation)")
        fig_cv = go.Figure()
        fig_cv.add_trace(go.Scatter(
            x=df['Date'], y=df['discharge_volatility_cv'],
            line=dict(color="#ec4899", width=2),
            name="7-Day Rolling CV"
        ))
        fig_cv.update_layout(
            height=360,
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Coefficient of Variation (σ / μ)")
        )
        st.plotly_chart(fig_cv, use_container_width=True)

    st.markdown("---")
    st.subheader("Correlations Matrix Across Pipeline Stages")
    corr_vars = [
        'apprehensions', 'cbp_custody', 'transfers_to_hhs', 
        'hhs_care', 'discharges_to_sponsors', 
        'transfer_efficiency_ratio', 'discharge_effectiveness'
    ]
    corr_df = df[corr_vars].rename(columns={
        'apprehensions': 'Apprehended',
        'cbp_custody': 'CBP Custody',
        'transfers_to_hhs': 'Transfers Out',
        'hhs_care': 'HHS Care Load',
        'discharges_to_sponsors': 'Discharges',
        'transfer_efficiency_ratio': 'Transfer Eff.',
        'discharge_effectiveness': 'Discharge Eff.'
    }).corr()
    
    fig_corr = px.imshow(
        corr_df, text_auto=".2f",
        color_continuous_scale="RdBu_r",
        aspect="auto",
        title="Inter-Stage Pearson Correlation Heatmap"
    )
    fig_corr.update_layout(height=400, margin=dict(l=30, r=30, t=40, b=30))
    st.plotly_chart(fig_corr, use_container_width=True)

# ---------------------------------------------------------
# TAB 6: POLICY WHAT-IF SCENARIO SIMULATOR
# ---------------------------------------------------------
with tab6:
    st.markdown("<div class=\"section-header\">Interactive Policy Scenario Simulator</div>", unsafe_allow_html=True)
    st.markdown("""
    Model how policy interventions, intake surges, and case management efficiency gains alter system backlog, census, and TVPRA compliance.
    """)
    
    sim_col1, sim_col2 = st.columns([1, 2])
    
    with sim_col1:
        st.subheader("Simulation Parameters")
        sim_intake_delta = st.slider(
            "Border Intake Change (%)",
            min_value=-50, max_value=100, value=0, step=5,
            help="Simulate an increase or decrease in daily border apprehensions."
        )
        sim_cbp_speed = st.slider(
            "CBP Transfer Efficiency Boost (%)",
            min_value=-50, max_value=50, value=15, step=5,
            help="Efficiency improvement from expanded interagency transport corridors."
        )
        sim_discharge_speed = st.slider(
            "Sponsor Placement Efficiency Boost (%)",
            min_value=-30, max_value=50, value=20, step=5,
            help="Efficiency gain from streamlined background checks and expedited case management."
        )
        sim_days = st.slider(
            "Simulation Horizon (Days)",
            min_value=30, max_value=180, value=60, step=15
        )
        
    with sim_col2:
        st.subheader("Projected Trajectory: Baseline vs Policy Reform")
        
        # Recent baseline averages
        recent_days = min(60, len(df))
        base_intake = df.tail(recent_days)['apprehensions'].mean()
        base_cbp = df.iloc[-1]['cbp_custody']
        base_hhs = df.iloc[-1]['hhs_care']
        base_trans_rate = df.tail(recent_days)['transfer_efficiency_ratio'].mean()
        base_disc_rate = df.tail(recent_days)['discharge_effectiveness'].mean()
        
        # Simulated rates
        sim_intake_rate = base_intake * (1 + sim_intake_delta / 100.0)
        sim_trans_rate = base_trans_rate * (1 + sim_cbp_speed / 100.0)
        sim_disc_rate = base_disc_rate * (1 + sim_discharge_speed / 100.0)
        
        # Simulate day by day
        base_hhs_path = [base_hhs]
        sim_hhs_path = [base_hhs]
        
        curr_b_cbp, curr_b_hhs = base_cbp, base_hhs
        curr_s_cbp, curr_s_hhs = base_cbp, base_hhs
        
        for _ in range(sim_days):
            # Baseline step
            b_trans = curr_b_cbp * base_trans_rate
            b_disc = curr_b_hhs * base_disc_rate
            curr_b_cbp = max(0, curr_b_cbp + base_intake - b_trans)
            curr_b_hhs = max(0, curr_b_hhs + b_trans - b_disc)
            base_hhs_path.append(curr_b_hhs)
            
            # Policy scenario step
            s_trans = curr_s_cbp * sim_trans_rate
            s_disc = curr_s_hhs * sim_disc_rate
            curr_s_cbp = max(0, curr_s_cbp + sim_intake_rate - s_trans)
            curr_s_hhs = max(0, curr_s_hhs + s_trans - s_disc)
            sim_hhs_path.append(curr_s_hhs)
            
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(
            x=list(range(sim_days + 1)), y=base_hhs_path,
            name="Status Quo Baseline", line=dict(color="#94a3b8", width=2.5, dash="dash")
        ))
        fig_sim.add_trace(go.Scatter(
            x=list(range(sim_days + 1)), y=sim_hhs_path,
            name="Simulated Policy Scenario", line=dict(color="#10b981", width=3)
        ))
        fig_sim.update_layout(
            height=380,
            margin=dict(l=30, r=20, t=30, b=30),
            xaxis=dict(title=f"Days Forward (Horizon: {sim_days} Days)"),
            yaxis=dict(title="Projected HHS Care Load (Children)")
        )
        st.plotly_chart(fig_sim, use_container_width=True)
        
        diff_end = sim_hhs_path[-1] - base_hhs_path[-1]
        st.success(f"""
        **Simulation Outcome Analysis**:
        - Projected HHS active care after {sim_days} days under reform: **{sim_hhs_path[-1]:,.0f} children**.
        - Compared to status quo, this represents a **{abs(diff_end):,.0f} child difference ({diff_end/base_hhs_path[-1]*100:+.1f}%)** in shelter bed requirements.
        """)

# ---------------------------------------------------------
# TAB 7: DATA EXPLORER & EXPORT
# ---------------------------------------------------------
with tab7:
    st.markdown("<div class=\"section-header\">Searchable Pipeline Record Explorer & Export</div>", unsafe_allow_html=True)
    
    col_exp1, col_exp2 = st.columns([3, 1])
    with col_exp1:
        st.write(f"Showing **{len(df)}** daily observations within selected time interval.")
    with col_exp2:
        csv_download = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Cleaned Dataset (CSV)",
            data=csv_download,
            file_name="uac_care_transition_analytics_filtered.csv",
            mime="text/csv"
        )
        
    st.dataframe(
        df[[
            'Date', 'apprehensions', 'cbp_custody', 'transfers_to_hhs',
            'transfer_efficiency_ratio', 'hhs_care', 'discharges_to_sponsors',
            'discharge_effectiveness', 'pipeline_throughput_rate', 'system_net_flow',
            'cbp_estimated_los_days', 'outcome_stability_score'
        ]].rename(columns={
            'apprehensions': 'Apprehensions',
            'cbp_custody': 'CBP Custody',
            'transfers_to_hhs': 'Transfers Out',
            'transfer_efficiency_ratio': 'Transfer Ratio',
            'hhs_care': 'HHS Care',
            'discharges_to_sponsors': 'Discharges',
            'discharge_effectiveness': 'Discharge Index',
            'pipeline_throughput_rate': 'Throughput Ratio',
            'system_net_flow': 'Net System Flow',
            'cbp_estimated_los_days': 'CBP Dwell (Days)',
            'outcome_stability_score': 'Stability Score (%)'
        }),
        height=450,
        use_container_width=True
    )

# ---------------------------------------------------------
# FOOTER & POLICY ATTESTATION
# ---------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem;">
    <strong>Care Transition Efficiency & Placement Outcome Analytics Dashboard</strong><br>
    Data Source: U.S. Department of Health and Human Services (HHS) & U.S. Customs and Border Protection (CBP)<br>
    Statutory Framework: William Wilberforce Trafficking Victims Protection Reauthorization Act (TVPRA) of 2008 (8 U.S.C. § 1232)<br>
    Developed for Policy Decision-Makers, Child Welfare Analysts, and Operations Oversight Teams.
</div>
""", unsafe_allow_html=True)
