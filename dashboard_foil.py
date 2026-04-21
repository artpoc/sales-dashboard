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

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance")

    brand_df = df.groupby(col_brand).agg({
        col_val_2025: "sum",
        col_val_2026: "sum"
    }).reset_index()

    brand_df["Share 2025 (%)"] = brand_df[col_val_2025] / brand_df[col_val_2025].sum()
    brand_df["Share 2026 (%)"] = brand_df[col_val_2026] / brand_df[col_val_2026].sum()
    brand_df["YoY (%)"] = (brand_df[col_val_2026] - brand_df[col_val_2025]) / brand_df[col_val_2025]

    # 🔥 SORT FIX
    brand_df = brand_df.sort_values(col_val_2026, ascending=False)

    st.plotly_chart(
        px.bar(brand_df, x=col_brand,
               y=[col_val_2025, col_val_2026],
               barmode="group",
               title="Sales by Brand (€)"),
        use_container_width=True
    )

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

    # ================= COLOR STYLE =================
    def highlight_yoy(val):
        if val > 0:
            return "background-color: #d4edda"  # green
        elif val < 0:
            return "background-color: #f8d7da"  # red
        return ""

    st.dataframe(brand_df.style.applymap(highlight_yoy, subset=["YoY (%)"]))

    # ================= PRODUCTS IN BRAND =================
    st.subheader("📊 Top Products within Brand (€)")

    selected_brand = st.selectbox("Select Brand", df[col_brand].dropna().unique())

    df_brand = df[df[col_brand] == selected_brand]

    top_products = df_brand.groupby(col_desc)[col_val_2026].sum().reset_index()
    top_products = top_products.sort_values(col_val_2026, ascending=False).head(10)

    st.plotly_chart(
        px.bar(top_products,
               x=col_desc,
               y=col_val_2026,
               title="Top Products by Sales (€) - 2026"),
        use_container_width=True
    )

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products 2026 (€)")
    st.dataframe(df.sort_values(col_val_2026, ascending=False)
                 [[col_desc, col_brand, col_val_2026]].head(10))

    # ================= YOY =================
    st.subheader("📈 YoY Change (%)")

    yoy = df[[col_desc, col_brand, col_val_2025, col_val_2026]].copy()
    yoy["YoY (%)"] = (yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]

    yoy = yoy.rename(columns={
        col_desc: "Product",
        col_brand: "Brand",
        col_val_2025: "Sales 2025 (€)",
        col_val_2026: "Sales 2026 (€)"
    })

    st.write("🔼 Top Growth")
    st.dataframe(yoy.sort_values("YoY (%)", ascending=False)
                 .head(10)
                 .style.applymap(highlight_yoy, subset=["YoY (%)"]))

    st.write("🔽 Biggest Decline")
    st.dataframe(yoy.sort_values("YoY (%)")
                 .head(10)
                 .style.applymap(highlight_yoy, subset=["YoY (%)"]))
