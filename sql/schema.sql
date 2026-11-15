CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.YOUR_DATASET.forecasts` (
  date DATE, store_id INT64, product_id INT64, category STRING,
  forecast FLOAT64, lower_95 FLOAT64, upper_95 FLOAT64, model STRING,
  lead_time_days INT64, unit_cost FLOAT64, on_hand FLOAT64,
  supplier_capacity INT64, moq INT64, pack_size INT64,
  holding_cost_rate FLOAT64, stockout_penalty FLOAT64, residual_std FLOAT64
);
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.YOUR_DATASET.recommendations` (
  store_id INT64, product_id INT64, category STRING, on_hand FLOAT64,
  lead_time_days INT64, lead_time_demand FLOAT64, demand_std_lead_time FLOAT64,
  safety_stock FLOAT64, reorder_point FLOAT64, recommended_order_qty INT64,
  unit_cost FLOAT64, estimated_order_cost FLOAT64, stockout_risk STRING,
  priority_score FLOAT64, supplier_capacity INT64, moq INT64, pack_size INT64,
  budget_limited_qty INT64
);
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.YOUR_DATASET.model_metrics` (
  model STRING, fold INT64, train_end DATE, valid_start DATE, valid_end DATE,
  mae FLOAT64, rmse FLOAT64, wape FLOAT64
);
CREATE TABLE IF NOT EXISTS `YOUR_PROJECT.YOUR_DATASET.daily_sales` (
  date DATE, sales_units INT64, promo_units INT64, promo_share FLOAT64
);
