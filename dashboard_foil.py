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

    # ================= CUSTOMER =================
    st.subheader("👤 Customer Information")

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
    c2.write(f"**Country:** {df[col_country].iloc[0]}")
    c3.write(f"**VAT ID:** {df[col_vat].iloc[0]}")

    st.divider()

    # ================= CATEGORY =================
    if col_category in df.columns:
        df["Category Clean"] = df[col_category]
    else:
        df["Category Clean"] = df[col_desc].astype(str).str.lower().apply(
            lambda x: "Foil" if "foil" in x else "Other"
        )

    df = df[df["Category Clean"].str.lower() == "foil"]
    df = df[df[col_desc].notna()]
    df = df[df[col_desc].astype(str).str.lower() != "none"]

    st.success("Filtered: Foil balloons")

    # ================= KPI =================
    st.markdown("### 💰 EURO (€) | 📦 PCS")

    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()

    k1, k2 = st.columns(2)
    k1.metric("Sales 2025 (€)", f"{sales_2025:,.0f}")
    k2.metric("Sales 2026 (€)", f"{sales_2026:,.0f}")

    st.divider()

    # ================= TOP 10 SHARE =================
    st.subheader("📊 Top 10 Products Share")

    top10 = df.sort_values(col_val_2026, ascending=False).head(10)
    share = top10[col_val_2026].sum() / sales_2026 * 100 if sales_2026 else 0

    st.write(f"Top 10 share in 2026: **{share:.0f}%**")

    if share > 50:
        st.success("Top 10 share >50% → strong portfolio concentration")
    else:
        st.warning("Top 10 share <50% → portfolio fragmented")

    st.plotly_chart(px.pie(top10, names=col_desc, values=col_val_2026))

    st.divider()

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({
        col_val_2025: "sum",
        col_val_2026: "sum"
    }).reset_index()

    colA, colB = st.columns(2)

    with colA:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2025,
                              title="Brand Share 2025"))

    with colB:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2026,
                              title="Brand Share 2026"))

    st.dataframe(brand[[col_brand, col_val_2025, col_val_2026]])

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products")

    c1, c2 = st.columns(2)

    with c1:
        st.write("2025")
        d = df.sort_values(col_val_2025, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2025, col_qty_2025]])

    with c2:
        st.write("2026")
        d = df.sort_values(col_val_2026, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2026, col_qty_2026]])

    st.divider()

    # ================= PRODUCTS IN BRAND =================
    st.subheader("📊 Top Products within Brand")

    brand_sel = st.selectbox("Select Brand", df[col_brand].unique())
    dfb = df[df[col_brand] == brand_sel]

    c1, c2 = st.columns(2)

    with c1:
        st.write("2025")
        d = dfb[dfb[col_val_2025] > 0].sort_values(col_val_2025, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2025]])

    with c2:
        st.write("2026")
        d = dfb[dfb[col_val_2026] > 0].sort_values(col_val_2026, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2026]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY Analysis")

    yoy = df.copy()
    yoy["YoY (%)"] = ((yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]) * 100
    yoy = yoy.replace([float("inf")], 100)

    tab1, tab2 = st.tabs(["2025", "2026"])

    with tab1:
        d = yoy.sort_values(col_val_2025, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2025, "YoY (%)"]])

    with tab2:
        d = yoy.sort_values(col_val_2026, ascending=False).head(10)
        st.dataframe(d[[col_code, col_desc, col_val_2026, "YoY (%)"]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    tab1, tab2 = st.tabs(["2025", "2026"])

    with tab1:
        p = df.sort_values(col_val_2025, ascending=False).head(10)
        st.dataframe(p[[col_code, col_desc, col_val_2025]])
        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2025))

    with tab2:
        p = df.sort_values(col_val_2026, ascending=False).head(10)
        st.dataframe(p[[col_code, col_desc, col_val_2026]])
        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2026))
