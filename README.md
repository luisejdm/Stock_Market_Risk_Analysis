# Stock Market Risk Analysis — Project Report

**Course:** Credit Models (Modelos de Crédito)

**Date:** February 2026

**Author:** Luis Jiménez

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Project Methodology](#3-project-methodology)
4. [Data Sources and Retrieval](#4-data-sources-and-retrieval)
5. [Model 1 — Altman Z-Score (Classic, Z)](#5-model-1--altman-z-score-classic-z)
6. [Model 2 — Altman Z'-Score (Revised for Private Firms)](#6-model-2--altman-z-score-revised-for-private-firms)
7. [Model 3 — Altman Z''-Score (Emerging Markets)](#7-model-3--altman-z-score-emerging-markets)
8. [Model 4 — Merton Distance-to-Default Model](#8-model-4--merton-distance-to-default-model)
9. [Combined Credit Decision Logic](#9-combined-credit-decision-logic)
10. [Version of the Z-Score Formula Used and Justification](#10-version-of-the-z-score-formula-used-and-justification)
11. [References](#11-references)

---

## 1. Introduction

This project implements a financial distress prediction system for publicly traded companies. Given a stock ticker and a firm type, the system automatically fetches the company's most recent financial statements, computes Altman Z-Score variants and a Merton structural model, and synthesizes both into a single credit decision.

The core analytical framework is grounded in the work of Edward I. Altman, whose landmark 1968 paper — later revisited and expanded in the year 2000 — demonstrated that a small set of accounting ratios, combined via multiple discriminant analysis (MDA), could predict corporate bankruptcy with high accuracy up to two years in advance [1]. This project extends that framework in two directions: (1) it applies the appropriate Z-Score variant depending on firm type, and (2) it supplements the accounting-based signal with a market-based structural model (Merton) to arrive at a more robust credit decision.

The system is delivered as a REST API (FastAPI backend) and an interactive dashboard (Streamlit frontend), making it accessible without any programming knowledge.

---

## 2. Getting Started

### 2.1 Prerequisites

- Python 3.9 or higher
- All dependencies listed in `requirements.txt`

Install all dependencies from the project root:

```bash
pip install -r requirements.txt
```

### 2.2 Running the API (FastAPI Backend)

The backend is built with **FastAPI** and must be started before the dashboard.

1. Open a terminal and navigate to the `backend/` directory:

```bash
cd backend
```

2. Start the server with Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

| Endpoint | Method | Description |
|---|---|---|
| `/evaluate` | `POST` | Evaluate a company by ticker and firm type |
| `/health` | `GET` | Health check — verifies the API is running |
| `/docs` | `GET` | Interactive Swagger UI documentation |

Example request body for `/evaluate`:

```json
{
  "ticker": "AAPL",
  "industry_type": 1
}
```

`industry_type` values:
- `1` → Public manufacturing firm (Classic Altman Z-Score)
- `2` → Private or non-manufacturing firm (Revised Z'-Score)
- `3` → Emerging market firm (Z''-Score)

### 2.3 Running the Dashboard (Streamlit Frontend)

The dashboard connects to the API running on `http://localhost:8000`. Make sure the backend is already running before launching the dashboard.

1. Open a **second terminal** and navigate to the `frontend/` directory:

```bash
cd frontend
```

2. Launch the Streamlit app:

```bash
streamlit run dashboard.py
```

Streamlit will automatically open the dashboard in your default browser at `http://localhost:8501`.

From the dashboard you can:
- Enter any stock ticker (e.g., `AAPL`, `TSLA`, `AMZN`).
- Select the firm type from the sidebar.
- View the computed Altman Z-Score, Merton Distance-to-Default, individual ratio breakdown, and the final credit decision.

### 2.4 Quick Start Summary

```bash
# Terminal 1 — Start the API
cd backend && uvicorn main:app --reload

# Terminal 2 — Start the dashboard
cd frontend && streamlit run dashboard.py
```

---

## 3. Project Methodology

The analysis pipeline consists of four sequential stages:

1. **Input validation.** The user supplies a stock ticker (e.g., `AAPL`) and a firm type code:
   - `1` → Public manufacturing firm → Classic Altman Z-Score
   - `2` → Private or non-manufacturing firm → Revised Z'-Score (Altman 2000)
   - `3` → Emerging market firm → Z''-Score (Emerging Markets model)

2. **Data retrieval.** Live financial statement data (balance sheet and income statement) are fetched programmatically from Yahoo Finance via the `yfinance` Python library. The four most recent annual reporting periods are downloaded; only the most recent period is used for Z-Score computation. Market price and shares outstanding are fetched separately to compute market equity.

3. **Model computation.** Depending on the firm type, the appropriate Altman variant is selected. All five financial ratios (X1–X5, or X1–X4 for the emerging market model) are computed from the retrieved data and combined into a single score. The Merton distance-to-default and default probability are computed in parallel using historical balance sheet data to estimate asset volatility.

4. **Classification and credit decision.** Each model independently classifies the firm into a Safe Zone, Grey Zone, or Distress Zone. A rule-based logic then merges the two model outputs into a final credit recommendation: *Approved*, *Approved with Caution*, *Analysis Required*, or *Dismissed*.

---

## 4. Data Sources and Retrieval

### 3.1 Financial Statements

All balance sheet and income statement data are obtained via **Yahoo Finance**, accessed through the open-source Python library [`yfinance`](https://github.com/ranaroussi/yfinance). For each ticker, the library returns standardized annual financial statements. The project uses:

| Statement | Fields Used |
|---|---|
| Balance Sheet | Total Assets, Working Capital, Retained Earnings, Total Liabilities, Current Liabilities, Stockholders' Equity |
| Income Statement | EBIT (Earnings Before Interest and Taxes), Total Revenue |

The code fetches the four most recent annual periods (`iloc[:, :4]`) and reads the most recent one (`iloc[0]`) for Z-Score computation. Historical total assets across all four periods are used to estimate asset volatility for the Merton model.

```python
_obj = yf.Ticker(ticker)
self._bs = pd.DataFrame(_obj.balance_sheet.iloc[:, :4])
self._ist = pd.DataFrame(_obj.income_stmt.iloc[:, :4])
```

### 3.2 Market Data

Current market price and shares outstanding are also retrieved from Yahoo Finance:

```python
self._current_price = _obj.history(period='1d')['Close'].iloc[0]
self._shares_outstanding = _obj.info['sharesOutstanding']
```

Market equity is then computed as:

> **Market Equity = Current Price × Shares Outstanding**

This is used as X4 in the Classic Z-Score model (Type 1).

### 3.3 Limitations

Because Yahoo Finance data is sourced from public filings and may lag or differ slightly from primary filings on EDGAR, the figures should be treated as indicative rather than audited. For production credit decisions, data should be sourced directly from audited annual reports.

---

## 5. Model 1 — Altman Z-Score (Classic, Z)

### 4.1 Background

The original Z-Score model was developed by Edward I. Altman in 1968 and revisited in 2000 [1]. It uses Multiple Discriminant Analysis (MDA) to combine five financial ratios into a single score that separates bankrupt from non-bankrupt manufacturing firms. The model was originally calibrated on a sample of 66 manufacturing firms (33 bankrupt, 33 non-bankrupt) with total assets between $1 million and $25 million, drawn from the period 1946–1965.

### 4.2 Formula

$$Z = 1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 1.0 X_5$$

### 4.3 Variables

| Variable | Definition | Interpretation |
|---|---|---|
| X1 | Working Capital / Total Assets | Liquidity relative to asset base |
| X2 | Retained Earnings / Total Assets | Cumulative profitability; implicit leverage measure |
| X3 | EBIT / Total Assets | Productivity of assets, independent of tax and leverage |
| X4 | **Market Value of Equity** / Book Value of Total Liabilities | Market-based solvency buffer |
| X5 | Total Revenue / Total Assets | Asset turnover (sales-generating efficiency) |

As Altman (2000) explains, X4 uses **market value of equity** — combining preferred and common shares — which adds a forward-looking market dimension absent from book-value approaches [1]. X3 is noted as the most robust individual predictor because it measures the firm's earning power independently of financing decisions.

### 4.4 Classification Thresholds

| Zone | Score Range | Meaning |
|---|---|---|
| **Safe Zone** | Z > 2.99 | Low probability of financial distress |
| **Grey Zone** | 1.81 ≤ Z ≤ 2.99 | Uncertain; further analysis warranted |
| **Distress Zone** | Z < 1.81 | High probability of financial distress |

The "Grey Zone" (also called the "zone of ignorance" by Altman) is the range where the model's classification accuracy diminishes and misclassifications are most likely to occur. Altman (2000) recommends using **1.81 as the conservative lower cutoff**, noting that in the most recent tests (1997–1999) the model achieved 94% accuracy at the 2.67 cutoff and 84% at the 1.81 cutoff [1].

### 4.5 Applicable Firm Type

This model is designed for **publicly traded manufacturing firms** (Type 1). It requires market equity data and is therefore not directly applicable to private firms.

### 4.6 Credit Interpretation

- A firm with **Z > 2.99** is considered financially healthy; credit risk is low.
- A firm in the **Grey Zone** requires qualitative review; the quantitative signal alone is inconclusive.
- A firm with **Z < 1.81** signals serious financial difficulty; credit extension is not recommended based on this model alone.

---

## 6. Model 2 — Altman Z'-Score (Revised for Private Firms)

### 5.1 Background

The Z'-Score was developed by Altman (2000) as a direct response to practitioners who needed to apply the Z-Score to **private companies**, where market equity is unavailable [1]. Rather than simply substituting book equity into the original formula, Altman re-estimated the entire discriminant function from scratch. This produces different coefficients for all variables, not just X4.

### 5.2 Formula

$$Z' = 0.717 X_1 + 0.847 X_2 + 3.107 X_3 + 0.420 X_4 + 0.998 X_5$$

### 5.3 Key Modification

X4 is redefined as:

> **X4 = Book Value of Stockholders' Equity / Book Value of Total Liabilities**

This replaces market equity with book equity, making the model applicable to firms without publicly traded shares. As Altman (2000) notes, the coefficient for the modified X4 drops from 0.6 to 0.42, reflecting a reduced discriminating contribution when the market dimension is removed [1].

### 5.4 Classification Thresholds

| Zone | Score Range |
|---|---|
| **Safe Zone** | Z' > 2.6 |
| **Grey Zone** | 1.1 ≤ Z' ≤ 2.6 |
| **Distress Zone** | Z' < 1.1 |

The grey area is wider than in the original model (1.1 to 2.6 vs. 1.81 to 2.99), reflecting increased uncertainty when book values replace market values.

### 5.5 Applicable Firm Type

Designed for **private or non-manufacturing firms** (Type 2) where market equity is not observable.

### 5.6 Credit Interpretation

- **Z' > 2.6:** Strong financial position; credit risk is low.
- **1.1 ≤ Z' ≤ 2.6:** Ambiguous signal; supplemental analysis required.
- **Z' < 1.1:** Firm is in financial distress; credit dismissal is warranted.

---

## 7. Model 3 — Altman Z''-Score (Emerging Markets)

### 6.1 Background

The Z''-Score model was developed by Altman, Hartzell, and Peck (1995) and presented in the 2000 paper to evaluate **emerging market corporates**, initially applied to Mexican firms issuing dollar-denominated Eurobonds [1]. The key modification relative to Z' is the **elimination of X5 (Sales/Total Assets)**. This is deliberate: asset turnover varies significantly across industries and could introduce systematic bias when comparing firms from different sectors or countries. The model also uses a constant of +3.25 to calibrate scores against U.S. bond-rating equivalents.

### 6.2 Formula (as implemented)

$$Z'' = 6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4$$

> Note: The implementation does not include the +3.25 constant, as the thresholds used are the standard distress/safe boundaries rather than bond-rating equivalents.

### 6.3 Variables

Same definitions as the Z'-Score (X1–X4), with **book value of equity** used for X4 and **X5 excluded**.

### 6.4 Classification Thresholds

| Zone | Score Range |
|---|---|
| **Safe Zone** | Z'' > 2.6 |
| **Grey Zone** | 1.1 ≤ Z'' ≤ 2.6 |
| **Distress Zone** | Z'' < 1.1 |

Altman (2000) provides a bond-rating equivalent table mapping Z'' scores to U.S. credit ratings (e.g., a score of 8.15 corresponds to AAA, 5.85 to BBB) [1].

### 6.5 Applicable Firm Type

Designed for **emerging market companies** (Type 3) where industry-specific asset turnover and book-value equity are the appropriate inputs.

### 6.6 Credit Interpretation

- **Z'' > 2.6:** The firm is in a safe financial position; consistent with investment-grade credit quality.
- **1.1 ≤ Z'' ≤ 2.6:** Uncertain zone; equivalent to a sub-investment-grade or speculative rating.
- **Z'' < 1.1:** High distress probability; credit extension is not recommended.

---

## 8. Model 4 — Merton Distance-to-Default Model

### 7.1 Background

The Merton model (1974) is a **structural model of credit risk** that views a firm's equity as a call option on its assets, with the debt face value as the strike price. If the firm's asset value falls below the value of its debt at maturity, the firm defaults. The key output is the **Distance to Default (DD)** — the number of standard deviations that the firm's asset value is away from the default point — and the corresponding **probability of default (PD)**.

Unlike the Altman models, the Merton model is inherently **forward-looking and market-based**, using asset volatility to measure the likelihood of a credit event.

### 7.2 Implementation

In this project, the Merton model is approximated using annual balance sheet data as a proxy for asset values:

- **Asset value (V):** Total Assets from the most recent balance sheet.
- **Default barrier (D):** Current Liabilities from the most recent balance sheet.
- **Asset volatility (σ):** Standard deviation of the year-over-year percentage change in Total Assets across the four most recent annual periods.
- **Risk-free rate (r):** Fixed at 4% per annum.
- **Time horizon (T):** 2 years.

The distance to default is computed as:

$$DD = \frac{\left(\ln\frac{V}{D} + \left(r - \frac{\sigma^2}{2}\right) T\right)}{\sigma \sqrt{T}}$$

And the probability of default:

$$PD = 1 - \Phi(DD)$$

where $\Phi$ is the standard normal CDF.

### 7.3 Classification Thresholds

| Zone | Condition | Interpretation |
|---|---|---|
| **Safe Zone** | PD < 1% | Very low probability of default |
| **Grey Zone** | 1% ≤ PD < 15% | Moderate uncertainty |
| **Distress Zone** | PD ≥ 15% | Elevated default risk |

### 7.4 Credit Interpretation

- **PD < 1%:** The firm is far from its default boundary; structural credit risk is negligible.
- **1% ≤ PD < 15%:** There is some structural distance to default, but uncertainty is non-trivial; the signal should be read in conjunction with the Altman score.
- **PD ≥ 15%:** The firm's asset value is dangerously close to the debt boundary; structural default risk is high, regardless of the accounting-based signal.

---

## 9. Combined Credit Decision Logic

Because accounting-based models (Altman) and market-based structural models (Merton) capture different dimensions of credit risk, neither alone is sufficient. The system combines both signals into a single credit recommendation using the following rule matrix:

| Altman Zone | Merton Zone | Credit Decision |
|---|---|---|
| Safe Zone | Safe Zone | **Approved** |
| Safe Zone | Grey Zone | **Approved with Caution** |
| Grey Zone | Safe Zone | **Approved with Caution** |
| Grey Zone | Grey Zone | **Analysis Required** |
| Distress Zone | *any* | **Dismissed** |
| *any* | Distress Zone | **Dismissed** |

The logic is conservative: **any distress signal from either model immediately results in dismissal**. This reflects the asymmetric cost of credit losses — the cost of a missed default far exceeds the opportunity cost of a declined credit.

---

## 10. Version of the Z-Score Formula Used and Justification

This project implements **three versions** of the Altman Z-Score, as described in Altman (2000) [1], and selects among them based on the declared firm type:

| Type Code | Model | Formula | X4 Definition |
|---|---|---|---|
| 1 | Classic Z-Score (1968) | Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5 | Market Value of Equity / Total Liabilities |
| 2 | Revised Z'-Score (2000) | Z' = 0.717X1 + 0.847X2 + 3.107X3 + 0.420X4 + 0.998X5 | Book Value of Equity / Total Liabilities |
| 3 | Emerging Markets Z''-Score (1995/2000) | Z'' = 6.56X1 + 3.26X2 + 6.72X3 + 1.05X4 | Book Value of Equity / Total Liabilities |

**Justification for using the convenient scaled form of the Classic Z-Score:**
The original 1968 paper expressed the formula as `Z = 0.012X1 + 0.014X2 + 0.033X3 + 0.006X4 + 0.999X5`, where X1–X4 were entered as full percentages (e.g., 10 for 10%). Altman himself acknowledges in the 2000 paper that "a more convenient specification of the model is of the form: Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 1.0X5," where the ratios are entered as decimals (e.g., 0.10 for 10%) [1]. Both formulations are mathematically identical and produce the same classifications. This project uses the **scaled decimal form** — which is the de facto standard in modern applications — as it is more consistent with how financial ratios are computed programmatically.

**Justification for the multi-model approach:**
Altman (2000) explicitly states that the Classic Z-Score is valid only for publicly traded manufacturing firms, the Z'-Score for private or non-manufacturing firms, and the Z''-Score for emerging market entities [1]. Using a single formula for all firm types would produce misleading results. The multi-model architecture in this project directly implements the recommendation from the source paper.

---

## 11. References

[1] Altman, E. I. (2000). *Predicting Financial Distress of Companies: Revisiting the Z-Score and ZETA® Models*. Working Paper, Stern School of Business, New York University. (Adapted and updated from: Altman, E. I. (1968). Financial ratios, discriminant analysis and the prediction of corporate bankruptcy. *Journal of Finance*, September 1968; and Altman, E. I., Haldeman, R., & Narayanan, P. (1977). Zeta analysis: A new model to identify bankruptcy risk of corporations. *Journal of Banking & Finance*, 1.)

[2] Merton, R. C. (1974). On the pricing of corporate debt: The risk structure of interest rates. *Journal of Finance*, 29(2), 449–470.

[3] Yahoo Finance. (2026). Financial statements data retrieved via the `yfinance` Python library (v0.2.x). Available at: https://github.com/ranaroussi/yfinance

[4] Altman, E. I., Hartzell, J., & Peck, M. (1995). Emerging markets corporate bonds: A scoring system. *Salomon Brothers*, New York. (Reprinted in Altman (2000).)
