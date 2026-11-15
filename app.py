from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Retail Inventory Intelligence", page_icon="📦", layout="wide")
st.title("📦 Retail Demand & Inventory Intelligence")
st.caption("Interactive planning workbench · Synthetic demo data")
ROOT = Path(__file__).parent / "data" / "processed"

@st.cache_data
def load(name):
    path = ROOT / f"{name}.csv"
    return pd.read_csv(path, parse_dates=["date"] if name in ("forecasts", "daily_sales") else None) if path.exists() else pd.DataFrame()

rec, fc, daily, metrics = (load(n) for n in ("recommendations", "forecasts", "daily_sales", "model_metrics"))
if rec.empty or fc.empty:
    st.warning("No pipeline outputs found. Run `python -m src.pipeline` from the repository root, then refresh.")
    st.stop()
st.sidebar.header("Planning controls")
stores, categories = sorted(rec.store_id.unique()), sorted(rec.category.unique())
selected_stores = st.sidebar.multiselect("Stores", stores, default=stores)
selected_categories = st.sidebar.multiselect("Categories", categories, default=categories)
service_level = st.sidebar.slider("Target service level", 0.80, 0.99, 0.95, 0.01, help="Higher service levels add safety stock and may increase recommended orders.")
budget = st.sidebar.number_input("Purchasing budget ($)", min_value=0.0, value=0.0, step=500.0, help="Set to zero for an unconstrained recommendation.")
max_lead = int(fc.lead_time_days.max())
lead_horizon = st.sidebar.slider("Forecast display horizon (days)", 1, max(1, len(fc.date.unique())), min(7, max(1, len(fc.date.unique()))))
risk = st.sidebar.selectbox("Risk filter", ["ALL", "HIGH", "MEDIUM", "LOW"])
filtered = rec[rec.store_id.isin(selected_stores) & rec.category.isin(selected_categories)].copy()
if risk != "ALL":
    levels = {"HIGH": ["HIGH"], "MEDIUM": ["HIGH", "MEDIUM"], "LOW": ["LOW"]}
    filtered = filtered[filtered.stockout_risk.isin(levels[risk])]
from src.inventory import optimize_replenishment
scenario = optimize_replenishment(fc, service_level=service_level, budget=budget if budget > 0 else None)
scenario = scenario[scenario.store_id.isin(selected_stores) & scenario.category.isin(selected_categories)]
if risk != "ALL":
    scenario = scenario[scenario.stockout_risk.isin(levels[risk])]
scenario["budget_limited_qty"] = scenario.recommended_order_qty
if budget > 0:
    remaining = budget
    for ix, row in scenario.sort_values("priority_score", ascending=False).iterrows():
        pack = max(1, int(row.pack_size))
        qty = min(int(row.recommended_order_qty), int(remaining // max(float(row.unit_cost), 0.01)) // pack * pack)
        scenario.loc[ix, "budget_limited_qty"] = qty
        remaining -= qty * float(row.unit_cost)
a, b, c, d = st.columns(4)
a.metric("Store-product items", f"{len(filtered):,}")
b.metric("High stockout risk", f"{(filtered.stockout_risk == 'HIGH').sum():,}")
c.metric("Scenario order units", f"{scenario.budget_limited_qty.sum():,.0f}")
d.metric("Scenario spend", f"${(scenario.budget_limited_qty * scenario.unit_cost).sum():,.0f}")
left, right = st.columns([1.3, 1])
with left:
    st.subheader("Demand trend")
    if not daily.empty:
        st.plotly_chart(px.line(daily, x="date", y="sales_units", title="Simulated daily units sold"), use_container_width=True)
with right:
    st.subheader("Replenishment risk")
    risk_counts = scenario.groupby("stockout_risk", as_index=False).agg(items=("product_id", "count"), units=("budget_limited_qty", "sum"))
    st.plotly_chart(px.bar(risk_counts, x="stockout_risk", y="items", color="stockout_risk", title="Items by risk tier"), use_container_width=True)
st.subheader("Scenario comparison")
base_spend = float(scenario.recommended_order_qty.mul(scenario.unit_cost).sum())
actual_spend = float(scenario.budget_limited_qty.mul(scenario.unit_cost).sum())
x, y, z = st.columns(3)
x.metric("Unconstrained order value", f"${base_spend:,.0f}")
y.metric("Budget-constrained spend", f"${actual_spend:,.0f}", delta=f"${actual_spend-base_spend:,.0f}")
z.metric("Items still below reorder point", f"{(scenario.on_hand < scenario.reorder_point).sum():,}")
st.caption(f"Recommendations use a {service_level:.0%} service target and supplier lead times. Orders respect supplier capacity, MOQ, and pack size. Forecast charts show the next {lead_horizon} available days.")
st.subheader("Priority queue")
st.dataframe(scenario.sort_values("priority_score", ascending=False).head(100), use_container_width=True, hide_index=True)
st.subheader("Forecast detail")
store = st.selectbox("Store", selected_stores or stores)
items = sorted(fc.loc[fc.store_id == store, "product_id"].unique())
if items:
    item = st.selectbox("Product", items)
    series = fc[(fc.store_id == store) & (fc.product_id == item)].sort_values("date").head(lead_horizon)
    chart = px.line(series, x="date", y="forecast", title=f"Demand forecast · Store {store} · Product {item}")
    chart.add_scatter(x=series.date, y=series.upper_95, mode="lines", line={"width": 0}, showlegend=False, name="upper")
    chart.add_scatter(x=series.date, y=series.lower_95, mode="lines", fill="tonexty", line={"width": 0}, fillcolor="rgba(31,119,180,0.15)", name="95% interval")
    st.plotly_chart(chart, use_container_width=True)
if not metrics.empty:
    st.subheader("Rolling validation results")
    summary = metrics.groupby("model", as_index=False).agg(mean_wape=("wape", "mean"), mean_mae=("mae", "mean"), mean_rmse=("rmse", "mean"))
    st.dataframe(summary.sort_values("mean_wape"), hide_index=True, use_container_width=True)
st.download_button("Download filtered recommendations", filtered.to_csv(index=False).encode(), "recommendations.csv", "text/csv")
st.download_button("Download forecasts", fc.to_csv(index=False).encode(), "forecasts.csv", "text/csv")
