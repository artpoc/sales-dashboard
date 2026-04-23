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
    arrow = "🟢 ↑" if v > 0 else "🔴 ↓"
    return f"{v:.0f}% {arrow}"

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
    return "Other"

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    col_code = "Art. Nr."
    col_desc = "Article description"
    col_brand = "Brand Name"
    col_cat = "Category"

    val25 = "Net Value 2025"
    val26 = "Net Value 2026"
    qty25 = "Quantity 2025"
    qty26 = "Quantity 2026"

    # ================= CATEGORY =================
    df["Category Clean"] = df[col_cat].fillna("").apply(normalize_category)

    categories = ["All Categories"] + sorted(df["Category Clean"].unique())
    selected = st.selectbox("📂 Category", categories)

    if selected != "All Categories":
        df = df[df["Category Clean"] == selected]

    df = df[df[col_desc].notna()]
    df = df[df[col_desc].str.lower() != "none"]

    # ================= KPI =================
    st.markdown("## 💰 KPI")

    s25, s26 = df[val25].sum(), df[val26].sum()
    q25, q26 = df[qty25].sum(), df[qty26].sum()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Sales 2025 €", f"{s25:,.0f}")
    k2.metric("Sales 2026 €", f"{s26:,.0f}", f"{calc_yoy(s26,s25):.0f}%")
    k3.metric("Qty 2025", f"{q25:,.0f}")
    k4.metric("Qty 2026", f"{q26:,.0f}", f"{calc_yoy(q26,q25):.0f}%")

    st.divider()

    # ================= BRAND =================
    st.markdown("## 🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({val25:"sum",val26:"sum"}).reset_index()

    c1,c2 = st.columns(2)
    c1.plotly_chart(px.pie(brand, names=col_brand, values=val25))
    c2.plotly_chart(px.pie(brand, names=col_brand, values=val26))

    st.dataframe(brand.sort_values(val26, ascending=False))

    st.divider()

    # ================= TOP PRODUCTS =================
    st.markdown("## 🏆 Top Products")

    c1,c2 = st.columns(2)
    c1.dataframe(df[df[val25]>0].sort_values(val25,ascending=False).head(10))
    c2.dataframe(df[df[val26]>0].sort_values(val26,ascending=False).head(10))

    st.divider()

    # ================= YOY =================
    st.markdown("## 📈 YoY Analysis")

    df["YoY %"] = df.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)
    df["YoY %"] = df["YoY %"].apply(yoy_format)

    st.dataframe(df.sort_values(val26, ascending=False))

    st.divider()

    # ================= PORTFOLIO =================
    st.markdown("## 🎯 Portfolio")

    top10 = df.sort_values(val26, ascending=False).head(10)
    share = top10[val26].sum()/s26*100 if s26 else 0

    st.plotly_chart(px.pie(top10, names=col_desc, values=val26))
    st.markdown(f"Top10 Concentration: {share:.0f}%")

    if share > 50:
        st.success("High concentration")
    else:
        st.warning("Low concentration")

    st.divider()

    # ================= AUTO INSIGHTS =================
    st.markdown("## 🧠 AUTO INSIGHTS")

    cat = df.groupby("Category Clean").agg({val25:"sum",val26:"sum"}).reset_index()
    cat["YoY"] = cat.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

    growth = cat.sort_values("YoY",ascending=False).head(3)
    decline = cat.sort_values("YoY").head(3)

    c1,c2 = st.columns(2)

    with c1:
        st.markdown("### 🚀 Growth")
        for _,r in growth.iterrows():
            st.success(f"{r['Category Clean']} +{r['YoY']:.0f}%")

    with c2:
        st.markdown("### ⚠️ Decline")
        for _,r in decline.iterrows():
            st.error(f"{r['Category Clean']} {r['YoY']:.0f}%")

    st.divider()

    # ================= BRAND INSIGHTS =================
    st.markdown("## 🏷️ Brand Insights")

    brand["YoY"] = brand.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

    st.success(f"Top Growth Brand: {brand.sort_values('YoY',ascending=False).iloc[0][col_brand]}")
    st.error(f"Risk Brand: {brand.sort_values('YoY').iloc[0][col_brand]}")

    st.divider()

    # ================= SKU INSIGHTS =================
    st.markdown("## 📦 SKU Insights")

    df["YoY raw"] = df.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

    st.success(f"Best SKU: {df.sort_values('YoY raw',ascending=False).iloc[0][col_desc]}")
    st.error(f"Worst SKU: {df.sort_values('YoY raw').iloc[0][col_desc]}")

    st.divider()

    # ================= CLIENT SCORE =================
    st.markdown("## 🎯 Client Score")

    score = "A 🔥" if calc_yoy(s26,s25)>20 else "B 👍" if calc_yoy(s26,s25)>0 else "C ⚠️"
    st.markdown(f"### {score}")
