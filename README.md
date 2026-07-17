# Telecom Demand Forecasting from Weather Conditions

Final Degree Project (TFG) — Bachelor's Degree in Computer Engineering, Universitat Politècnica de València (2024–2025). Grade: 9.5/10.

## Problem

A telecommunications field-service company (installations, maintenance, repairs) sees its number of daily work orders swing significantly with the weather. Without a way to anticipate this, planning staff and materials is hard: quiet days leave technicians idle, while spikes leave the company short-handed — both of which raise costs and hurt service. The goal of this project is to **forecast daily work-order demand from weather conditions**, so the company can plan resources ahead and operate more efficiently.

## Data

- Historical work orders provided by the company, filtered to the city of Valencia (QGIS was used for the geographic filtering).
- Operator movement records.
- Daily weather for Valencia — temperature, precipitation and wind — from Meteostat.

> The company's raw operational data is confidential and is **not** included in this repository.

## Approach

- **ETL & exploratory analysis:** cleaning, geographic filtering to Valencia, and weekly aggregation. Precipitation turned out to be the main driver of demand; temperature and wind showed no clear relationship and were dropped.
- **Feature engineering:** mean and weighted rolling precipitation, plus weekend and holiday indicators.
- **Models compared:** Random Forest Regressor, Gradient Boosting and XGBoost. **XGBoost** gave the best results and was chosen as the final model.
- **Deployment:** a Flask web app and API serve the model, applying rule-based adjustments for weekends and holiday periods; SQLite stores the prediction history.

## Results

Prediction error was reduced step by step:

| Stage | RMSE | MAE |
|---|---|---|
| Baseline (previous-day precipitation) | 82 | 44 |
| + engineered precipitation features | 60 | 35 |
| + API weekend/holiday adjustments | 26 | 20 |

## Tech stack

Python (pandas, NumPy, scikit-learn, XGBoost, Matplotlib, Seaborn, Joblib), Google Colab, Flask, SQLite.
