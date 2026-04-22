import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

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

    # ================= CUSTOMER INFO =================
    st.subheader("👤 Customer Information")

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
    c2.write(f"**Country:** {df[col_country].iloc[0]}")
    c3.write(f"**VAT ID:** {df[col_vat].iloc[0]}")

    st.divider()

    # ================= CATEGORY =================
    if col_category in df.columns:
        df["Category Clean"] = df[col_category].astype(str)
    else:
        df["Category Clean"] = df[col_desc].astype(str).str.lower().apply(
            lambda x: "Foil" if "foil" in x else "Other"
        )

    df = df[df["Category Clean"].str.lower() == "foil"]

    # usuń None
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

    # ================= ALERT =================
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
        col_val_2026: "sum",
        col_qty_2025: "sum",
        col_qty_2026: "sum"
    }).reset_index()

    brand["Share 2025 (%)"] = brand[col_val_2025] / brand[col_val_2025].sum() * 100
    brand["Share 2026 (%)"] = brand[col_val_2026] / brand[col_val_2026].sum() * 100

    brand = brand.sort_values(col_val_2026, ascending=False)
    brand.index = range(1, len(brand)+1)

    colA, colB = st.columns(2)

    with colA:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2025,
                              title="Brand Share 2025"))

    with colB:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2026,
                              title="Brand Share 2026"))

    st.dataframe(brand)

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products")

    c1, c2 = st.columns(2)

    with c1:
        d = df.sort_values(col_val_2026, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2026, col_qty_2026]])

    with c2:
        d = df.sort_values(col_val_2025, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2025, col_qty_2025]])

    st.divider()

    # ================= PRODUCTS IN BRAND =================
    st.subheader("📊 Top Products within Brand")

    brand_sel = st.selectbox("Select Brand", df[col_brand].unique())
    dfb = df[df[col_brand] == brand_sel]

    c1, c2 = st.columns(2)

    with c1:
        d = dfb.sort_values(col_val_2026, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2026, col_qty_2026]])

    with c2:
        d = dfb.sort_values(col_val_2025, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2025, col_qty_2025]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY Analysis")

    yoy = df.copy()
    yoy["YoY (%)"] = ((yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]) * 100
    yoy = yoy.replace([float("inf")], 100)

    tab1, tab2 = st.tabs(["2026", "2025"])

    with tab1:
        d = yoy.sort_values(col_val_2026, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2026, "YoY (%)"]])

    with tab2:
        d = yoy.sort_values(col_val_2025, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2025, "YoY (%)"]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    tab1, tab2 = st.tabs(["2026", "2025"])

    with tab1:
        p = df.sort_values(col_val_2026, ascending=False).head(10)
        st.dataframe(p[[col_code, col_desc, col_val_2026]])
        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2026))

    with tab2:
        p = df.sort_values(col_val_2025, ascending=False).head(10)
        st.dataframe(p[[col_code, col_desc, col_val_2025]])
        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2025))
