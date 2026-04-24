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
    elif (old > 0) and (pd.isna(new) or new == 0):
        return -100
    else:
        return (new - old) / old * 100

def yoy_format(v):
    if v > 0:
        return f"+{v:.0f}% 🟢"
    elif v < 0:
        return f"{v:.0f}% 🔴"
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

    # 🔥 KLUCZOWY FIX
    df = pd.read_excel(uploaded_file, decimal=",", thousands=" ")
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

    # ✅ BEZPIECZNA KONWERSJA
    for c in [val25, val26, qty25, qty26]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ================= CATEGORY FILTER =================
    ALLOWED_CATEGORIES = [
        "Napkins","Hats","Banner","Straws","Bags","Plates","Paper Cups",
        "Tablecover","Reusable","Foil","Wooden","Candles","Latex",
        "Invitations","Articles","Masks","Pinata","Plastic Cups"
    ]

    df["Category Clean"] = df[col_cat].fillna("").apply(normalize_category)
    df = df[df["Category Clean"].isin(ALLOWED_CATEGORIES)]

    # 🔥 ZAPIS PEŁNYCH DANYCH
    df_original_all = df.copy()

    # ================= CUSTOMER FILTER =================
    customers = ["All Customers"] + sorted(df[col_customer].dropna().unique())
    selected_customer = st.selectbox("👤 Select Customer", customers)

    if selected_customer != "All Customers":
        df = df[df[col_customer] == selected_customer]

    # ================= DATA CONTEXT =================
    if selected_customer == "All Customers":
        df_context = df_original_all.copy()
    else:
        df_context = df.copy()

    # ================= CUSTOMER INFO =================
    st.subheader("👤 Customer Information")

    if selected_customer == "All Customers":
        st.write("**Customer:** All Customers")
        st.write(f"**Total Clients:** {df_original_all[col_customer].nunique()}")
    else:
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
        c2.write(f"**Country:** {df[col_country].iloc[0]}")
        c3.write(f"**VAT:** {df[col_vat].iloc[0]}")

    # ================= CATEGORY =================
    categories = ["All Categories"] + sorted(df["Category Clean"].unique())
    selected = st.selectbox("📂 Select Category", categories)

    # 🔥 KLUCZOWE – zawsze pełne dane
    df_original = df_original_all.copy()

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
    k1.metric("Sales 2025 (€)", f"{s25:,.2f}")
    k2.metric("Sales 2026 (€)", f"{s26:,.2f}", f"{calc_yoy(s26,s25):+.0f}%")
    k3.metric("Qty 2025", f"{q25:,.0f}")
    k4.metric("Qty 2026", f"{q26:,.0f}", f"{calc_yoy(q26,q25):+.0f}%")

    # ================= CATEGORY PERFORMANCE =================
    if selected == "All Categories":
        st.markdown("## 📊 Category Performance")

        cat_perf = df_context.groupby("Category Clean").agg({
            val25: "sum",
            val26: "sum"
        }).reset_index()

        # 🔥 SHARE %
        total25 = cat_perf[val25].sum()
        total26 = cat_perf[val26].sum()

        cat_perf["Share 2025 %"] = cat_perf[val25] / total25 * 100
        cat_perf["Share 2026 %"] = cat_perf[val26] / total26 * 100

        # 🔥 YoY
        cat_perf["YoY"] = cat_perf.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
        cat_perf["YoY %"] = cat_perf["YoY"].apply(yoy_format)

        # 🔥 format %
        cat_perf["Share 2025 %"] = cat_perf["Share 2025 %"].map(lambda x: f"{x:.1f}%")
        cat_perf["Share 2026 %"] = cat_perf["Share 2026 %"].map(lambda x: f"{x:.1f}%")

        c1,c2 = st.columns(2)

        with c1:
            st.markdown("### 2025")
            st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val25))

        with c2:
            st.markdown("### 2026")
            st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val26))

        st.markdown("### Category Comparison")
        st.dataframe(add_index(
            cat_perf[[
                "Category Clean",
                val25, "Share 2025 %",
                val26, "Share 2026 %",
                "YoY %"
            ]].sort_values(val26, ascending=False)
        ))

    st.divider()

    # ================= BRAND PERFORMANCE =================
    st.markdown("## 🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({
        val25: "sum",
        val26: "sum"
    }).reset_index()

    # 🔥 SHARE %
    total25 = brand[val25].sum()
    total26 = brand[val26].sum()

    brand["Share 2025 %"] = brand[val25] / total25 * 100
    brand["Share 2026 %"] = brand[val26] / total26 * 100

    # 🔥 YoY
    brand["YoY"] = brand.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
    brand["YoY %"] = brand["YoY"].apply(yoy_format)

    # 🔥 format %
    brand["Share 2025 %"] = brand["Share 2025 %"].map(lambda x: f"{x:.1f}%")
    brand["Share 2026 %"] = brand["Share 2026 %"].map(lambda x: f"{x:.1f}%")

    c1,c2 = st.columns(2)

    with c1:
        st.markdown("### 2025")
        st.plotly_chart(px.pie(brand, names=col_brand, values=val25))

    with c2:
        st.markdown("### 2026")
        st.plotly_chart(px.pie(brand, names=col_brand, values=val26))

    st.dataframe(add_index(
        brand[[
            col_brand,
            val25, "Share 2025 %",
            val26, "Share 2026 %",
            "YoY %"
        ]].sort_values(val26, ascending=False)
    ))

    st.divider()

    # ================= TOP PRODUCTS =================
    st.markdown("## 🏆 Top Products")

    if df.empty:
        st.warning("No data available for selected filters")
    else:
        c1, c2 = st.columns(2)

        # ================= 2025 =================
        with c1:
            st.write("### 2025")

            d25 = df.groupby([col_code, col_desc]).agg({
                val25: "sum",
                qty25: "sum"
            }).reset_index()

            d25 = d25[d25[val25] > 0]

            if d25.empty:
                st.info("No sales in 2025")
            else:
                top25 = d25.sort_values(val25, ascending=False).head(10)
                st.dataframe(add_index(top25[[col_code, col_desc, val25, qty25]]))

                total25 = d25[val25].sum()
                top25_sum = top25[val25].sum()

                st.write(f"Top 10 share: {(top25_sum/total25*100):.1f}%")

                st.plotly_chart(px.pie(
                    pd.DataFrame({
                        "Group": ["Top 10", "Others"],
                        "Value": [top25_sum, total25 - top25_sum]
                    }),
                    names="Group",
                    values="Value"
                ))

        # ================= 2026 =================
        with c2:
            st.write("### 2026")

            d26 = df.groupby([col_code, col_desc]).agg({
                val26: "sum",
                qty26: "sum"
            }).reset_index()

            d26 = d26[d26[val26] > 0]

            if d26.empty:
                st.info("No sales in 2026")
            else:
                top26 = d26.sort_values(val26, ascending=False).head(10)
                st.dataframe(add_index(top26[[col_code, col_desc, val26, qty26]]))

                total26 = d26[val26].sum()
                top26_sum = top26[val26].sum()

                st.write(f"Top 10 share: {(top26_sum/total26*100):.1f}%")

                st.plotly_chart(px.pie(
                    pd.DataFrame({
                        "Group": ["Top 10", "Others"],
                        "Value": [top26_sum, total26 - top26_sum]
                    }),
                    names="Group",
                    values="Value"
                ))

    st.divider()

    # ================= PARETO =================
    st.markdown("## 📊 Pareto Analysis")

    tab1, tab2 = st.tabs(["2025","2026"])

    for year, val in zip([tab1, tab2], [val25, val26]):
        with year:
            p = df.groupby([col_code, col_desc, "Category Clean"]).agg({
                val25:"sum",
                val26:"sum"
            }).reset_index()

            p = p.sort_values(val, ascending=False)
            p["cum"] = p[val].cumsum()/p[val].sum()

            top80 = p[p["cum"] <= 0.8]

            st.write(f"Top SKU for 80%: {len(top80)} / {len(p)}")

            # 🔥 dodany Article Number
            st.dataframe(add_index(
                top80[[col_code, col_desc, "Category Clean", val]]
            ))

    st.divider()

    # ================= ABC =================
    st.markdown("## 📊 ABC Analysis")

    tab1, tab2 = st.tabs(["2025","2026"])

    for year, val in zip([tab1, tab2], [val25, val26]):
        with year:
            a = df.groupby([col_code, col_desc]).agg({
                val25:"sum",
                val26:"sum"
            }).reset_index()

            # 🔥 usuwamy zerowe SKU
            a = a[a[val] > 0]

            a = a.sort_values(val, ascending=False)
            a["cum"] = a[val].cumsum()/a[val].sum()

            a["segment"] = "C"
            a.loc[a["cum"]<=0.7,"segment"]="A"
            a.loc[(a["cum"]>0.7)&(a["cum"]<=0.9),"segment"]="B"

            # 🔥 liczba SKU w segmentach
            seg_counts = a["segment"].value_counts()

            st.write(f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}")

            st.dataframe(add_index(
                a[[col_code, col_desc, val, "segment"]]
            ))

    st.divider()

    # ================= YOY =================
    st.markdown("## 📈 L4L Analysis")

    df_yoy = df.groupby([col_code, col_desc]).agg({
        val25: "sum",
        val26: "sum",
        qty25: "sum",
        qty26: "sum"
    }).reset_index()

    df_yoy["YoY %"] = df_yoy.apply(lambda x: yoy_format(calc_yoy(x[val26], x[val25])), axis=1)

    st.dataframe(add_index(
        df_yoy.sort_values(val26, ascending=False)
        [[col_code,col_desc,val25,val26,qty25,qty26,"YoY %"]]
    ))

    st.divider()

    # ================= AUTO INSIGHTS =================
    st.markdown("## 🧠 Auto Insights")

    cat = df_context.groupby("Category Clean").agg({
        val25:"sum",
        val26:"sum"
    }).reset_index()

    cat["YoY"] = cat.apply(lambda x: calc_yoy(x[val26], x[val25]), axis=1)
    cat["YoY %"] = cat["YoY"].apply(yoy_format)

    # ================= TOP 3 =================
    st.write("### Top 5 Categories")

    c1, c2 = st.columns(2)

    with c1:
        st.write("#### 2025")
        top25 = cat.sort_values(val25, ascending=False).head(5)
        st.dataframe(add_index(top25[["Category Clean", val25]]))

    with c2:
        st.write("#### 2026")
        top26 = cat.sort_values(val26, ascending=False).head(5)
        st.dataframe(add_index(top26[["Category Clean", val26, "YoY %"]]))

    # ================= GROWTH =================
    st.write("### Growth (L4L)")

    growth = cat[cat["YoY"] > 0].sort_values("YoY", ascending=False).head(5)

    if growth.empty:
        st.info("There is no growth in categories")
    else:
        st.dataframe(add_index(growth[["Category Clean", val25, val26, "YoY %"]]))

    # ================= RISK =================
    st.write("### Risk")

    risk = cat[cat["YoY"] < 0].sort_values("YoY").head(5)

    if risk.empty:
        st.success("There is no risk in categories")
    else:
        st.dataframe(add_index(risk[["Category Clean", val25, val26, "YoY %"]]))

    st.divider()

    # ================= CLIENT SCORE =================
    st.markdown("## 🎯 Client Score")

    yoy_total = calc_yoy(s26,s25)
    qty_diff = q26 - q25

    st.info(f"2026 Sales: €{s26:,.2f} | Qty: {q26:,.0f} (Δ {qty_diff:+,.0f} vs 2025)")

    if yoy_total > 20:
        st.success(f"A 🔥 | Growth: +{yoy_total:.0f}%")
    elif yoy_total > 0:
        st.info(f"B 👍 | Growth: +{yoy_total:.0f}%")
    else:
        st.error(f"C ⚠️ | Growth: {yoy_total:.0f}%")
