# BigQuery and Looker Studio

Replace `YOUR_PROJECT.YOUR_DATASET` in both SQL files with your project and dataset IDs. Create the dataset, run `schema.sql`, then load each generated CSV into its same-named table using the BigQuery UI or `bq load` with CSV autodetect disabled. The schema lists the intended types. Example:

```bash
bq load --source_format=CSV --skip_leading_rows=1 YOUR_PROJECT:YOUR_DATASET.forecasts data/processed/forecasts.csv
bq load --source_format=CSV --skip_leading_rows=1 YOUR_PROJECT:YOUR_DATASET.recommendations data/processed/recommendations.csv
bq load --source_format=CSV --skip_leading_rows=1 YOUR_PROJECT:YOUR_DATASET.model_metrics data/processed/model_metrics.csv
bq load --source_format=CSV --skip_leading_rows=1 YOUR_PROJECT:YOUR_DATASET.daily_sales data/processed/daily_sales.csv
```

Run `dashboard_views.sql`, then add a BigQuery source to Looker Studio using `inventory_dashboard`. Suggested charts: high-risk items by store/category, budget-limited units, planned spend, and forecast interval by date. This demo does not create cloud resources or upload data automatically.
