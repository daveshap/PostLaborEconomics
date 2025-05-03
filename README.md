# Post-Labor Economics (PLE) Triage Dashboard

**A public, county-level early-warning system for the age when pay-checks stop anchoring prosperity.**

[![License: Apache 2.0](https://img.shields.io/badge/Code%20License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![License: CC BY 4.0](https://img.shields.io/badge/Data%20License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![License: CC BY-ND 4.0](https://img.shields.io/badge/Docs%20License-CC%20BY--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
*(Placeholder badges - update as needed)*

---

## Abstract

The United States is drifting toward an economy where local prosperity is no longer anchored solely to the pay-checks of people who live there. Automation (AI & Robotics), demographic shifts, and remote work are potentially uncoupling economic output from local labor demand. While national metrics like GDP or the unemployment rate provide a broad overview, they often lag behind or mask the crucial shifts happening at the community level. The first signs of economic distress – such as declining labor force participation, shrinking work hours, or rising dependence on transfers – often appear locally long before they dominate national headlines.

This project, grounded in the principles of Post-Labor Economics (PLE), aims to fill that critical information gap. The **PLE Triage Dashboard** provides an early-warning system by tracking key labor market indicators at the US county level. It fuses multiple publicly available data streams into a composite **"Collapse Index" (CI)**, designed to signal when a local labor market is decoupling from broader economic trends, potentially indicating structural stress related to automation or other deep shifts. This dashboard serves as the initial "surveillance" layer for the broader PLE framework, which ultimately aims to understand and improve local **Economic Agency** by analyzing the composition of household income (Wages vs. Property vs. Transfers). By making these trends visible and comparable across counties, this dashboard empowers local leaders, researchers, businesses, and citizens to diagnose challenges early and consider proactive interventions before crises fully manifest.

*(Link to Live Dashboard: [Placeholder - e.g., labor-triage.netlify.app] - Coming Soon!)*
*(Link to PLE Theory / Blog: [Placeholder - e.g., Your Substack/Website Link])*

## The Problem: Lagging Indicators in a Fast-Changing Economy

Traditional economic dashboards focus heavily on headline unemployment rates and GDP growth. While important, these metrics often fail to capture the early, structural shifts impacting local economies in the face of automation and changing work patterns:

* **Wage Erosion:** Automation may suppress wages or reduce hours worked long before mass layoffs occur.
* **Participation Decline:** Discouraged workers, particularly youth, may exit the labor force entirely (NEETs), which isn't reflected in the unemployment rate of those *actively seeking* work.
* **Shifting Income Sources:** A community might maintain consumption levels temporarily through government transfers, masking an underlying erosion of earned income from wages or local business.
* **Geographic Disparities:** National averages obscure significant variations between counties – some thriving, others entering structural decline unnoticed.

Without timely, granular, and compositionally-aware metrics, local communities lack the tools to proactively manage the transition to a potentially post-labor future.

## The Solution: A County-Level Triage Dashboard

This project provides a transparent, reproducible dashboard focused on **early-warning indicators** of labor market stress at the US county level.

* **Goal:** To provide an accessible "heatmap" identifying counties potentially experiencing early stages of labor market decoupling or decline, prompting further investigation and potential intervention.
* **Approach:** Utilizes the "Measure -> Menu -> Monitor" concept central to PLE. This dashboard focuses on the **Measure** aspect for labor market health.
* **Core Metric:** The **Collapse Index (CI)**, a composite score derived from several key labor market indicators.

## Key Metrics & Interpretation

The dashboard tracks several Key Performance Indicators (KPIs), standardized and combined into the Collapse Index (CI):

1.  **Employment-to-Population Ratio (E/Pop):** (Using total E/Pop from BLS LAUS initially). Measures the share of the population that is employed. A falling ratio indicates declining labor absorption.
2.  **Average Weekly Hours:** (Using BLS CES/QCEW). A decline can signal reduced labor demand or a shift to part-time work, even if employment numbers hold steady.
3.  **Youth NEET Rate (Proxy):** (Using ACS B14005). Tracks young adults (16-24) Not in Education, Employment, or Training. A rising rate signals youth disengagement or lack of entry-level opportunities.
4.  **Labor Share of Income:** (Using BEA SAINC7). The proportion of total personal income derived from wages and salaries. A structural decline indicates productivity gains are accruing more to capital than labor.
5.  **Part-Time for Economic Reasons Share (Proxy):** (Using state-level CPS data or LAUS underemployment). Indicates workers who want full-time work but can only find part-time hours due to economic conditions.
6.  **Wage-to-Transfer Income Ratio:** (Using BEA SAINC7). Compares income earned from work to income received from government transfers. A falling ratio signals rising dependency.

**Collapse Index (CI):** Calculated as the average of the standardized z-scores of the available KPIs for a given county and year ($CI = \sum z_i / \sqrt{k}$).
* `CI > 0`: Labor market generally healthier than the national average for that year.
* `CI ≈ 0`: Tracking the national average.
* `CI < 0`: Labor market showing signs of stress relative to the national average; potential early warning for post-labor transition effects.

**(Future Integration: Economic Agency Index - EAI)**
While this dashboard focuses on *triage*, the core diagnostic metric of PLE is the **EAI**. It measures income *composition*:
$EAI = z(\% Earned) + z(\% Property) - z(\% Transfers)$
This will be integrated later to provide a deeper view of how counties are structured economically (reliance on work vs. ownership vs. external support).

## Methodology & Data Sources

This project uses exclusively **public-domain data** from official US government sources. The Extract-Transform-Load (ETL) pipeline is designed to be run **offline** after initial manual download of required raw files, ensuring reproducibility and avoiding reliance on live API calls.

* **Sources:**
    * `BLS LAUS`: County-level employment, labor force (monthly/annual).
    * `BLS CES/QCEW`: Average weekly hours, wages (monthly/quarterly).
    * `BEA SAINC7`: County personal income components (Wages, Property, Transfers) (annual).
    * `ACS B14005`: Youth school enrollment & employment status (annual 5-year estimates).
    * `Census TIGER`: County boundaries/centroids (static).
    * *(Future EAI)*: `IRS SOI` (county AGI data as backup).
* **Pipeline:**
    1.  Raw data files manually placed in `data/raw/`.
    2.  `ingest/` scripts read raw files, perform basic cleaning/filtering, output to `data/interim/`.
    3.  `kpi/` scripts read interim files, calculate specific KPI ratios/values, output to `data/processed/kpi_*.parquet`.
    4.  `index/` script reads processed KPI files, calculates z-scores and the composite `collapse_index.parquet`.
    5.  `dashboard/` script reads *only* processed parquet files for visualization.
* **Tools:** Python 3.11+, Pandas, DuckDB, GeoPandas, Streamlit, PyDeck.

## Dashboard Features & Interpretation

The dashboard aims to provide an intuitive view of county-level labor market health:

* **National Heatmap:** Visualize the Collapse Index (or individual KPIs) across all US counties, typically using a green-to-red color scale.
* **Time Slider:** Scrub through years (e.g., 1990-present) to observe historical trends and the propagation of economic shifts.
* **County Drill-Down:** Click or search for a specific county to see its detailed KPI scorecard, historical sparklines, and percentile ranks compared to peers or the nation.
* **Alerts:** Potential future feature to flag counties where multiple KPIs show sustained negative trends.

**Interpretation:** A persistently low or rapidly falling Collapse Index suggests a county's labor market is under structural stress and may require deeper investigation and potentially interventions aimed at boosting economic agency (the focus of the EAI and the broader PLE framework).

## Getting Started (Local Development)

1.  **Clone the repository:** `git clone [Your Repo URL]`
2.  **Create/activate a virtual environment** (optional but recommended).
3.  **Install dependencies:** `pip install -r requirements.txt`
4.  **Download Raw Data:** Manually download the required files listed in `etl_core.py` (it will prompt with URLs if files are missing) and place them in the `data/raw/` directory.
5.  **Run the ETL pipeline:** `python build_triage.py` (or use `pipelines/run_all.sh/bat` if created). This generates files in `data/processed/`.
6.  **Launch the dashboard:** `python -m streamlit run dashboard/dashboard_triage.py`
7.  Open `http://localhost:8501` in your browser.

*(See `etl_core.py` and `build_triage.py` for specific data requirements and processing steps).*

## Contributing

Contributions are welcome! Please feel free to open an issue to report bugs, suggest features, or discuss methodology. Pull requests are encouraged for:

* Adding new, validated KPIs to the triage dashboard.
* Improving data ingestion robustness and error handling.
* Enhancing dashboard visualizations and user experience.
* Extending the framework to include EAI, CPP, and CCI calculations.
* Adding international data sources (as a separate module).

*(Placeholder: Add link to CONTRIBUTING.md if you create one)*

## License

* **Source Code:** Licensed under the [Apache License 2.0](LICENSE).
* **Generated Data Artefacts (e.g., parquet files):** Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
* **Methodology Documents / White Papers:** Licensed under [Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)](https://creativecommons.org/licenses/by-nd/4.0/).
* **Name & Logo:** "Post-Labor Triage Dashboard"™ and associated logos are trademarks of [Your Name/Org].

## Contact & Citation

* **Project Lead:** [Your Name / Link to your profile/Substack]
* **Contact:** [Your Preferred Contact Email/Method]
* **Suggested Citation:** Shapiro, David. (2025). *Post-Labor Economics Triage Dashboard (Version X.Y)*. [Link to GitHub Repo].

---