CREATE OR REPLACE VIEW `YOUR_PROJECT.YOUR_DATASET.inventory_dashboard` AS
SELECT r.store_id, r.product_id, r.category, r.stockout_risk, r.priority_score,
 r.on_hand, r.lead_time_demand, r.safety_stock, r.reorder_point,
 r.recommended_order_qty, r.budget_limited_qty, r.unit_cost,
 r.budget_limited_qty * r.unit_cost AS planned_spend,
 f.date AS forecast_date, f.forecast, f.lower_95, f.upper_95, f.model
FROM `YOUR_PROJECT.YOUR_DATASET.recommendations` r
LEFT JOIN `YOUR_PROJECT.YOUR_DATASET.forecasts` f USING (store_id, product_id);
