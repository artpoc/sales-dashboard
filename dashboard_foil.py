import streamlit as st
import pandas as pd
import plotly.express as px

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
    qty_2025 = df[col_qty_2025].sum()
    qty_2026 = df[col_qty_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 if qty_2025 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales 2025 (€)", f"{sales_2025:,.0f} €")
    c2.metric("Sales 2026 (€)", f"{sales_2026:,.0f} €", f"{yoy_sales:.1%} YoY (%)")
    c3.metric("Quantity 2025 (units)", f"{qty_2025:,.0f}")
    c4.metric("Quantity 2026 (units)", f"{qty_2026:,.0f}", f"{yoy_qty:.1%} YoY (%)")

    # ================= ALERTS =================
    st.subheader("🚨 Sales Alerts")
    if yoy_sales < -0.2:
        st.error("Sales decline > 20% YoY (%)")
    elif yoy_sales > 0.2:
        st.success("Sales growth > 20% YoY (%)")
    else:
        st.info("Stable sales YoY (%)")

    # ================= BRAND ANALYSIS =================
    if col_brand:
        st.subheader("🏷️ Brand Performance Analysis")

        brand_df = df.groupby(col_brand).agg({
            col_val_2025: "sum",
            col_val_2026: "sum"
        }).reset_index()

        brand_df["Share 2025 (%)"] = brand_df[col_val_2025] / brand_df[col_val_2025].sum()
        brand_df["Share 2026 (%)"] = brand_df[col_val_2026] / brand_df[col_val_2026].sum()
        brand_df["YoY (%)"] = (brand_df[col_val_2026] - brand_df[col_val_2025]) / brand_df[col_val_2025]

        # Bar chart
        st.plotly_chart(
            px.bar(brand_df,
                   x=col_brand,
                   y=[col_val_2025, col_val_2026],
                   barmode="group",
                   title="Sales by Brand (€)"),
            use_container_width=True
        )

        # Pie charts
        colA, colB = st.columns(2)

        with colA:
            st.plotly_chart(
                px.pie(brand_df, names=col_brand,
                       values=col_val_2025,
                       title="Brand Share 2025 (%)"),
                use_container_width=True
            )

        with colB:
            st.plotly_chart(
                px.pie(brand_df, names=col_brand,
                       values=col_val_2026,
                       title="Brand Share 2026 (%)"),
                use_container_width=True
            )

        st.dataframe(brand_df)

    # ================= PRODUCT SHARE =================
    st.subheader("📊 Product Share within Brand (%)")

    if col_brand:
        selected_brand = st.selectbox("Select Brand", df[col_brand].dropna().unique())

        df_brand = df[df[col_brand] == selected_brand]

        prod_share = df_brand.groupby(col_desc)[col_val_2026].sum().reset_index()
        prod_share["Share (%)"] = prod_share[col_val_2026] / prod_share[col_val_2026].sum()

        st.plotly_chart(
            px.bar(prod_share.sort_values("Share (%)", ascending=False).head(10),
                   x=col_desc, y="Share (%)",
                   title="Top Products Share (%) - 2026"),
            use_container_width=True
        )

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products 2026 (€)")

    top_df = df.sort_values(col_val_2026, ascending=False).head(10)
    st.dataframe(top_df[[col_desc, col_brand, col_val_2026]])

    # ================= YOY DETAILS =================
    st.subheader("📈 Year-over-Year Change (YoY %)")

    yoy = df[[col_desc, col_brand, col_val_2025, col_val_2026]].copy()
    yoy["YoY (%)"] = (yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]

    yoy = yoy.rename(columns={
        col_desc: "Product",
        col_brand: "Brand",
        col_val_2025: "Sales 2025 (€)",
        col_val_2026: "Sales 2026 (€)"
    })

    st.write("🔼 Top Growth Products")
    st.dataframe(yoy.sort_values("YoY (%)", ascending=False).head(10))

    st.write("🔽 Biggest Declines")
    st.dataframe(yoy.sort_values("YoY (%)").head(10))
