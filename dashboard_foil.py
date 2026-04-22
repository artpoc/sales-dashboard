import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Sales Dashboard (Multi Category)")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

# ================= HELPER =================
def yoy_format(v):
    if pd.isna(v):
        return "0%"
    arrow = "🟢 ↑" if v > 0 else "🔴 ↓"
    return f"{v:.0f}% {arrow}"

# NORMALIZACJA KATEGORII
def normalize_category(x):
    x = str(x).lower().strip()

    if "foil" in x:
        return "Foil"
    if "napkin" in x:
        return "Napkins"
    if "plate" in x:
        return "Plates"
    if "cup" in x:
        return "Cups"
    if "tablecover" in x:
        return "Tablecover"
    if "hat" in x:
        return "Hats"
    if "banner" in x:
        return "Banner"
    if "bag" in x:
        return "Bags"
    if "invitation" in x:
        return "Invitations"
    if "latex" in x:
        return "Latex"
    if "straw" in x:
        return "Straws"
    if "reusable" in x:
        return "Reusable"

    return "Other"

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

    # ================= CATEGORY CLEAN =================
    if col_category in df.columns:
        df["Category Clean"] = df[col_category].fillna("").apply(normalize_category)
    else:
        df["Category Clean"] = df[col_desc].fillna("").apply(normalize_category)

    # ================= CATEGORY SELECT =================
    st.subheader("📂 Select Category")

    categories = sorted(df["Category Clean"].dropna().unique())
    selected_category = st.selectbox("Choose category", categories)

    df = df[df["Category Clean"] == selected_category]

    # ================= CUSTOMER =================
    st.subheader("👤 Customer Information")

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
    c2.write(f"**Country:** {df[col_country].iloc[0]}")
    c3.write(f"**VAT ID:** {df[col_vat].iloc[0]}")

    st.success(f"Category: {selected_category}")

    st.divider()

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

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({
        col_val_2025: "sum",
        col_val_2026: "sum"
    }).reset_index()

    col1, col2 = st.columns(2)

    with col1:
        b = brand.sort_values(col_val_2025, ascending=False)
        st.plotly_chart(px.pie(b, names=col_brand, values=col_val_2025))
        st.dataframe(b[[col_brand, col_val_2025]])

    with col2:
        b = brand.sort_values(col_val_2026, ascending=False)
        st.plotly_chart(px.pie(b, names=col_brand, values=col_val_2026))
        st.dataframe(b[[col_brand, col_val_2026]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY Analysis")

    df_yoy = df.copy()

    df_yoy["YoY Value (%)"] = ((df_yoy[col_val_2026] - df_yoy[col_val_2025]) / df_yoy[col_val_2025]) * 100
    df_yoy["YoY Qty (%)"] = ((df_yoy[col_qty_2026] - df_yoy[col_qty_2025]) / df_yoy[col_qty_2025]) * 100

    df_yoy = df_yoy.replace([float("inf"), -float("inf")], 0)
    df_yoy = df_yoy.sort_values(col_val_2026, ascending=False)

    df_yoy["YoY Value (%)"] = df_yoy["YoY Value (%)"].apply(yoy_format)
    df_yoy["YoY Qty (%)"] = df_yoy["YoY Qty (%)"].apply(yoy_format)

    st.dataframe(df_yoy[[
        col_code,
        col_desc,
        col_val_2025,
        col_val_2026,
        col_qty_2025,
        col_qty_2026,
        "YoY Value (%)",
        "YoY Qty (%)"
    ]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    p = df.sort_values(col_val_2026, ascending=False).head(10)
    st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2026))

    share = p[col_val_2026].sum() / sales_2026 * 100 if sales_2026 else 0
    st.markdown(f"📊 Top 10 Concentration: **{share:.0f}%**")
