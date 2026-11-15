# Retail Demand Forecasting & Inventory Decision Intelligence

A reproducible end-to-end demo that generates synthetic retail demand, compares forecasting models with rolling-origin validation, turns predictions into replenishment recommendations, and exposes results in a Streamlit dashboard. The pipeline also writes BigQuery-ready CSVs and SQL so the same outputs can power Looker Studio.

> All data is synthetic. Reported model metrics and simulated cost savings are demo outputs, not claims about a real retailer.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m src.pipeline --days 730 --stores 20 --products 30 --seed 42
streamlit run app.py
```

The default is intentionally modest for a laptop. Use `--stores 200 --products 30 --days 730` for about 4.4 million store-product-day rows; use `--stores 200 --products 7` for roughly one million rows.

## What it does

1. `src/data.py` creates demand with store/product effects, weekly and yearly seasonality, trend, promotions, price changes, and intermittent noise. It creates inventory snapshots, supplier lead times, costs, and service targets.
2. `src/features.py` builds calendar, lag, rolling, price, promotion, and item/store features. Lags are shifted so future demand cannot leak into training features.
3. `src/forecast.py` compares seasonal-naive and moving-average baselines with Random Forest and (when installed) XGBoost using expanding-window validation. It reports MAE, RMSE, and WAPE.
4. `src/inventory.py` estimates lead-time demand and uncertainty, computes safety stock and reorder points, and applies MOQ, pack size, budget, and supplier capacity constraints.
5. `src/pipeline.py` writes forecasts, recommendations, metrics, and daily aggregates to `data/processed/` as CSV. `sql/` contains BigQuery DDL and a dashboard view.
6. `app.py` provides store/category/risk filters, service-level and budget scenario controls, KPI cards, risk prioritization, forecast views, and downloadable CSVs.

## Outputs

- `data/processed/forecasts.csv` — one row per store-product and forecast date, with point forecast and a simple uncertainty interval.
- `data/processed/recommendations.csv` — on-hand, lead-time demand, safety stock, reorder point, proposed order, risk, and estimated order cost.
- `data/processed/model_metrics.csv` — time-split validation metrics by model and fold.
- `data/processed/daily_sales.csv` — compact dashboard trend data.

## BigQuery and Looker Studio

Create a dataset, load the processed CSV files into tables named `forecasts`, `recommendations`, `model_metrics`, and `daily_sales`, then run `sql/dashboard_views.sql`. The view `inventory_dashboard` is a simple Looker Studio source. See `sql/README.md` for load instructions. Cloud credentials are not required for local use.

## Configuration

```bash
python -m src.pipeline --help
```

The pipeline accepts row scale, seed, forecast horizon, and output directory arguments. Optional XGBoost is installed from `requirements.txt`; if unavailable, the pipeline continues with the other models. To keep runtime reasonable, the tree models train on a sampled subset while validation remains chronological.

## Project layout

```text
app.py                 Streamlit decision-support dashboard
src/                   Data generation, features, forecasting, optimization, pipeline
sql/                   BigQuery tables and dashboard view
data/processed/        Generated outputs (gitignored)
```

## Assumptions and limitations

- Synthetic data has no real-world causal meaning. Promotion and price effects are generated, not estimated from business data.
- The order quantity is a single-period policy recommendation, not a multi-echelon or full purchase-order optimizer.
- Uncertainty uses validation residual dispersion and a normal approximation; calibrate intervals against real data before operational use.
- Stockout flags in simulated history are latent approximations; observed sales can be censored by stock availability in actual systems.
- BigQuery loading and Looker Studio configuration are documented but require the user's Google Cloud project and credentials.

## License

MIT. See `LICENSE`.
