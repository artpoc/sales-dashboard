import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("📊 Sales Dashboard")

# Upload file
uploaded_file = st.file_uploader("Wgraj plik Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # --- CATEGORY MAPPING ---
    def map_category(name):
        name = str(name).lower()
        if "plate" in name:
            return "plates"
        elif "cup" in name:
            return "cups"
        elif "napkin" in name:
            return "napkins"
        elif "balloon" in name or "foil" in name:
            return "foil balloons"
        else:
            return "other"

    df["Category"] = df["Article description"].apply(map_category)

    # --- CUSTOMER SELECTION ---
    customers = df["Customer Name"].unique()
    selected_customer = st.selectbox("Wybierz klienta", customers)

    df_cust = df[df["Customer Name"] == selected_customer]

    # --- KPI ---
    sales_2025 = df_cust["Net Value 2025"].sum()
    sales_2026 = df_cust["Net Value 2026"].sum()

    qty_2025 = df_cust["Quantity 2025"].sum()
    qty_2026 = df_cust["Quantity 2026"].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 if sales_2025 != 0 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 if qty_2025 != 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Sprzedaż 2025", f"{sales_2025:,.0f}")
    col2.metric("Sprzedaż 2026", f"{sales_2026:,.0f}", f"{yoy_sales:.1%}")
    col3.metric("Ilość 2025", f"{qty_2025:,.0f}")
    col4.metric("Ilość 2026", f"{qty_2026:,.0f}", f"{yoy_qty:.1%}")

    # --- CATEGORIES ---
    st.subheader("📦 Kategorie produktów")

    cat_group = df_cust.groupby("Category").agg({
        "Net Value 2025": "sum",
        "Net Value 2026": "sum"
    }).reset_index()

    cat_group["Share 2026"] = cat_group["Net Value 2026"] / cat_group["Net Value 2026"].sum()

    fig = px.bar(cat_group, x="Category",
                 y=["Net Value 2025", "Net Value 2026"],
                 barmode="group",
                 title="Sprzedaż wg kategorii")

    st.plotly_chart(fig, use_container_width=True)

    # --- SHARE ---
    fig2 = px.pie(cat_group, names="Category", values="Net Value 2026",
                  title="Udział kategorii 2026")

    st.plotly_chart(fig2, use_container_width=True)

    # --- TOP PRODUCTS ---
    st.subheader("🏆 TOP produkty")

    df_cust["Total 2026"] = df_cust["Net Value 2026"]

    top_products = df_cust.sort_values(by="Total 2026", ascending=False).head(10)

    st.dataframe(top_products[[
        "Article description",
        "Net Value 2025",
        "Net Value 2026",
        "Quantity 2025",
        "Quantity 2026"
    ]])

    # --- CUSTOMER TABLE ---
    st.subheader("📋 Porównanie klientów")

    df_group = df.groupby("Customer Name").agg({
        "Net Value 2025": "sum",
        "Net Value 2026": "sum",
        "Quantity 2025": "sum",
        "Quantity 2026": "sum"
    }).reset_index()

    df_group["YoY Sales"] = (df_group["Net Value 2026"] - df_group["Net Value 2025"]) / df_group["Net Value 2025"]
    df_group["YoY Qty"] = (df_group["Quantity 2026"] - df_group["Quantity 2025"]) / df_group["Quantity 2025"]

    st.dataframe(df_group)
