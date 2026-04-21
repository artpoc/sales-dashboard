import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard - Company A")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

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

    # FILTER
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
    c1.metric("Sales 2025 (€)", f"{sales_2025:,.0f}")
    c2.metric("Sales 2026 (€)", f"{sales_2026:,.0f}", f"{yoy_sales:.0%}")
    c3.metric("Quantity 2025 (units)", f"{qty_2025:,.0f}")
    c4.metric("Quantity 2026 (units)", f"{qty_2026:,.0f}", f"{yoy_qty:.0%}")

    st.divider()

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance (€ + Units)")

    brand = df.groupby(col_brand).agg({
        col_val_2025: "sum",
        col_val_2026: "sum",
        col_qty_2025: "sum",
        col_qty_2026: "sum"
    }).reset_index()

    brand["YoY Value (%)"] = ((brand[col_val_2026] - brand[col_val_2025]) / brand[col_val_2025]) * 100
    brand["YoY Qty (%)"] = ((brand[col_qty_2026] - brand[col_qty_2025]) / brand[col_qty_2025]) * 100

    brand = brand.sort_values(col_val_2026, ascending=False).reset_index(drop=True)
    brand.index = brand.index + 1

    st.dataframe(brand)

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products (Value € & Units)")

    top = df.sort_values(col_val_2026, ascending=False).head(10).reset_index(drop=True)
    top.index = top.index + 1

    st.dataframe(top[[col_desc, col_brand, col_val_2026, col_qty_2026]])

    st.divider()

    # ================= TOP VOLUME =================
    st.subheader("📦 Top Volume Products (Units 2026)")

    volume = df.sort_values(col_qty_2026, ascending=False).head(10).reset_index(drop=True)
    volume.index = volume.index + 1

    st.dataframe(volume[[col_desc, col_brand, col_qty_2026]])

    st.divider()

    # ================= PRICE ANALYSIS =================
    st.subheader("💰 Price / Mix Analysis (€ per unit)")

    df["Price 2025"] = df[col_val_2025] / df[col_qty_2025]
    df["Price 2026"] = df[col_val_2026] / df[col_qty_2026]

    price = df[[col_desc, col_brand, "Price 2025", "Price 2026"]].copy()
    price = price.sort_values("Price 2026", ascending=False).head(10)
    price.index = range(1, len(price) + 1)

    st.dataframe(price)

    st.divider()

    # ================= YOY =================
    st.subheader("📈 YoY (Value € vs Quantity Units)")

    yoy = df[[col_desc, col_brand, col_val_2025, col_val_2026, col_qty_2025, col_qty_2026]].copy()

    yoy["YoY Value (%)"] = ((yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]) * 100
    yoy["YoY Qty (%)"] = ((yoy[col_qty_2026] - yoy[col_qty_2025]) / yoy[col_qty_2025]) * 100

    yoy = yoy.sort_values(col_val_2026, ascending=False).reset_index(drop=True)
    yoy.index = yoy.index + 1

    st.dataframe(yoy.head(15))
