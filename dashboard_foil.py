import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard - Company A")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # ---------- HELPERS ----------
    def find_column(keyword):
        for col in df.columns:
            if keyword.lower() in col.lower():
                return col
        return None

    def format_percent(val):
        if pd.isna(val):
            return "-"
        return f"{val:.0f}%"

    # ---------- COLUMN DETECTION ----------
    col_brand = find_column("brand")
    col_desc = find_column("article")

    col_val_2025 = [c for c in df.columns if "2025" in c and "value" in c.lower()][0]
    col_val_2026 = [c for c in df.columns if "2026" in c and "value" in c.lower()][0]
    col_qty_2025 = [c for c in df.columns if "2025" in c and "quantity" in c.lower()][0]
    col_qty_2026 = [c for c in df.columns if "2026" in c and "quantity" in c.lower()][0]

    # ---------- FILTER ----------
    df["Category"] = df[col_desc].astype(str).str.lower().apply(
        lambda x: "Foil" if "foil" in x else "Other"
    )
    df = df[df["Category"] == "Foil"]

    st.success("Dataset filtered: Foil balloons only")

    # ================= KPI =================
    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()
    qty_2025 = df[col_qty_2025].sum()
    qty_2026 = df[col_qty_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 * 100 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 * 100 if qty_2025 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales 2025 (€)", f"{sales_2025:,.0f}")
    c2.metric("Sales 2026 (€)", f"{sales_2026:,.0f}", f"{yoy_sales:.0f}%")
    c3.metric("Quantity 2025", f"{qty_2025:,.0f}")
    c4.metric("Quantity 2026", f"{qty_2026:,.0f}", f"{yoy_qty:.0f}%")

    st.divider()

    # ================= ALERT =================
    st.subheader("🚨 Sales Alerts")
    st.caption("Comparison: 2026 vs 2025")

    if yoy_sales < -20:
        st.error("Sales decline > 20%")
    elif yoy_sales > 20:
        st.success("Sales growth > 20%")
    else:
        st.info("Stable performance")

    st.divider()

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({
        col_val_2025: "sum",
        col_val_2026: "sum",
        col_qty_2025: "sum",
        col_qty_2026: "sum"
    }).reset_index()

    brand["Share 2025 (%)"] = brand[col_val_2025] / brand[col_val_2025].sum() * 100
    brand["Share 2026 (%)"] = brand[col_val_2026] / brand[col_val_2026].sum() * 100

    brand["YoY Value (%)"] = ((brand[col_val_2026] - brand[col_val_2025]) / brand[col_val_2025]) * 100
    brand["YoY Qty (%)"] = ((brand[col_qty_2026] - brand[col_qty_2025]) / brand[col_qty_2025]) * 100

    brand = brand.replace([float("inf")], 100)
    brand = brand.sort_values(col_val_2026, ascending=False).reset_index(drop=True)
    brand.index = brand.index + 1

    # charts
    st.plotly_chart(px.bar(brand, x=col_brand,
                           y=[col_val_2025, col_val_2026],
                           barmode="group",
                           title="Sales by Brand (€)"),
                    use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2025,
                               title="Brand Share 2025 (%)"))
    with colB:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2026,
                               title="Brand Share 2026 (%)"))

    # format %
    brand_display = brand.copy()
    for col in ["Share 2025 (%)", "Share 2026 (%)", "YoY Value (%)", "YoY Qty (%)"]:
        brand_display[col] = brand_display[col].apply(format_percent)

    st.dataframe(brand_display)

    st.divider()

    # ================= PRODUCTS IN BRAND =================
    st.subheader("📊 Top Products within Brand")

    selected_brand = st.selectbox("Select Brand", df[col_brand].dropna().unique())

    df_brand = df[df[col_brand] == selected_brand]

    prod = df_brand.groupby(col_desc).agg({
        col_val_2025: "sum",
        col_val_2026: "sum",
        col_qty_2025: "sum",
        col_qty_2026: "sum"
    }).reset_index()

    prod = prod.sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
    prod.index = prod.index + 1

    st.dataframe(prod)

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products 2026")

    top_2026 = df.sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
    top_2026.index = top_2026.index + 1

    st.dataframe(top_2026[[col_desc, col_brand, col_val_2026, col_qty_2026]])

    st.subheader("🏆 Top Products 2025")

    top_2025 = df.sort_values(col_val_2025, ascending=False).head(10).reset_index(drop=True)
    top_2025.index = top_2025.index + 1

    st.dataframe(top_2025[[col_desc, col_brand, col_val_2025, col_qty_2025]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY Analysis")

    yoy = df[[col_desc, col_brand, col_val_2025, col_val_2026, col_qty_2025, col_qty_2026]].copy()

    yoy["YoY Value (%)"] = ((yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]) * 100
    yoy["YoY Qty (%)"] = ((yoy[col_qty_2026] - yoy[col_qty_2025]) / yoy[col_qty_2025]) * 100

    yoy = yoy.replace([float("inf")], 100)
    yoy = yoy.sort_values(col_val_2026, ascending=False).reset_index(drop=True)
    yoy.index = yoy.index + 1

    yoy_display = yoy.copy()
    yoy_display["YoY Value (%)"] = yoy_display["YoY Value (%)"].apply(format_percent)
    yoy_display["YoY Qty (%)"] = yoy_display["YoY Qty (%)"].apply(format_percent)

    st.dataframe(yoy_display.head(15))

    st.divider()

    # ================= RISK =================
    st.subheader("📉 Risk Detection")

    risk = df.sort_values(col_val_2025, ascending=False).head(20)
    risk = risk[risk[col_val_2026] < risk[col_val_2025]]

    risk["YoY (%)"] = ((risk[col_val_2026] - risk[col_val_2025]) / risk[col_val_2025]) * 100
    risk = risk.replace([float("inf")], 100)
    risk = risk.sort_values("YoY (%)").reset_index(drop=True)
    risk.index = risk.index + 1

    risk_display = risk.copy()
    risk_display["YoY (%)"] = risk_display["YoY (%)"].apply(format_percent)

    st.dataframe(risk_display[[col_desc, col_brand, col_val_2025, col_val_2026, "YoY (%)"]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    portfolio = df.sort_values(col_val_2026, ascending=False)
    total = portfolio[col_val_2026].sum()

    top10 = portfolio.head(10)
    share = top10[col_val_2026].sum() / total * 100

    st.metric("Top 10 Share", f"{share:.0f}%")

    if share > 70:
        st.warning("High concentration risk")
    elif share > 50:
        st.info("Moderate concentration")
    else:
        st.success("Diversified portfolio")
