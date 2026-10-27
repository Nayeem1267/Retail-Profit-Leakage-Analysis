# Retail Profit Leakage Analysis
A comprehensive data analytics case study evaluating 15,000 retail transactions to detect margin vulnerabilities, evaluate markdown efficiency, and establish algorithmic guardrails.

## 📊 Performance Architecture
* **Net Sales:** ₹61.56M
* **Total Profit:** ₹20.31M
* **Composite Profit Margin:** 32.99%
* **Loss Transactions Identified:** 42 high-priority exceptions (isolated to the Electronics category)

## 🛠️ Technology Stack & Architecture
* **Database Layer:** Local MySQL instance containing historical transaction logs.
* **Engineering & Automation:** Python 3 (Pandas, NumPy) pipeline engineered to rebuild repeatable KPI matrices and handle discount quartile boundary ties seamlessly via custom sorting indices.
* **Business Intelligence:** Tableau desktop platform visualizing rolling revenue trends, product margins, and discount variance.

## 📂 Project Directory Structure
* `retail_profit_analysis.py` - Core Python extraction and validation script.
* `Retail_Profit_Leakage_Analysis.twb` - Native Tableau workbook connected to the data layer.
* `Executive_Action_Plan.docx` - Structured 30-day corporate strategy brief.

## 🚀 Execution & Reproducibility
The Python script functions as a localized pipeline to digest a secure `.csv` relational export of the `retail_sales` database schema without running live mutation queries on the production environment.

### Prerequisites
```bash
pip install pandas numpy openpyxl
```

### Run Command
```bash
python retail_profit_analysis.py path/to/retail_sales.csv
```
The routine automatically yields targeted breakdown files (`category.csv`, `discount_quartiles.csv`, `loss_products.csv`, `monthly.csv`) alongside a master key metrics JSON manifest in an isolated output folder.
