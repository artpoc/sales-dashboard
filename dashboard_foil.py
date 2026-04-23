import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha ")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

# ================= HELPERS =================
def calc_yoy(new, old):
    if pd.isna(old) or old == 0:
        if new > 0:
            return 100
        else:
            return 0
    elif (old > 0) and (pd.isna(new) or new == 0):
        return -100
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

    if "napkin" in x: return "Napkins"
    if "hat" in x: return "Hats"
    if "banner" in x: return "Banner"
    if "straw" in x: return "Straws"
    if "bag" in x: return "Bags"
    if "plate" in x: return "Plates"
    if "paper cup" in x: return "Paper Cups"
    if "plastic cup" in x: return "Plastic Cups"
    if "cup" in x: return "Cups"
    if "tablecover" in x: return "Tablecover"
    if "reusable" in x: return "Reusable"
    if "foil" in x: return "Foil"
    if "wood" in x: return "Wooden"
    if "candle" in x: return "Candles"
    if "latex" in x: return "Latex"
    if "invitation" in x: return "Invitations"
    if "article" in x: return "Articles"
    if "mask" in x: return "Masks"
    if "pinata" in x: return "Pinata"

    return "Other"

def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

def create_color_map(values):
    unique_vals = sorted(values)
    colors = px.colors.qualitative.Plotly
    return {val: colors[i % len(colors)] for i, val in enumerate(unique_vals)}

# ================= MAIN =================
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
    k2.metric("Sales 2026 (€)", f"{s26:,.0f}", f"{calc_yoy(s26,s25):+.0f}%")
    k3.metric("Qty 2025", f"{q25:,.0f}")
    k4.metric("Qty 2026", f"{q26:,.0f}", f"{calc_yoy(q26,q25):+.0f}%")

    # ================= CATEGORY PERFORMANCE =================
    if selected == "All Categories":
        st.markdown("## 📊 Category Performance")

        cat_perf = df_original.groupby("Category Clean").agg({
            val25: "sum",
            val26: "sum"
        }).reset_index()

        cat_perf["YoY %"] = cat_perf.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)

        color_map_cat = create_color_map(cat_perf["Category Clean"])

        c1,c2 = st.columns(2)

        with c1:
            st.markdown("### 2025")
            c = add_index(cat_perf.sort_values(val25, ascending=False))
            st.plotly_chart(px.pie(c, names="Category Clean", values=val25,
                                  color="Category Clean", color_discrete_map=color_map_cat))
            st.dataframe(c[["Category Clean", val25]])

        with c2:
            st.markdown("### 2026")
            c = add_index(cat_perf.sort_values(val26, ascending=False))
            st.plotly_chart(px.pie(c, names="Category Clean", values=val26,
                                  color="Category Clean", color_discrete_map=color_map_cat))
            st.dataframe(c[["Category Clean", val26, "YoY %"]])

    st.divider()

    # ================= BRAND =================
    st.markdown("## 🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({val25:"sum",val26:"sum"}).reset_index()
    brand["YoY %"] = brand.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)

    color_map_brand = create_color_map(brand[col_brand])

    c1,c2 = st.columns(2)

    with c1:
        st.markdown("### 2025")
        b = add_index(brand.sort_values(val25, ascending=False))
        st.plotly_chart(px.pie(b, names=col_brand, values=val25,
                              color=col_brand, color_discrete_map=color_map_brand))
        st.dataframe(b[[col_brand,val25]])

    with c2:
        st.markdown("### 2026")
        b = add_index(brand.sort_values(val26, ascending=False))
        st.plotly_chart(px.pie(b, names=col_brand, values=val26,
                              color=col_brand, color_discrete_map=color_map_brand))
        st.dataframe(b[[col_brand,val26,"YoY %"]])

    st.divider()

    # ================= PARETO =================
    st.markdown("## 📊 Pareto Analysis (80/20)")

    pareto = df.sort_values(val26, ascending=False)
    pareto["CumSum"] = pareto[val26].cumsum()
    total = pareto[val26].sum()
    pareto["Cum%"] = pareto["CumSum"] / total * 100

    top80 = pareto[pareto["Cum%"] <= 80]
    rest20 = pareto[pareto["Cum%"] > 80]

    st.write(f"SKU for 80%: {len(top80)} | SKU for 20%: {len(rest20)}")

    st.dataframe(add_index(top80[[col_code,col_desc,val26]]))

    fig = px.pie(
        names=["Top 80%", "Remaining 20%"],
        values=[top80[val26].sum(), rest20[val26].sum()]
    )
    st.plotly_chart(fig)

    # ================= ABC =================
    st.markdown("## 📊 ABC Analysis (70/20/10)")

    pareto["Class"] = pd.cut(
        pareto["Cum%"],
        bins=[0,70,90,100],
        labels=["A","B","C"]
    )

    abc = pareto.groupby("Class")[val26].sum().reset_index()

    st.plotly_chart(px.pie(abc, names="Class", values=val26))

    st.dataframe(add_index(pareto[[col_code,col_desc,val26,"Class"]]))

    st.divider()

    # ================= YOY =================
    st.markdown("## 📈 YoY Analysis (2026 vs 2025)")

    df_yoy = df.copy()
    df_yoy["YoY raw"] = df_yoy.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
    df_yoy["YoY %"] = df_yoy["YoY raw"].apply(yoy_format)

    df_yoy = add_index(df_yoy.sort_values("YoY raw", ascending=False))

    st.dataframe(df_yoy[[col_code,col_desc,val25,val26,qty25,qty26,"YoY %"]])

    st.divider()

    # ================= AUTO INSIGHTS =================
    st.markdown("## 🧠 Auto Insights")

    if selected == "All Categories":

        cat = df_original.groupby("Category Clean").agg({val25:"sum",val26:"sum"}).reset_index()
        cat["YoY"] = cat.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

        st.subheader("Top 3 Categories 2025")
        st.dataframe(add_index(cat.sort_values(val25, ascending=False).head(3)))

        st.subheader("Top 3 Categories 2026")
        st.dataframe(add_index(cat.sort_values(val26, ascending=False).head(3)))

        growth = cat.sort_values("YoY", ascending=False).head(3)
        risk = cat.sort_values("YoY").head(3)

        st.info(f"Growth: {', '.join(growth['Category Clean'])}")
        st.warning(f"Risk: {', '.join(risk['Category Clean'])}")

    else:
        st.subheader("Category Product Insights")

        st.write("Top 2025")
        st.dataframe(add_index(df.sort_values(val25, ascending=False).head(3)))

        st.write("Top 2026")
        st.dataframe(add_index(df.sort_values(val26, ascending=False).head(3)))

        df["YOY"] = df.apply(lambda x: calc_yoy(x[val26],x[val25]),axis=1)

        st.info(f"Growth: {df.sort_values('YOY', ascending=False).iloc[0][col_desc]}")
        st.warning(f"Risk: {df.sort_values('YOY').iloc[0][col_desc]}")

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
