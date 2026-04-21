import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Dashboard - Company A")

uploaded_file = st.file_uploader("Wgraj plik Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # 🔧 Czyszczenie nazw kolumn
    df.columns = df.columns.str.strip()

    # 🔎 Automatyczne wykrywanie kolumn
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

    # 🎈 FILTR FOIL
    df["Category"] = df[col_desc].astype(str).str.lower().apply(
        lambda x: "Foil" if "foil" in x else "Other"
    )
    df = df[df["Category"] == "Foil"]

    st.success("Pokazuję tylko balony foliowe")

    # 📊 KPI
    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()
    qty_2025 = df[col_qty_2025].sum()
    qty_2026 = df[col_qty_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 if qty_2025 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sprzedaż 2025", f"{sales_2025:,.0f}")
    c2.metric("Sprzedaż 2026", f"{sales_2026:,.0f}", f"{yoy_sales:.1%}")
    c3.metric("Ilość 2025", f"{qty_2025:,.0f}")
    c4.metric("Ilość 2026", f"{qty_2026:,.0f}", f"{yoy_qty:.1%}")

    # 🚨 ALERTY
    st.subheader("🚨 Alerty")
    if yoy_sales < -0.2:
        st.error("Spadek sprzedaży >20%")
    elif yoy_sales > 0.2:
        st.success("Wzrost sprzedaży >20%")

    # 🏷️ BRAND ANALYSIS
    if col_brand:
        st.subheader("🏷️ Sprzedaż wg Brand")

        brand_df = df.groupby(col_brand).agg({
            col_val_2025: "sum",
            col_val_2026: "sum"
        }).reset_index()

        brand_df["Share"] = brand_df[col_val_2026] / brand_df[col_val_2026].sum()

        # wykres słupkowy
        fig = px.bar(
            brand_df,
            x=col_brand,
            y=[col_val_2025, col_val_2026],
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)

        # pie chart udział %
        fig2 = px.pie(
            brand_df,
            names=col_brand,
            values=col_val_2026,
            title="Udział % Brand 2026"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # 🏆 TOP produkty
    st.subheader("🏆 TOP produkty")
    st.dataframe(df.sort_values(col_val_2026, ascending=False)
                 [[col_desc, col_brand, col_val_2026]].head(10))

    # 📉 NAJGORSZE produkty
    st.subheader("📉 Najgorsze produkty")
    st.dataframe(df.sort_values(col_val_2026)
                 [[col_desc, col_brand, col_val_2026]].head(10))

    # 💰 Średnia cena
    st.subheader("💰 Średnia cena")
    df["price_2025"] = df[col_val_2025] / df[col_qty_2025]
    df["price_2026"] = df[col_val_2026] / df[col_qty_2026]

    price_df = pd.DataFrame({
        "Year": ["2025", "2026"],
        "Price": [df["price_2025"].mean(), df["price_2026"].mean()]
    })

    st.plotly_chart(px.bar(price_df, x="Year", y="Price"),
                    use_container_width=True)

    # 📈 YOY PRODUKTY
    st.subheader("📈 Zmiany YoY")
    df["YoY"] = (df[col_val_2026] - df[col_val_2025]) / df[col_val_2025]

    st.write("TOP wzrosty")
    st.dataframe(df.sort_values("YoY", ascending=False)
                 [[col_desc, "YoY"]].head(10))

    st.write("Największe spadki")
    st.dataframe(df.sort_values("YoY")
                 [[col_desc, "YoY"]].head(10))
