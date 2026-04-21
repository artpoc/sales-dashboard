import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard - Company A")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Detect columns
    def find_column(keyword):
        for col in df.columns:
            if keyword.lower() in col.lower():
                return col
        return None

    col_brand = find_column("brand")
    col_desc = find_column("article")
    col_val_2025 = [c for c in df.columns if "2025" in c and "value" in c.lower()][0]
    col_val_2026 = [c for c in df.columns if "2026" in c and "value" in c.lower()][0]
    col_qty_2025 = [c for c in df.columns if "2025" in c and "quantity" in c.lower()][0]
    col_qty_2026 = [c for c in df.columns if "2026" in c and "quantity" in c.lower()][0]

    # Filter Foil
    df["Category"] = df[col_desc].astype(str).str.lower().apply(
        lambda x: "Foil" if "foil" in x else "Other"
    )
    df = df[df["Category"] == "Foil"]

    st.success("Dataset filtered: Foil balloons only")

    # ================= KPI =================
    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 if sales_2025 else 0

    c1, c2 = st.columns(2)
    c1.metric("Sales 2025 (€)", f"{sales_2025:,.0f} €")
    c2.metric("Sales 2026 (€)", f"{sales_2026:,.0f} €", f"{yoy_sales:.0%} YoY")

    st.divider()

    # ================= ALERTS =================
    st.subheader("🚨 Sales Alerts")
    st.caption("Comparison basis: Sales 2026 vs Sales 2025 (Year-over-Year)")

    if yoy_sales < -0.2:
        st.error("Sales decline > 20% (YoY 2026 vs 2025)")
    elif yoy_sales > 0.2:
        st.success("Sales growth > 20% (YoY 2026 vs 2025)")
    else:
        st.info("Stable sales (YoY 2026 vs 2025)")

    st.divider()

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance (2026 as reference)")

    brand_df = df.groupby(col_brand).agg({
        col_val_2025: "sum",
        col_val_2026: "sum"
    }).reset_index()

    brand_df["Share 2025 (%)"] = (brand_df[col_val_2025] / brand_df[col_val_2025].sum()) * 100
    brand_df["Share 2026 (%)"] = (brand_df[col_val_2026] / brand_df[col_val_2026].sum()) * 100
    brand_df["YoY (%)"] = ((brand_df[col_val_2026] - brand_df[col_val_2025]) / brand_df[col_val_2025]) * 100

    brand_df["YoY (%)"] = brand_df["YoY (%)"].replace([float("inf")], 100)

    brand_df = brand_df.sort_values(col_val_2026, ascending=False).reset_index(drop=True)
    brand_df.index = brand_df.index + 1

    st.dataframe(brand_df)

    st.divider()

    # ================= PRODUCTS IN BRAND =================
    st.subheader("📊 Top Products within Brand (Value €)")

    selected_brand = st.selectbox("Select Brand", df[col_brand].dropna().unique())

    df_brand = df[df[col_brand] == selected_brand]

    prod = df_brand.groupby(col_desc).agg({
        col_val_2025: "sum",
        col_val_2026: "sum"
    }).reset_index()

    prod = prod.sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
    prod.index = prod.index + 1

    st.dataframe(prod)

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products 2026 (€)")

    top_2026 = df.sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
    top_2026.index = top_2026.index + 1

    st.dataframe(top_2026[[col_desc, col_brand, col_val_2026]])

    st.subheader("🏆 Top Products 2025 (€)")

    top_2025 = df.sort_values(col_val_2025, ascending=False).head(10).reset_index(drop=True)
    top_2025.index = top_2025.index + 1

    st.dataframe(top_2025[[col_desc, col_brand, col_val_2025]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 Year-over-Year Analysis (2026 vs 2025)")

    yoy = df[[col_desc, col_brand, col_val_2025, col_val_2026]].copy()
    yoy["YoY (%)"] = ((yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]) * 100
    yoy["YoY (%)"] = yoy["YoY (%)"].replace([float("inf")], 100)

    yoy = yoy.sort_values(col_val_2026, ascending=False)

    st.write("🔼 Top Growth Products (based on 2026)")
    growth = yoy.sort_values("YoY (%)", ascending=False).head(10).reset_index(drop=True)
    growth.index = growth.index + 1
    st.dataframe(growth)

    st.write("🔽 Biggest Declines (based on 2026)")
    decline = yoy.sort_values("YoY (%)").head(10).reset_index(drop=True)
    decline.index = decline.index + 1
    st.dataframe(decline)

    st.divider()

    # ================= RISK DETECTION =================
    st.subheader("📉 Risk Detection – Declining Top Products")

    st.caption("Top products from 2025 that are declining in 2026")

    top_2025_full = df.sort_values(col_val_2025, ascending=False).head(20)

    risk_df = top_2025_full[top_2025_full[col_val_2026] < top_2025_full[col_val_2025]].copy()
    risk_df["YoY (%)"] = ((risk_df[col_val_2026] - risk_df[col_val_2025]) / risk_df[col_val_2025]) * 100
    risk_df = risk_df.sort_values("YoY (%)").reset_index(drop=True)
    risk_df.index = risk_df.index + 1

    st.dataframe(risk_df[[col_desc, col_brand, col_val_2025, col_val_2026, "YoY (%)"]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    st.caption("Sales concentration based on 2026 (€)")

    portfolio = df.sort_values(col_val_2026, ascending=False).copy()
    total_sales = portfolio[col_val_2026].sum()

    top10 = portfolio.head(10)
    top10_share = (top10[col_val_2026].sum() / total_sales) * 100

    rest = portfolio.iloc[10:]
    rest_share = (rest[col_val_2026].sum() / total_sales) * 100

    c1, c2 = st.columns(2)
    c1.metric("Top 10 Share (%)", f"{top10_share:.0f}%")
    c2.metric("Remaining Share (%)", f"{rest_share:.0f}%")

    if top10_share > 70:
        st.warning("High concentration risk")
    elif top10_share > 50:
        st.info("Moderate concentration")
    else:
        st.success("Well diversified portfolio")

    st.write("Top 10 Products contributing to 2026 sales")
    top10_display = top10[[col_desc, col_brand, col_val_2026]].copy()
    top10_display = top10_display.reset_index(drop=True)
    top10_display.index = top10_display.index + 1

    st.dataframe(top10_display)
