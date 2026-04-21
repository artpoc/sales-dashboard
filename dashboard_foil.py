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
    st.markdown("### 💰 All values are in EURO (€) | 📦 Quantities in PCS")

    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()
    qty_2025 = df[col_qty_2025].sum()
    qty_2026 = df[col_qty_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 * 100 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 * 100 if qty_2025 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales 2025 (€)", f"{sales_2025:,.0f}")
    c2.metric("Sales 2026 (€)", f"{sales_2026:,.0f}", f"{yoy_sales:.0f}%")
    c3.metric("Quantity 2025 (PCS)", f"{qty_2025:,.0f}")
    c4.metric("Quantity 2026 (PCS)", f"{qty_2026:,.0f}", f"{yoy_qty:.0f}%")

    st.divider()

    # ================= ALERT =================
    st.subheader("🚨 Sales Alerts")
    st.caption("Comparison: 2026 vs 2025")

    if yoy_sales < -20:
        st.error(f"Sales decline >20% (Actual: {yoy_sales:.0f}%)")
    elif yoy_sales > 20:
        st.success(f"Sales growth >20% (Actual: {yoy_sales:.0f}%)")
    else:
        st.info(f"Threshold ±20% NOT exceeded (Actual: {yoy_sales:.0f}%)")

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

    # 📊 BAR
    st.plotly_chart(
        px.bar(brand, x=col_brand, y=[col_val_2025, col_val_2026],
               barmode="group", title="Sales by Brand (€)"),
        use_container_width=True
    )

    # 🥧 PIE 2025 / 2026
    colA, colB = st.columns(2)

    with colA:
        st.plotly_chart(
            px.pie(brand, names=col_brand, values=col_val_2025,
                   title="Brand Share 2025 (%)"),
            use_container_width=True
        )

    with colB:
        st.plotly_chart(
            px.pie(brand, names=col_brand, values=col_val_2026,
                   title="Brand Share 2026 (%)"),
            use_container_width=True
        )

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

    st.write("Top Products 2026 (€ & PCS)")
    prod_2026 = df_brand.sort_values(col_val_2026, ascending=False).head(10)
    prod_2026.index = range(1, len(prod_2026) + 1)
    st.dataframe(prod_2026[[col_desc, col_val_2026, col_qty_2026]])

    st.write("Top Products 2025 (€ & PCS)")
    prod_2025 = df_brand.sort_values(col_val_2025, ascending=False).head(10)
    prod_2025.index = range(1, len(prod_2025) + 1)
    st.dataframe(prod_2025[[col_desc, col_val_2025, col_qty_2025]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY Analysis")

    yoy = df.copy()
    yoy["YoY Value (%)"] = ((yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]) * 100
    yoy["YoY Qty (%)"] = ((yoy[col_qty_2026] - yoy[col_qty_2025]) / yoy[col_qty_2025]) * 100

    yoy = yoy.replace([float("inf")], 100)

    st.write("Top by Sales Value 2026")
    yoy_val = yoy.sort_values(col_val_2026, ascending=False).head(10)
    yoy_val["YoY Value (%)"] = yoy_val["YoY Value (%)"].apply(format_percent)
    st.dataframe(yoy_val[[col_desc, col_val_2026, "YoY Value (%)"]])

    st.write("Top by Quantity 2026")
    yoy_qty_df = yoy.sort_values(col_qty_2026, ascending=False).head(10)
    yoy_qty_df["YoY Qty (%)"] = yoy_qty_df["YoY Qty (%)"].apply(format_percent)
    st.dataframe(yoy_qty_df[[col_desc, col_qty_2026, "YoY Qty (%)"]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    portfolio = df.sort_values(col_val_2026, ascending=False)
    top10 = portfolio.head(10)

    top10.index = range(1, len(top10) + 1)
    st.dataframe(top10[[col_desc, col_val_2026]])

    st.plotly_chart(
        px.pie(top10, names=col_desc, values=col_val_2026,
               title="Top 10 Products Share (2026 €)"),
        use_container_width=True
    )

    share = top10[col_val_2026].sum() / df[col_val_2026].sum() * 100

    st.metric("Top 10 Share (%)", f"{share:.0f}%")

    if share > 70:
        st.warning("High concentration risk")
    elif share > 50:
        st.info("Moderate concentration")
    else:
        st.success("Diversified portfolio")
