import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

# ================= HELPER =================
def yoy_format(v):
    if pd.isna(v):
        return "0%"
    arrow = "🟢 ↑" if v > 0 else "🔴 ↓"
    return f"{v:.0f}% {arrow}"

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # ================= COLUMN MAPPING =================
    col_customer = "Customer Name"
    col_country = "Country"
    col_vat = "Vat ID Nr."

    col_code = "Art. Nr."
    col_desc = "Article description"
    col_brand = "Brand Name"
    col_category = "Category"

    col_val_2025 = "Net Value 2025"
    col_val_2026 = "Net Value 2026"
    col_qty_2025 = "Quantity 2025"
    col_qty_2026 = "Quantity 2026"

    # ================= CUSTOMER =================
    st.subheader("👤 Customer Information")

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
    c2.write(f"**Country:** {df[col_country].iloc[0]}")
    c3.write(f"**VAT ID:** {df[col_vat].iloc[0]}")

    st.divider()

    # ================= CATEGORY (SAFE) =================
    if col_category in df.columns:
        df["Category Clean"] = df[col_category].fillna("").astype(str)
    else:
        df["Category Clean"] = df[col_desc].fillna("").astype(str).str.lower().apply(
            lambda x: "Foil" if "foil" in x else "Other"
        )

    df = df[df["Category Clean"].astype(str).str.lower().str.contains("foil")]
    df = df[df[col_desc].notna()]
    df = df[df[col_desc].astype(str).str.lower() != "none"]

    st.success("Filtered: Foil balloons")

    # ================= KPI =================
    st.markdown("### 💰 EURO (€) | 📦 PCS")

    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()
    qty_2025 = df[col_qty_2025].sum()
    qty_2026 = df[col_qty_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 * 100 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 * 100 if qty_2025 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sales 2025 (€)", f"{sales_2025:,.0f}")
    k2.metric("Sales 2026 (€)", f"{sales_2026:,.0f}", f"{yoy_sales:.0f}%")
    k3.metric("Quantity 2025 (PCS)", f"{qty_2025:,.0f}")
    k4.metric("Quantity 2026 (PCS)", f"{qty_2026:,.0f}", f"{yoy_qty:.0f}%")

    st.divider()

    # ================= SALES ALERT =================
    st.subheader("🚨 Sales Alerts")

    if yoy_sales < -20:
        st.error(f"Sales decline >20% (Actual: {yoy_sales:.0f}%)")
    elif yoy_sales > 20:
        st.success(f"Sales growth >20% (Actual: {yoy_sales:.0f}%)")
    else:
        st.info(f"Stable performance (Actual: {yoy_sales:.0f}%)")

    st.divider()

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({
        col_val_2025: "sum",
        col_val_2026: "sum"
    }).reset_index()

    col1, col2 = st.columns(2)

    with col1:
        st.write("### 2025")
        b = brand.sort_values(col_val_2025, ascending=False).reset_index(drop=True)
        b.index = b.index + 1
        st.plotly_chart(px.pie(b, names=col_brand, values=col_val_2025))
        st.dataframe(b[[col_brand, col_val_2025]])

    with col2:
        st.write("### 2026")
        b = brand.sort_values(col_val_2026, ascending=False).reset_index(drop=True)
        b.index = b.index + 1
        st.plotly_chart(px.pie(b, names=col_brand, values=col_val_2026))
        st.dataframe(b[[col_brand, col_val_2026]])

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products")

    c1, c2 = st.columns(2)

    with c1:
        d = df.sort_values(col_val_2025, ascending=False).head(10).reset_index(drop=True)
        d.index = d.index + 1
        st.dataframe(d[[col_code, col_desc, col_val_2025, col_qty_2025]])

    with c2:
        d = df.sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
        d.index = d.index + 1
        st.dataframe(d[[col_code, col_desc, col_val_2026, col_qty_2026]])

    st.divider()

    # ================= PRODUCTS IN BRAND =================
    st.subheader("📊 Top Products within Brand")

    brand_sel = st.selectbox("Select Brand", df[col_brand].unique())
    dfb = df[df[col_brand] == brand_sel]

    c1, c2 = st.columns(2)

    with c1:
        d = dfb[dfb[col_val_2025] > 0].sort_values(col_val_2025, ascending=False).head(10).reset_index(drop=True)
        d.index = d.index + 1
        st.dataframe(d[[col_code, col_desc, col_val_2025]])

    with c2:
        d = dfb[dfb[col_val_2026] > 0].sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
        d.index = d.index + 1
        st.dataframe(d[[col_code, col_desc, col_val_2026]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY Analysis")

    df_yoy = df.copy()
    df_yoy["YoY Value (%)"] = ((df_yoy[col_val_2026] - df_yoy[col_val_2025]) / df_yoy[col_val_2025]) * 100
    df_yoy["YoY Qty (%)"] = ((df_yoy[col_qty_2026] - df_yoy[col_qty_2025]) / df_yoy[col_qty_2025]) * 100
    df_yoy = df_yoy.replace([float("inf"), -float("inf")], 0)

    tab1, tab2 = st.tabs(["2025 view", "2026 view"])

    with tab1:
        d = df_yoy.sort_values(col_val_2025, ascending=False).head(10).reset_index(drop=True)
        d.index = d.index + 1
        d["YoY Value (%)"] = d["YoY Value (%)"].apply(yoy_format)
        st.dataframe(d[[col_code, col_desc, col_val_2025, "YoY Value (%)"]])

    with tab2:
        d = df_yoy.sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
        d.index = d.index + 1
        d["YoY Value (%)"] = d["YoY Value (%)"].apply(yoy_format)
        st.dataframe(d[[col_code, col_desc, col_val_2026, "YoY Value (%)"]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    tab1, tab2 = st.tabs(["2025", "2026"])

    with tab1:
        p = df.sort_values(col_val_2025, ascending=False).head(10)
        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2025))
        share_2025 = p[col_val_2025].sum() / sales_2025 * 100 if sales_2025 else 0
        st.markdown(f"📊 Top 10 Concentration 2025: **{share_2025:.0f}%**")

    with tab2:
        p = df.sort_values(col_val_2026, ascending=False).head(10)
        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2026))
        share_2026 = p[col_val_2026].sum() / sales_2026 * 100 if sales_2026 else 0
        st.markdown(f"📊 Top 10 Concentration 2026: **{share_2026:.0f}%**")

    st.divider()

    # ================= FINAL CONCENTRATION =================
    st.subheader("📊 Overall Top 10 Concentration")

    top10 = df.sort_values(col_val_2026, ascending=False).head(10)
    share = top10[col_val_2026].sum() / sales_2026 * 100 if sales_2026 else 0

    st.markdown(f"**Top 10 Products Share (2026): {share:.0f}%**")

    if share > 50:
        st.success("High concentration → portfolio driven by key SKUs")
    else:
        st.warning("Low concentration → fragmented portfolio")
