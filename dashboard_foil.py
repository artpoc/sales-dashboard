import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha ")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

# ================= HELPERS =================
def calc_yoy(new, old):
    if pd.isna(old) or old == 0:
        return 100 if new > 0 else 0
    elif old > 0 and (pd.isna(new) or new == 0):
        return -100
    return (new - old) / old * 100

def yoy_format(v):
    if v > 0:
        return f"+{v:.0f}% 🟢"
    elif v < 0:
        return f"{v:.0f}% 🔴"
    return "0%"

def normalize_category(x):
    x = str(x).lower()
    if "napkin" in x: return "Napkins"
    if "hat" in x: return "Hats"
    if "banner" in x: return "Banner"
    if "straw" in x: return "Straws"
    if "bag" in x: return "Bags"
    if "plate" in x: return "Plates"
    if "paper cup" in x: return "Paper Cups"
    if "plastic cup" in x: return "Plastic Cups"
    if "tablecover" in x: return "Tablecover"
    if "reusable" in x: return "Reusable"
    if "foil" in x: return "Foil"
    if "wood" in x: return "Wooden"
    if "candle" in x: return "Candles"
    if "latex" in x: return "Latex"
    if "invitation" in x: return "Invitations"
    if "mask" in x: return "Masks"
    if "pinata" in x: return "Pinata"
    if "article" in x: return "Articles"
    return "Other"

def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

# ================= MAIN =================
if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

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

    # ===== NUMERIC FIX (KLUCZ DO BŁĘDU SUMY) =====
    for c in [val25, val26, qty25, qty26]:
        df[c] = (
            df[c]
            .astype(str)
            .str.replace(" ", "")
            .str.replace(",", ".")
        )
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ================= CATEGORY CLEAN =================
    df["Category Clean"] = df[col_cat].fillna("").apply(normalize_category)

    # MASTER DF
    df_all = df.copy()

    # ================= CUSTOMER FILTER =================
    customers = ["All Customers"] + sorted(df_all[col_customer].dropna().unique())
    selected_customer = st.selectbox("👤 Select Customer", customers)

    if selected_customer != "All Customers":
        df = df_all[df_all[col_customer] == selected_customer]
    else:
        df = df_all.copy()

    # ================= CUSTOMER INFO =================
    st.subheader("👤 Customer Information")

    c1, c2, c3 = st.columns(3)

    if selected_customer == "All Customers":
        c1.write("**Customer:** All Customers")
        c2.write(f"**Countries:** {df[col_country].nunique()}")
        c3.write(f"**VATs:** {df[col_vat].nunique()}")
    else:
        if not df.empty:
            c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
            c2.write(f"**Country:** {df[col_country].iloc[0]}")
            c3.write(f"**VAT:** {df[col_vat].iloc[0]}")

    # ================= CATEGORY =================
    categories = ["All Categories"] + sorted(df["Category Clean"].unique())
    selected = st.selectbox("📂 Select Category", categories)

    df_original = df.copy()

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
    k2.metric("Sales 2026 (€)", f"{s26:,.0f}", yoy_format(calc_yoy(s26,s25)))
    k3.metric("Qty 2025", f"{q25:,.0f}")
    k4.metric("Qty 2026", f"{q26:,.0f}", yoy_format(calc_yoy(q26,q25)))

    # ================= CATEGORY PERFORMANCE =================
    if selected == "All Categories":
        st.markdown("## 📊 Category Performance")

        cat_perf = df_original.groupby("Category Clean").agg({
            val25: "sum",
            val26: "sum"
        }).reset_index()

        cat_perf["YoY"] = cat_perf.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
        cat_perf["YoY %"] = cat_perf["YoY"].apply(yoy_format)

        c1,c2 = st.columns(2)

        with c1:
            st.markdown("### 2025")
            st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val25))

        with c2:
            st.markdown("### 2026")
            st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val26))

        st.markdown("### Category Comparison")
        st.dataframe(add_index(
            cat_perf[["Category Clean", val25, val26, "YoY %"]]
            .sort_values(val26, ascending=False)
        ))

    st.divider()

    # ================= BRAND PERFORMANCE =================
    st.markdown("## 🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({val25:"sum",val26:"sum"}).reset_index()
    brand["YoY"] = brand.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
    brand["YoY %"] = brand["YoY"].apply(yoy_format)

    st.markdown("### Brand Comparison (2025 vs 2026)")
    st.dataframe(add_index(
        brand[[col_brand,val25,val26,"YoY %"]]
        .sort_values(val26, ascending=False)
    ))

    st.divider()

    # ================= TOP PRODUCTS =================
    st.markdown("## 🏆 Top Products")

    c1,c2 = st.columns(2)

    with c1:
        d = df.sort_values(val25, ascending=False).head(10)
        st.dataframe(add_index(d[[col_code,col_desc,val25,qty25]]))

        fig = px.pie(d, names=col_desc, values=val25)
        st.plotly_chart(fig)

    with c2:
        d = df.sort_values(val26, ascending=False).head(10)
        st.dataframe(add_index(d[[col_code,col_desc,val26,qty26]]))

        fig = px.pie(d, names=col_desc, values=val26)
        st.plotly_chart(fig)

    st.divider()

    # ================= PARETO =================
    st.markdown("## 📊 Pareto Analysis")

    tab1, tab2 = st.tabs(["2025","2026"])

    for year, val in zip([tab1, tab2], [val25, val26]):
        with year:
            p = df.groupby([col_desc, "Category Clean"]).agg({
                val25:"sum",
                val26:"sum"
            }).reset_index()

            p = p.sort_values(val, ascending=False)
            p["cum"] = p[val].cumsum()/p[val].sum()

            top80 = p[p["cum"] <= 0.8]

            st.write(f"Top SKU for 80%: {len(top80)} / {len(p)}")
            st.dataframe(add_index(top80[[col_desc,"Category Clean",val25,val26]]))

    st.divider()

    # ================= ABC =================
    st.markdown("## 📊 ABC Analysis")

    tab1, tab2 = st.tabs(["2025","2026"])

    for year, val in zip([tab1, tab2], [val25, val26]):
        with year:
            a = df.groupby(col_desc).agg({val25:"sum",val26:"sum"}).reset_index()
            a = a.sort_values(val, ascending=False)
            a["cum"] = a[val].cumsum()/a[val].sum()

            a["segment"] = "C"
            a.loc[a["cum"]<=0.7,"segment"]="A"
            a.loc[(a["cum"]>0.7)&(a["cum"]<=0.9),"segment"]="B"

            st.dataframe(add_index(a[[col_desc,val25,val26,"segment"]]))

    st.divider()

    # ================= YOY =================
    st.markdown("## 📈 YoY Analysis")

    df_yoy = df.copy()
    df_yoy["YoY raw"] = df_yoy.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
    df_yoy["YoY %"] = df_yoy["YoY raw"].apply(yoy_format)

    st.dataframe(add_index(
        df_yoy.sort_values(val26, ascending=False)
        [[col_code,col_desc,val25,val26,qty25,qty26,"YoY %"]]
    ))

    st.divider()

    # ================= CLIENT SCORE =================
    st.markdown("## 🎯 Client Score")

    yoy_total = calc_yoy(s26,s25)
    qty_diff = q26 - q25

    st.info(f"2026 Sales: €{s26:,.0f} | Qty: {q26:,.0f} (Δ {qty_diff:+,.0f} vs 2025)")

    if yoy_total > 20:
        st.success(f"A 🔥 | Growth: +{yoy_total:.0f}%")
    elif yoy_total > 0:
        st.info(f"B 👍 | Growth: +{yoy_total:.0f}%")
    else:
        st.error(f"C ⚠️ | Growth: {yoy_total:.0f}%")
