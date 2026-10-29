# 🏛️ Care Transition Efficiency & Placement Outcome Analytics

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.40+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Policy Focus](https://img.shields.io/badge/Federal%20Policy-HHS%20ORR%20%7C%20CBP-navy.svg)](https://www.hhs.gov/)

> **A Comprehensive Process Flow, Queuing Theory, and Placement Outcome Analytics Platform for the Unaccompanied Alien Children (UAC) Care Pipeline.**

---

## 📌 Executive Overview

The U.S. Unaccompanied Alien Children (UAC) Program—administered jointly by the **Department of Homeland Security (U.S. Customs and Border Protection - CBP)** and the **Department of Health and Human Services (Office of Refugee Resettlement - HHS/ORR)**—operates as a complex, multi-stage care and family reunification pipeline. 

While federal reporting has historically emphasized aggregate, static headcounts (e.g., number of children in custody), structural metrics evaluating **process transition efficiency**, **inter-agency velocity**, **TVPRA 72-hour statutory compliance**, and **placement bottlenecks** have remained largely absent.

This project reframes the UAC dataset from a static monitoring lens to an **end-to-end process-engineering and queuing evaluation model**, analyzing **720 daily reporting cycles (January 12, 2023 – December 21, 2025)**.

```
+-----------------------------------------------------------------------------------------------+
|                                    UAC CARE FLOW PIPELINE                                     |
+-----------------------------------------------------------------------------------------------+
|  Stage 1: Inflow & Intake       Stage 2: Care & Case Management    Stage 3: Outflow & Placement|
|                                                                                               |
|  [ Border Apprehensions ]                                                                     |
|            |                                                                                  |
|            v                                                                                  |
|  [ CBP Holding Facilities ] ---(Transfer Efficiency)---> [ HHS/ORR Shelter Network ]          |
|    Active CBP Custody                                      Active HHS Care Load               |
|    (Target: <= 72 Hours)                                   (Case Mgmt, Medical, Legal)        |
|                                                                     |                         |
|                                                           (Discharge Effectiveness)           |
|                                                                     v                         |
|                                                          [ Vetted Sponsor Home ]              |
|                                                            (Family Reunification)             |
+-----------------------------------------------------------------------------------------------+
```

---

## 🎯 Project Objectives & Core Questions

- **Measure CBP $\rightarrow$ HHS Transition Velocity**: How quickly are children moved out of short-term border holding into licensed child welfare shelters?
- **Evaluate Sponsor Placement Outcomes**: Are discharges keeping pace with intake surges?
- **Uncover Operational Bottlenecks**: Where and when do backlogs accumulate? Why does placement efficiency dip during mid-week cycles?
- **Statutory TVPRA Compliance Assessment**: How often does CBP custody exceed the statutory 72-hour limit mandated by 8 U.S.C. § 1232?
- **Actionable Policy Interventions**: Inform predictive transport corridors, parallelized sponsor vetting, and interagency flow synchronization.

---

## 📊 Core Key Performance Indicators (KPIs)

| KPI Name | Mathematical Formula | Operational Significance | Benchmark / Empirical Value |
| :--- | :---: | :--- | :---: |
| **Transfer Efficiency Ratio ($TER$)** | $\frac{\text{Daily Transfers Out of CBP}}{\text{Active CBP Custody}}$ | Measures CBP-to-HHS handover velocity | **Mean: 69.1%** (Median: 70.4%) |
| **Discharge Effectiveness Index ($DEI$)** | $\frac{\text{Daily Discharges to Sponsors}}{\text{Active HHS Shelter Care}}$ | Measures child reunification throughput per unit of shelter capacity | **Mean: 2.37%** (Median: 2.63%) |
| **Pipeline Throughput Rate ($PTR$)** | $\frac{\text{Total Exits (Discharges)}}{\text{Total Entries (Apprehensions)}}$ | Overall system exit-to-entry movement parity | **Mean: 2.50x** (Median: 1.78x) |
| **Net Backlog Accumulation ($NBA$)** | $\text{Apprehensions} - \text{Discharges}$ | Daily net queue buildup (+) or clearance (-) | **Net Period Total: -57,516 Children** |
| **Little's Law CBP Dwell ($W_{CBP}$)** | $\frac{\text{CBP Custody}}{\text{Transfers to HHS}}$ | Average days spent in CBP border patrol holding | **Mean: 1.99 Days** (TVPRA breaches: 13.3%) |
| **Little's Law HHS Dwell ($W_{HHS}$)** | $\frac{\text{HHS Shelter Care}}{\text{Discharges to Sponsors}}$ | Average length of stay (LOS) in shelter care | **Median: 38.0 Days** in shelter custody |
| **Outcome Stability Score ($OSS$)** | $100 \times \frac{1}{1 + CV_{7d}(\text{Discharges})}$ | Consistency and predictability of placements | **Mean: 79.1%** (Min: 55.6%) |

---

## 🚀 Key Empirical Insights

1. **Macro Flow Cleared Significant Inventory**:
   - Total Apprehensions: **67,337 children**
   - Total Transfers to HHS: **92,641 children**
   - Total Safe Discharges: **124,853 children**
   - Resulted in a net reduction of **57,516 children**, driving active HHS care down from an emergency high of **11,516** (Dec 2023) to a sustainable steady-state of **~2,400** (late 2025).
2. **TVPRA 72-Hour Statutory Breach Risk**:
   - In **96 out of 720 days (13.33% of reporting periods)**, estimated dwell time in CBP holding facilities exceeded the **72-hour statutory limit**, primarily due to regional transport shortages and emergency bed assignment delays during surge periods.
3. **Weekly Operational Asynchrony**:
   - Border encounters occur 7 days a week (~93–97 minors/day).
   - In contrast, discharges drop to an administrative low on **Tuesday (136.1 discharges, $DEI = 1.87\%$)** and peak over the weekend on **Sunday (206.1 discharges, $DEI = 2.84\%$)**, indicating batching around working sponsor schedules.
4. **Fiscal Impact of Shelter Stay Compression**:
   - Operating emergency influx beds costs \$1,200–\$1,400/day per minor.
   - Reducing shelter length of stay from **38 days down to 25 days** via parallelized sponsor vetting would save **\$340M–\$520M annually** in federal holding costs.

---

## 🖥️ Streamlit Web Application Features

The interactive dashboard includes:
1. **Executive KPI Scorecard**: Real-time high-level indicators with automated TVPRA risk and efficiency breach warning banners.
2. **Care Pipeline Flow Visualization**:
   - Dynamic **Plotly Sankey Diagram** tracing child movement from border encounter to sponsor placement.
   - Stage conversion waterfall and dual-axis active census comparison.
3. **Transfer & Discharge Panels**:
   - Moving average trendlines (7-day / 30-day).
   - Statistical distribution histograms, boxplots, and breach counters.
4. **Bottleneck & Queue Buildup Detection**:
   - Inflow vs outflow divergence charts with color-coded net balance.
   - Cumulative backlog trajectory.
   - TVPRA 72-hour statutory compliance monitor with scatter breach markers.
5. **Temporal & Pattern Analysis**:
   - Day-of-week transition speed and volume bar charts.
   - Month-over-month placement velocity charts.
6. **Outcome Stability & Volatility**:
   - 7-day rolling coefficient of variation ($CV$).
   - Inter-stage Pearson correlation matrix heatmap.
7. **Interactive Policy What-If Scenario Simulator**:
   - Simulate $+/-$ border intake, CBP transport speed gains, and sponsor vetting acceleration over 30 to 180 days.
8. **Data Explorer & Export**:
   - Searchable, filterable records with one-click CSV export.

---

## 📁 Repository Structure

```text
├── .streamlit/
│   └── config.toml               # Streamlit federal styling & theme configuration
├── HHS_Unaccompanied_Alien_Children_Program.csv  # Raw federal intake dataset
├── cleaned_hhs_uac_data.csv       # Cleaned, standardized dataset with derived KPIs
├── monthly_aggregated_metrics.csv# Aggregated monthly performance figures
├── analytics_summary.json        # Precomputed statistical metrics & correlations
├── app.py                        # Complete Streamlit analytics web application
├── eda_analysis.py               # Exploratory data analysis & data cleaning pipeline
├── advanced_analytics.py         # Advanced queue modeling & Little's Law computations
├── Research_Paper_Care_Transition_Efficiency_and_Placement_Outcome_Analytics.md # Full Research Paper
├── Executive_Summary_Government_Stakeholders.md # Federal policy memorandum
├── PROJECT_SUBMISSION_GUIDE.md   # Complete submission guide, links & video script
├── requirements.txt              # Production Python package dependencies
└── README.md                     # Project documentation
```

---

## 🛠️ Quickstart & Local Installation

### Prerequisites
- Python 3.10+ (tested up to Python 3.14)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Jamy-777/care-transition-efficiency-uac-analytics.git
cd care-transition-efficiency-uac-analytics
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Streamlit App
```bash
streamlit run app.py
```
The application will open in your default browser at `http://localhost:8501`.

---

## ☁️ Deployment Instructions (Streamlit Community Cloud)

1. Push your project files to your GitHub repository.
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New app"**.
4. Select your repository: `Jamy-777/care-transition-efficiency-uac-analytics`.
5. Select the Main file path: `app.py`.
6. Click **"Deploy!"**.
7. Your app will be live at `https://<your-app-name>.streamlit.app` in under 2 minutes!

---

## 📄 Deliverables Summary

- **Research Paper**: Full empirical paper located in [`Research_Paper_Care_Transition_Efficiency_and_Placement_Outcome_Analytics.md`](Research_Paper_Care_Transition_Efficiency_and_Placement_Outcome_Analytics.md).
- **Executive Summary**: Policy memo for HHS/CBP leadership located in [`Executive_Summary_Government_Stakeholders.md`](Executive_Summary_Government_Stakeholders.md).
- **Submission Walkthrough & Video Script**: Step-by-step guide and video recording outline located in [`PROJECT_SUBMISSION_GUIDE.md`](PROJECT_SUBMISSION_GUIDE.md).

---

## 📜 Legal & Policy Framework
- **William Wilberforce Trafficking Victims Protection Reauthorization Act (TVPRA) of 2008** (8 U.S.C. § 1232)
- **Flores v. Reno Stipulated Settlement Agreement** (1997)
- **Homeland Security Act of 2002** (P.L. 107-296)

---

## 🤝 Acknowledgments
Data sourced from the **U.S. Department of Health and Human Services (HHS)**, the **Administration for Children and Families (ACF)**, the **Office of Refugee Resettlement (ORR)**, and **U.S. Customs and Border Protection (CBP)**. Developed under the **Unified Mentor** Internship Program.

