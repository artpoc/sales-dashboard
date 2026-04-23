import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

# ================= HELPERS =================
def calc_yoy(new, old):
    if old == 0 and new > 0:
        return 100
    elif old > 0 and new == 0:
        return -100
    elif old == 0 and new == 0:
        return 0
    else:
        return (new - old) / old * 100

def yoy_format(v):
    if v > 0:
        return f"+{v:.0f}% 🟢 ↑"
    elif v < 0:
        return f"{v:.0f}% 🔴 ↓"
    else:
        return "0%"

def normalize_category(x):
    x = str(x).lower()
    if "foil" in x: return "Foil"
    if "napkin" in x: return "Napkins"
    if "plate" in x: return "Plates"
    if "cup" in x: return "Cups"
    if "tablecover" in x: return "Tablecover"
    if "hat" in x: return "Hats"
    if "banner" in x: return "Banner"
    if "bag" in x: return "Bags"
    if "invitation" in x: return "Invitations"
    if "latex" in x: return "Latex"
    if "straw" in x: return "Straws"
    if "reusable" in x: return "Reusable"
    return "Other"

def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # ================= COLUMNS =================
    col_customer = "Customer Name"
    col_country = "Country"
    col_vat = "Vat ID Nr."
    col_code = "Art. Nr."
    col_desc = "Article description"
    col_brand = "Brand Name"
    col_cat = "Category"

    val25 = "Net Value 2025"
    val26 = "Net Value 2026"
    qty25 = "Quantity 2025"
    qty26 = "Quantity 2026"

    # ================= CUSTOMER =================
    st.subheader("👤 Customer Information")

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
    c2.write(f"**Country:** {df[col_country].iloc[0]}")
    c3.write(f"**VAT:** {df[col_vat].iloc[0]}")

    # ================= CATEGORY =================
    df["Category Clean"] = df[col_cat].fillna("").apply(normalize_category)

    categories = ["All Categories"] + sorted(df["Category Clean"].unique())
    selected = st.selectbox("📂 Select Category", categories)

    if selected != "All Categories":
        df = df[df["Category Clean"] == selected]

    df = df[df[col_desc].notna()]
    df = df[df[col_desc].str.lower() != "none"]

    st.divider()

    # ================= KPI =================
    st.markdown("## 💰 KPI (EUR / PCS)")

    s25, s26 = df[val25].sum(), df[val26].sum()
    q25, q26 = df[qty25].sum(), df[qty26].sum()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Sales 2025 (€)", f"{s25:,.0f}")
    k2.metric("Sales 2026 (€)", f"{s26:,.0f}", f"{calc_yoy(s26,s25):+.0f}%")
    k3.metric("Qty 2025", f"{q25:,.0f}")
    k4.metric("Qty 2026", f"{q26:,.0f}", f"{calc_yoy(q26,q25):+.0f}%")

    st.divider()

    # ================= YOY =================
    st.markdown("## 📈 YoY Analysis (2026 vs 2025)")

    df_yoy = df.copy()
    df_yoy["YoY %"] = df_yoy.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
    df_yoy["YoY %"] = df_yoy["YoY %"].apply(yoy_format)

    df_yoy = add_index(df_yoy.sort_values(val26, ascending=False))

    st.dataframe(df_yoy[[col_code,col_desc,val25,val26,qty25,qty26,"YoY %"]])

    st.divider()

    # ================= AUTO INSIGHTS =================
    st.markdown("## 🧠 Auto Insights")

    cat = df.groupby("Category Clean").agg({
        val25:"sum", val26:"sum",
        qty25:"sum", qty26:"sum"
    }).reset_index()

    tab1, tab2 = st.tabs(["2025","2026"])

    with tab1:
        top = cat.sort_values(val25, ascending=False).iloc[0]
        st.success(f"Top 2025: {top['Category Clean']} | €{top[val25]:,.0f} | {top[qty25]:,.0f} pcs")

    with tab2:
        top = cat.sort_values(val26, ascending=False).iloc[0]
        st.success(f"Top 2026: {top['Category Clean']} | €{top[val26]:,.0f} | {top[qty26]:,.0f} pcs")

    cat["YoY"] = cat.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

    growth = cat.sort_values("YoY", ascending=False).iloc[0]
    risk = cat.sort_values("YoY").iloc[0]

    st.info(f"Growth: {growth['Category Clean']} | {growth['YoY']:.0f}% | €{growth[val26]:,.0f}")
    st.warning(f"Risk: {risk['Category Clean']} | {risk['YoY']:.0f}% | €{risk[val26]:,.0f}")

    st.divider()

    # ================= BRAND INSIGHTS =================
    st.markdown("## 🏷️ Brand Insights")

    brand = df.groupby(col_brand).agg({
        val25:"sum", val26:"sum",
        qty25:"sum", qty26:"sum"
    }).reset_index()

    tab1, tab2 = st.tabs(["2025","2026"])

    with tab1:
        top = brand.sort_values(val25, ascending=False).iloc[0]
        st.success(f"Top 2025: {top[col_brand]} | €{top[val25]:,.0f}")

    with tab2:
        top = brand.sort_values(val26, ascending=False).iloc[0]
        st.success(f"Top 2026: {top[col_brand]} | €{top[val26]:,.0f}")

    brand["YoY"] = brand.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

    growth = brand.sort_values("YoY", ascending=False).iloc[0]
    risk = brand.sort_values("YoY").iloc[0]

    st.info(f"Growth Brand: {growth[col_brand]} | {growth['YoY']:.0f}%")
    st.warning(f"Risk Brand: {risk[col_brand]} | {risk['YoY']:.0f}%")

    st.divider()

    # ================= SKU INSIGHTS =================
    st.markdown("## 📦 SKU Insights")

    df["YoY raw"] = df.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

    tab1, tab2 = st.tabs(["2025","2026"])

    with tab1:
        top = df.sort_values(val25, ascending=False).iloc[0]
        st.success(f"Top 2025: {top[col_desc]} | €{top[val25]:,.0f}")

    with tab2:
        top = df.sort_values(val26, ascending=False).iloc[0]
        st.success(f"Top 2026: {top[col_desc]} | €{top[val26]:,.0f}")

    growth = df.sort_values("YoY raw", ascending=False).iloc[0]
    risk = df.sort_values("YoY raw").iloc[0]

    st.info(f"Growth SKU: {growth[col_desc]} | {growth['YoY raw']:.0f}%")
    st.warning(f"Risk SKU: {risk[col_desc]} | {risk['YoY raw']:.0f}%")

    st.divider()

    # ================= CLIENT SCORE =================
    st.markdown("## 🎯 Client Score")

    yoy_total = calc_yoy(s26,s25)

    st.info(f"2026 Performance: €{s26:,.0f} | {q26:,.0f} pcs")

    if yoy_total > 20:
        st.success(f"A 🔥 | Growth: +{yoy_total:.0f}%")
    elif yoy_total > 0:
        st.info(f"B 👍 | Growth: +{yoy_total:.0f}%")
    else:
        st.error(f"C ⚠️ | Growth: {yoy_total:.0f}%")
