import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# PDF (bez reportlab — prostsze i stabilne)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")
st.title("🎈 Foil Balloons Sales Dashboard - Company A")

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

    # ---------- COLUMN DETECTION ----------
    col_brand = find_column("brand")
    col_desc = find_column("article")

    col_val_2025 = [c for c in df.columns if "2025" in c and "value" in c.lower()][0]
    col_val_2026 = [c for c in df.columns if "2026" in c and "value" in c.lower()][0]
    col_qty_2025 = [c for c in df.columns if "2025" in c and "quantity" in c.lower()][0]
    col_qty_2026 = [c for c in df.columns if "2026" in c and "quantity" in c.lower()][0]

    # ---------- FILTER ----------
    df["Category"] = df[col_desc].astype(str).str.lower().apply(
        lambda x: "Foil" if "foil" in x else "Other"
    )
    df = df[df["Category"] == "Foil"]

    st.success("Dataset filtered: Foil balloons only")

    # ================= KPI =================
    st.markdown("### 💰 All values are in EURO (€) | 📦 Quantities in PCS")

    sales_2025 = df[col_val_2025].sum()
    sales_2026 = df[col_val_2026].sum()
    qty_2025 = df[col_qty_2025].sum()
    qty_2026 = df[col_qty_2026].sum()

    yoy_sales = (sales_2026 - sales_2025) / sales_2025 * 100 if sales_2025 else 0
    yoy_qty = (qty_2026 - qty_2025) / qty_2025 * 100 if qty_2025 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales 2025 (€)", f"{sales_2025:,.0f}")
    c2.metric("Sales 2026 (€)", f"{sales_2026:,.0f}", f"{yoy_sales:.0f}%")
    c3.metric("Quantity 2025 (PCS)", f"{qty_2025:,.0f}")
    c4.metric("Quantity 2026 (PCS)", f"{qty_2026:,.0f}", f"{yoy_qty:.0f}%")

    st.divider()

    # ================= ALERT =================
    st.subheader("🚨 Sales Alerts")

    if yoy_sales < -20:
        alert_text = f"Sales decline >20% (Actual: {yoy_sales:.0f}%)"
        st.error(alert_text)
    elif yoy_sales > 20:
        alert_text = f"Sales growth >20% (Actual: {yoy_sales:.0f}%)"
        st.success(alert_text)
    else:
        alert_text = f"Stable performance (Actual: {yoy_sales:.0f}%)"
        st.info(alert_text)

    st.divider()

    # ================= BRAND =================
    st.subheader("🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({
        col_val_2026: "sum"
    }).reset_index()

    st.plotly_chart(px.pie(brand, names=col_brand, values=col_val_2026,
                           title="Brand Share 2026 (%)"))

    st.divider()

    # ================= TOP PRODUCTS =================
    st.subheader("🏆 Top Products 2026")

    top_2026 = df.sort_values(col_val_2026, ascending=False).head(10)
    st.dataframe(top_2026[[col_desc, col_val_2026, col_qty_2026]])

    st.divider()

    # ================= PORTFOLIO =================
    st.subheader("🎯 Portfolio Optimization")

    portfolio = df.sort_values(col_val_2026, ascending=False)
    top10 = portfolio.head(10)

    st.dataframe(top10[[col_desc, col_val_2026]])

    st.plotly_chart(px.pie(top10, names=col_desc, values=col_val_2026,
                           title="Top 10 Products Share"))

    st.divider()

    # ================= RECOMMENDATIONS =================
    st.subheader("💡 AI Sales Recommendations")

    recommendations = []

    if yoy_sales > 10 and yoy_qty < 0:
        recommendations.append("📈 Sales driven by price increase – monitor demand elasticity")

    if yoy_qty > 10:
        recommendations.append("📦 Strong volume growth – consider scaling distribution")

    if yoy_sales < 0:
        recommendations.append("⚠️ Declining sales – review portfolio and promotions")

    top_share = top10[col_val_2026].sum() / df[col_val_2026].sum() * 100

    if top_share > 70:
        recommendations.append("⚠️ High dependency on few products – diversify portfolio")

    if not recommendations:
        recommendations.append("✅ Portfolio performing well – no immediate risks detected")

    for rec in recommendations:
        st.write(rec)

    st.divider()

    # ================= PDF EXPORT =================
    st.subheader("📄 Export Report to PDF")

    def generate_pdf():
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        content = []

        content.append(Paragraph("Foil Balloons Sales Report", styles["Title"]))
        content.append(Spacer(1, 12))

        content.append(Paragraph(f"Sales 2026: {sales_2026:,.0f} €", styles["Normal"]))
        content.append(Paragraph(f"YoY Sales: {yoy_sales:.0f}%", styles["Normal"]))
        content.append(Spacer(1, 12))

        content.append(Paragraph("Recommendations:", styles["Heading2"]))

        for rec in recommendations:
            content.append(Paragraph(rec, styles["Normal"]))

        doc.build(content)
        buffer.seek(0)
        return buffer

    pdf_file = generate_pdf()

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_file,
        file_name="sales_report.pdf",
        mime="application/pdf"
    )
