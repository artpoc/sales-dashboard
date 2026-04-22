import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard")

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

    # ---------- COLUMNS ----------
    col_brand = find_column("brand")
    col_desc = find_column("article")
    col_code = find_column("code")

    col_val_2025 = [c for c in df.columns if "2025" in c and "value" in c.lower()][0]
    col_val_2026 = [c for c in df.columns if "2026" in c and "value" in c.lower()][0]
    col_qty_2025 = [c for c in df.columns if "2025" in c and "quantity" in c.lower()][0]
    col_qty_2026 = [c for c in df.columns if "2026" in c and "quantity" in c.lower()][0]

    # ---------- CUSTOMER ----------
    st.subheader("👤 Customer Information")

    col_customer = find_column("customer")
    col_country = find_column("country")
    col_vat = find_column("vat")

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Customer:** {df[col_customer].iloc[0] if col_customer else '-'}")
    c2.write(f"**Country:** {df[col_country].iloc[0] if col_country else '-'}")
    c3.write(f"**VAT ID:** {df[col_vat].iloc[0] if col_vat else '-'}")

    st.divider()

    # ---------- FILTER ----------
    df = df[df[col_desc].notna()]
    df = df[df[col_desc].astype(str).str.lower() != "none"]

    df["Category"] = df[col_desc].astype(str).str.lower().apply(
        lambda x: "Foil" if "foil" in x else "Other"
    )
    df = df[df["Category"] == "Foil"]

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
    k3.metric("Quantity 2025", f"{qty_2025:,.0f}")
    k4.metric("Quantity 2026", f"{qty_2026:,.0f}", f"{yoy_qty:.0f}%")

    st.divider()

    # ================= ALERT =================
    st.subheader("🚨 Sales Alerts")

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

    st.plotly_chart(px.bar(brand, x=col_brand,
                           y=[col_val_2025, col_val_2026],
                           barmode="group",
                           title="Sales by Brand (€)"),
                    use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2025,
                              title="Brand Share 2025"))
    with colB:
        st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2026,
                              title="Brand Share 2026"))

    brand_display = brand.copy()
    for col in ["Share 2025 (%)", "Share 2026 (%)", "YoY Value (%)", "YoY Qty (%)"]:
        brand_display[col] = brand_display[col].apply(format_percent)

    st.dataframe(brand_display)

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products")

    t1, t2 = st.columns(2)

    with t1:
        st.write("2026")
        d = df.sort_values(col_val_2026, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2026, col_qty_2026]])

    with t2:
        st.write("2025")
        d = df.sort_values(col_val_2025, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2025, col_qty_2025]])

    st.divider()

    # ================= PRODUCTS IN BRAND =================
    st.subheader("📊 Top Products within Brand")

    brand_sel = st.selectbox("Select Brand", df[col_brand].dropna().unique())
    dfb = df[df[col_brand] == brand_sel]

    b1, b2 = st.columns(2)

    with b1:
        st.write("2026")
        d = dfb.sort_values(col_val_2026, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2026, col_qty_2026]])

    with b2:
        st.write("2025")
        d = dfb.sort_values(col_val_2025, ascending=False).head(10)
        d.index = range(1, len(d)+1)
        st.dataframe(d[[col_code, col_desc, col_val_2025, col_qty_2025]])

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY Analysis")

    yoy = df.copy()
    yoy["YoY Value (%)"] = ((yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]) * 100
    yoy["YoY Qty (%)"] = ((yoy[col_qty_2026] - yoy[col_qty_2025]) / yoy[col_qty_2025]) * 100
    yoy = yoy.replace([float("inf")], 100)

    tab1, tab2 = st.tabs(["2026", "2025"])

    with tab1:
        d = yoy.sort_values(col_val_2026, ascending=False).head(10)
        d["YoY Value (%)"] = d["YoY Value (%)"].apply(format_percent)
        d["YoY Qty (%)"] = d["YoY Qty (%)"].apply(format_percent)
        st.dataframe(d[[col_code, col_desc, col_val_2026, "YoY Value (%)", "YoY Qty (%)"]])

    with tab2:
        d = yoy.sort_values(col_val_2025, ascending=False).head(10)
        d["YoY Value (%)"] = d["YoY Value (%)"].apply(format_percent)
        d["YoY Qty (%)"] = d["YoY Qty (%)"].apply(format_percent)
        st.dataframe(d[[col_code, col_desc, col_val_2025, "YoY Value (%)", "YoY Qty (%)"]])

    st.divider()

    # ================= RISK =================
    st.subheader("📉 Risk Detection")

    risk = df.sort_values(col_val_2025, ascending=False).head(20)
    risk = risk[risk[col_val_2026] < risk[col_val_2025]]

    risk["YoY (%)"] = ((risk[col_val_2026] - risk[col_val_2025]) / risk[col_val_2025]) * 100
    risk = risk.replace([float("inf")], 100)
    risk = risk.sort_values("YoY (%)")
    risk.index = range(1, len(risk)+1)

    risk["YoY (%)"] = risk["YoY (%)"].apply(format_percent)

    st.dataframe(risk[[col_code, col_desc, col_val_2025, col_val_2026, "YoY (%)"]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    tab1, tab2 = st.tabs(["2026", "2025"])

    with tab1:
        p = df.sort_values(col_val_2026, ascending=False).head(10)
        p.index = range(1, len(p)+1)
        st.dataframe(p[[col_code, col_desc, col_val_2026]])

        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2026,
                              title="Top 10 Share 2026"))

    with tab2:
        p = df.sort_values(col_val_2025, ascending=False).head(10)
        p.index = range(1, len(p)+1)
        st.dataframe(p[[col_code, col_desc, col_val_2025]])

        st.plotly_chart(px.pie(p, names=col_desc, values=col_val_2025,
                              title="Top 10 Share 2025"))
