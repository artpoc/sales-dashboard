import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard - Company A")

uploaded_file = st.file_uploader("Wgraj plik Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # FILTER ONLY FOIL BALLOONS
    df["Category"] = df["Article description"].str.lower().apply(lambda x: "Foil" if "foil" in str(x) else "Other")
    df = df[df["Category"] == "Foil"]

    st.success("Dane przefiltrowane: tylko balony foliowe")

    # KPI
    sales_2025 = df["Net Value 2025"].sum()
    sales_2026 = df["Net Value 2026"].sum()

    qty_2025 = df["Quantity 2025"].sum()
    qty_2026 = df["Quantity 2026"].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 if qty_2025 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sprzedaż 2025", f"{sales_2025:,.0f}")
    col2.metric("Sprzedaż 2026", f"{sales_2026:,.0f}", f"{yoy_sales:.1%}")
    col3.metric("Ilość 2025", f"{qty_2025:,.0f}")
    col4.metric("Ilość 2026", f"{qty_2026:,.0f}", f"{yoy_qty:.1%}")

    # SALES COMPARISON
    st.subheader("📊 Sprzedaż rok do roku")
    sales_df = pd.DataFrame({
        "Year": ["2025", "2026"],
        "Sales": [sales_2025, sales_2026]
    })
    fig = px.bar(sales_df, x="Year", y="Sales", title="Sprzedaż Foil YoY")
    st.plotly_chart(fig, use_container_width=True)

    # BRAND ANALYSIS
    st.subheader("🏷️ Sprzedaż wg Brand (licencji)")
    brand_group = df.groupby("Brand Name").agg({
        "Net Value 2025": "sum",
        "Net Value 2026": "sum"
    }).reset_index()

    fig2 = px.bar(brand_group, x="Brand Name",
                  y=["Net Value 2025", "Net Value 2026"],
                  barmode="group",
                  title="Sprzedaż wg Brand")
    st.plotly_chart(fig2, use_container_width=True)

    # TOP PRODUCTS
    st.subheader("🏆 Najlepsze produkty 2026")
    top_products = df.sort_values(by="Net Value 2026", ascending=False).head(10)
    st.dataframe(top_products[["Article description", "Brand Name", "Net Value 2026"]])

    # WORST PRODUCTS
    st.subheader("📉 Najgorsze produkty 2026")
    worst_products = df.sort_values(by="Net Value 2026", ascending=True).head(10)
    st.dataframe(worst_products[["Article description", "Brand Name", "Net Value 2026"]])

    # QUANTITY ANALYSIS
    st.subheader("📦 Ilość sprzedanych produktów")
    qty_df = pd.DataFrame({
        "Year": ["2025", "2026"],
        "Quantity": [qty_2025, qty_2026]
    })
    fig3 = px.bar(qty_df, x="Year", y="Quantity", title="Ilość YoY")
    st.plotly_chart(fig3, use_container_width=True)

    # PRICE ANALYSIS
    st.subheader("💰 Średnia cena")
    df["Price 2025"] = df["Net Value 2025"] / df["Quantity 2025"]
    df["Price 2026"] = df["Net Value 2026"] / df["Quantity 2026"]

    avg_price_2025 = df["Price 2025"].mean()
    avg_price_2026 = df["Price 2026"].mean()

    price_df = pd.DataFrame({
        "Year": ["2025", "2026"],
        "Price": [avg_price_2025, avg_price_2026]
    })

    fig4 = px.bar(price_df, x="Year", y="Price", title="Średnia cena")
    st.plotly_chart(fig4, use_container_width=True)

    # YOY BY PRODUCT
    st.subheader("📈 Zmiana YoY per produkt")
    df["YoY"] = (df["Net Value 2026"] - df["Net Value 2025"]) / df["Net Value 2025"]
    st.dataframe(df[["Article description", "YoY"]].sort_values(by="YoY", ascending=False).head(10))
