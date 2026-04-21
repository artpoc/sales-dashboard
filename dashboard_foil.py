import streamlit as st
import pandas as pd
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Dashboard - Company A")

uploaded_file = st.file_uploader("Wgraj plik Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # 🔎 wykrywanie kolumn
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

    # 🎈 filtr foil
    df["Category"] = df[col_desc].astype(str).str.lower().apply(
        lambda x: "Foil" if "foil" in x else "Other"
    )
    df = df[df["Category"] == "Foil"]

    st.success("Dane: tylko balony foliowe (Foil)")

    # ================= KPI =================
    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()
    qty_2025 = df[col_qty_2025].sum()
    qty_2026 = df[col_qty_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 if qty_2025 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sprzedaż 2025 (€)", f"{sales_2025:,.0f} €")
    c2.metric("Sprzedaż 2026 (€)", f"{sales_2026:,.0f} €", f"{yoy_sales:.1%} YoY")
    c3.metric("Ilość 2025 (szt.)", f"{qty_2025:,.0f}")
    c4.metric("Ilość 2026 (szt.)", f"{qty_2026:,.0f}", f"{yoy_qty:.1%} YoY")

    # ================= 🚨 ALERTY =================
    st.subheader("🚨 Alerty sprzedażowe")
    if yoy_sales < -0.2:
        st.error("Spadek sprzedaży > 20% (YoY)")
    elif yoy_sales > 0.2:
        st.success("Wzrost sprzedaży > 20% (YoY)")
    else:
        st.info("Stabilna sprzedaż (YoY)")

    # ================= 🏷️ BRAND =================
    if col_brand:
        st.subheader("🏷️ Analiza Brand (licencji)")

        brand_df = df.groupby(col_brand).agg({
            col_val_2025: "sum",
            col_val_2026: "sum"
        }).reset_index()

        brand_df["Udział % 2026"] = brand_df[col_val_2026] / brand_df[col_val_2026].sum()
        brand_df["YoY %"] = (brand_df[col_val_2026] - brand_df[col_val_2025]) / brand_df[col_val_2025]

        # wykres słupkowy
        st.plotly_chart(
            px.bar(brand_df, x=col_brand,
                   y=[col_val_2025, col_val_2026],
                   barmode="group",
                   title="Sprzedaż (€) wg Brand"),
            use_container_width=True
        )

        # pie chart
        st.plotly_chart(
            px.pie(brand_df, names=col_brand,
                   values=col_val_2026,
                   title="Udział % Brand 2026"),
            use_container_width=True
        )

        st.dataframe(brand_df)

    # ================= 📊 PRODUKTY W BRAND =================
    st.subheader("📊 Udział produktów w ramach Brand")

    if col_brand:
        selected_brand = st.selectbox("Wybierz Brand", df[col_brand].dropna().unique())

        df_brand = df[df[col_brand] == selected_brand]

        prod_share = df_brand.groupby(col_desc)[col_val_2026].sum().reset_index()
        prod_share["Udział %"] = prod_share[col_val_2026] / prod_share[col_val_2026].sum()

        st.plotly_chart(
            px.bar(prod_share.sort_values("Udział %", ascending=False).head(10),
                   x=col_desc, y="Udział %",
                   title="Top produkty w Brand (%)"),
            use_container_width=True
        )

    # ================= 🎯 BEST vs DEAD =================
    st.subheader("🎯 Best Seller vs Dead Stock")

    best = df.sort_values(col_val_2026, ascending=False).head(10)
    dead = df[df[col_val_2026] == 0]

    st.write("🏆 Best Sellers")
    st.dataframe(best[[col_desc, col_brand, col_val_2026]])

    st.write("💀 Dead Stock (brak sprzedaży 2026)")
    st.dataframe(dead[[col_desc, col_brand, col_val_2025]])

    # ================= 📈 YOY =================
    st.subheader("📈 Zmiana YoY – szczegóły")

    yoy = df[[col_desc, col_brand, col_val_2025, col_val_2026]].copy()
    yoy["YoY %"] = (yoy[col_val_2026] - yoy[col_val_2025]) / yoy[col_val_2025]

    yoy = yoy.rename(columns={
        col_desc: "Produkt",
        col_brand: "Brand",
        col_val_2025: "Sprzedaż 2025 (€)",
        col_val_2026: "Sprzedaż 2026 (€)"
    })

    st.write("🔼 Największe wzrosty")
    st.dataframe(yoy.sort_values("YoY %", ascending=False).head(10))

    st.write("🔽 Największe spadki")
    st.dataframe(yoy.sort_values("YoY %").head(10))

    # ================= 📤 PDF =================
    st.subheader("📤 Eksport raportu PDF")

    if st.button("Generuj PDF"):

        doc = SimpleDocTemplate("raport.pdf")
        styles = getSampleStyleSheet()

        elements = []
        elements.append(Paragraph("Raport sprzedaży - Foil Balloons", styles["Title"]))
        elements.append(Paragraph(f"Sprzedaż 2025: {sales_2025:,.0f} €", styles["Normal"]))
        elements.append(Paragraph(f"Sprzedaż 2026: {sales_2026:,.0f} €", styles["Normal"]))

        doc.build(elements)

        st.success("PDF wygenerowany jako raport.pdf")
