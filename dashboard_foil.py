import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha ")

col1, col2 = st.columns(2)

with col1:
    file_l4l = st.file_uploader("📂 Upload L4L (2025 vs 2026)", type=["xlsx"])

with col2:
    file_full = st.file_uploader("📂 Upload Full Year (2024 vs 2025)", type=["xlsx"])

mode = st.radio(
    "Select Analysis Mode",
    ["L4L (2025 vs 2026)", "Full Year (2024 vs 2025)"]
)

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

    if is_l4l:
        df = pd.read_excel(file_l4l, decimal=",", thousands=" ")
    else:
        df = pd.read_excel(file_full, decimal=",", thousands=" ")

    df.columns = df.columns.str.strip()

# ================= MAIN =================
if (mode == "L4L (2025 vs 2026)" and file_l4l) or \
   (mode == "Full Year (2024 vs 2025)" and file_full):

    # 🔥 KLUCZOWY FIX
    df = pd.read_excel(file, decimal=",", thousands=" ")
    df.columns = df.columns.str.strip()

    col_customer = "Customer Name"
    col_country = "Country"
    col_vat = "Vat ID Nr."
    col_code = "Art. Nr."
    col_desc = "Article description"
    col_brand = "Brand Name"
    col_cat = "Category"

    def detect_columns(df):
        net = sorted([c for c in df.columns if "Net Value" in c])
        qty = sorted([c for c in df.columns if "Quantity" in c])

        if is_l4l:
            return net[0], net[1], qty[0], qty[1]
        else:
            return net[1], net[1], qty[1], qty[1]  # FULL YEAR = tylko NOWY ROK


    val_old, val_new, qty_old, qty_new = detect_columns(df)

    # ✅ BEZPIECZNA KONWERSJA
    for c in [val_old, val_new, qty_old, qty_new]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ================= COUNTRY FILTER =================
    countries = ["All Countries"] + sorted(df[col_country].dropna().unique())

    selected_country = st.selectbox("🌍 Select Country", countries)

    if selected_country != "All Countries":
        df = df[df[col_country] == selected_country]


    # ================= CATEGORY FILTER =================
    ALLOWED_CATEGORIES = [
        "Napkins","Hats","Banner","Straws","Bags","Plates","Paper Cups",
        "Tablecover","Reusable","Foil","Wooden","Candles","Latex",
        "Invitations","Articles","Masks","Pinata","Plastic Cups"
    ]

    # CATEGORY CLEAN (MUSI BYĆ WCZEŚNIEJ)
    df["Category Clean"] = df[col_cat].fillna("").apply(normalize_category)

    df = df[df["Category Clean"].isin(ALLOWED_CATEGORIES)]

    # DOPIERO TERAZ ZAPIS PEŁNEGO DATASETU
    df_original_all = df.copy()
    df_context = df_original_all.copy()

    if not is_l4l:
        df_analysis = df_original_all.copy()
    else:
        df_analysis = df.copy()


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

    s25, s26 = df[val_old].sum(), df[val_new].sum()
    q25, q26 = df[qty_old].sum(), df[qty_new].sum()

    k1,k2,k3,k4 = st.columns(4)
    k1.metric(f"Sales {val_old.split()[-1]} (€)", f"{s25:,.2f}")
    k2.metric(f"Sales {val_new.split()[-1]} (€)", f"{s26:,.2f}", f"{calc_yoy(s26,s25):+.0f}%")
    k3.metric("Qty 2025", f"{q25:,.0f}")
    k4.metric("Qty 2026", f"{q26:,.0f}", f"{calc_yoy(q26,q25):+.0f}%")

    # ================= CATEGORY PERFORMANCE =================
    if selected == "All Categories":
        st.markdown("## 📊 Category Performance")

        cat_perf = df_context.groupby("Category Clean").agg({
            val_old: "sum",
            val_new: "sum"
        }).reset_index()

        total25 = cat_perf[val_old].sum()
        total26 = cat_perf[val_new].sum()

        if total25 == 0 or total26 == 0:
            st.warning("No data for category performance")
        else:
            cat_perf["Share 2025 %"] = cat_perf[val_old] / total25 * 100
            cat_perf["Share 2026 %"] = cat_perf[val_new] / total26 * 100

            cat_perf["YoY"] = cat_perf.apply(lambda x: calc_yoy(x[val_new], x[val_old]), axis=1)
            cat_perf["YoY %"] = cat_perf["YoY"].apply(yoy_format)

            cat_perf["Share 2025 %"] = cat_perf["Share 2025 %"].map(lambda x: f"{x:.1f}%")
            cat_perf["Share 2026 %"] = cat_perf["Share 2026 %"].map(lambda x: f"{x:.1f}%")

            c1, c2 = st.columns(2)

            with c1:
                st.markdown("### 2025")
                st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val_old))

            with c2:
                st.markdown("### 2026")
                st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val_new))

            st.markdown("### Category Comparison")
            st.dataframe(add_index(
                cat_perf.sort_values(val_new, ascending=False)[[
                    "Category Clean",
                    val_old, "Share 2025 %",
                    val_new, "Share 2026 %",
                    "YoY %"
                ]]
            ))

    st.divider()

    # ================= BRAND PERFORMANCE =================
    st.markdown("## 🏷️ Brand Performance")

    brand = df.groupby(col_brand).agg({
        val_old: "sum",
        val_new: "sum"
    }).reset_index()

    # 🔥 SHARE %
    total25 = brand[val_old].sum()
    total26 = brand[val_new].sum()

    brand["Share 2025 %"] = brand[val_old] / total25 * 100
    brand["Share 2026 %"] = brand[val_new] / total26 * 100

    # 🔥 YoY
    brand["YoY"] = brand.apply(lambda x: calc_yoy(x[val_new], x[val_old]), axis=1)
    brand["YoY %"] = brand["YoY"].apply(yoy_format)

    # 🔥 format %
    brand["Share 2025 %"] = brand["Share 2025 %"].map(lambda x: f"{x:.1f}%")
    brand["Share 2026 %"] = brand["Share 2026 %"].map(lambda x: f"{x:.1f}%")

    c1,c2 = st.columns(2)

    with c1:
        st.markdown("### 2025")
        st.plotly_chart(px.pie(brand, names=col_brand, values=val_old))

    with c2:
        st.markdown("### 2026")
        st.plotly_chart(px.pie(brand, names=col_brand, values=val_new))

    st.dataframe(add_index(
        brand[[
            col_brand,
            val_old, "Share 2025 %",
            val_new, "Share 2026 %",
            "YoY %"
        ]].sort_values(val_new, ascending=False)
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
                val_old: "sum",
                qty_old: "sum"
            }).reset_index()

            # 🔥 tylko SKU ze sprzedażą
            d25 = d25[d25[val_old] > 0]

            if d25.empty:
                st.info("No sales in 2025")
            else:
                top25 = d25.sort_values(val_old, ascending=False).head(10)

                total25 = d25[val_old].sum()
                top25_sum = top25[val_old].sum()

                # 🔥 udział %
                top25["Share %"] = top25[val_old] / total25 * 100

                st.dataframe(add_index(
                    top25[[col_code, col_desc, val_old, qty_old, "Share %"]]
                ))

                st.write(f"Top 10 share: {(top25_sum/total25*100):.1f}%")


        # ================= 2026 =================
        with c2:
            st.write("### 2026")

            d26 = df.groupby([col_code, col_desc]).agg({
                val_new: "sum",
                qty_new: "sum"
            }).reset_index()

            # 🔥 tylko SKU ze sprzedażą
            d26 = d26[d26[val_new] > 0]

            if d26.empty:
                st.info("No sales in 2026")
            else:
                top26 = d26.sort_values(val_new, ascending=False).head(10)

                total26 = d26[val_new].sum()
                top26_sum = top26[val_new].sum()

                # 🔥 udział %
                top26["Share %"] = top26[val_new] / total26 * 100

                st.dataframe(add_index(
                    top26[[col_code, col_desc, val_new, qty_new, "Share %"]]
                ))

                st.write(f"Top 10 share: {(top26_sum/total26*100):.1f}%")

    st.divider()

    # ================= PARETO =================
    st.markdown("## 📊 Pareto Analysis")

    tab1, tab2 = st.tabs(["2025","2026"])

    for year, val in zip([tab1, tab2], [val_old, val_new]):
        with year:

            # 🔥 agregacja do poziomu SKU (unikalny Art. Nr.)
            p = df.groupby(col_code).agg({
                col_desc: "first",          # opis pomocniczo
                "Category Clean": "first",  # kategoria pomocniczo
                val: "sum"
            }).reset_index()

            # 🔥 tylko SKU ze sprzedażą w danym roku
            p = p[p[val] > 0]

            if p.empty:
                st.info("No sales in this year")
            else:
                # 🔥 sortowanie malejąco
                p = p.sort_values(val, ascending=False)

                # 🔥 kumulacja wartości
                p["cum_value"] = p[val].cumsum()
                total_value = p[val].sum()
                p["cum_share"] = p["cum_value"] / total_value

                # 🔥 Pareto 80%
                top80 = p[p["cum_share"] <= 0.8]

                # 🔥 liczba SKU
                total_sku = p[col_code].nunique()
                pareto_sku = top80[col_code].nunique()

                # 🔥 % SKU które robi 80%
                sku_share = pareto_sku / total_sku * 100

                st.write(f"Top SKU for 80%: {pareto_sku} / {total_sku} ({sku_share:.1f}% of SKU)")

                st.dataframe(add_index(
                    top80[[col_code, col_desc, "Category Clean", val]]
                ))

    st.divider()

    # ================= ABC =================
    st.markdown("## 📊 ABC Analysis")

    tab1, tab2 = st.tabs(["2025","2026"])

    for year, val in zip([tab1, tab2], [val_old, val_new]):
        with year:
            a = df.groupby([col_code, col_desc]).agg({
                val_old:"sum",
                val_new:"sum"
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
        val_old: "sum",
        val_new: "sum",
        qty_old: "sum",
        qty_new: "sum"
    }).reset_index()

    df_yoy["YoY %"] = df_yoy.apply(lambda x: yoy_format(calc_yoy(x[val_new], x[val_old])), axis=1)

    st.dataframe(add_index(
        df_yoy.sort_values(val_new, ascending=False)
        [[col_code,col_desc,val_old,val_new,qty_old,qty_new,"YoY %"]]
    ))

    st.divider()

    # ================= AUTO INSIGHTS =================
    st.markdown("## 🧠 Auto Insights")

    cat = df_context.groupby("Category Clean").agg({
        val_old:"sum",
        val_new:"sum"
    }).reset_index()

    cat["YoY"] = cat.apply(lambda x: calc_yoy(x[val_new], x[val_old]), axis=1)
    cat["YoY %"] = cat["YoY"].apply(yoy_format)

    # ================= TOP 3 =================
    st.write("### Top 5 Categories")

    c1, c2 = st.columns(2)

    with c1:
        st.write("#### 2025")
        top25 = cat.sort_values(val_old, ascending=False).head(5)
        st.dataframe(add_index(top25[["Category Clean", val_old]]))

    with c2:
        st.write("#### 2026")
        top26 = cat.sort_values(val_new, ascending=False).head(5)
        st.dataframe(add_index(top26[["Category Clean", val_new, "YoY %"]]))

    # ================= GROWTH =================
    st.write("### Growth (L4L)")

    growth = cat[cat["YoY"] > 0].sort_values("YoY", ascending=False).head(5)

    if growth.empty:
        st.info("There is no growth in categories")
    else:
        st.dataframe(add_index(growth[["Category Clean", val_old, val_new, "YoY %"]]))

    # ================= RISK =================
    st.write("### Risk")

    risk = cat[cat["YoY"] < 0].sort_values("YoY").head(5)

    if risk.empty:
        st.success("There is no risk in categories")
    else:
        st.dataframe(add_index(risk[["Category Clean", val_old, val_new, "YoY %"]]))

    st.divider()

    # ================= CUSTOMER IMPACT =================
    st.markdown("## 👥 Customer Impact (Growth vs Decline)")

    # 🔥 wybór kategorii
    all_categories = sorted(df_original_all["Category Clean"].dropna().unique())
    selected_cat_impact = st.selectbox(
        "Select Category for Impact Analysis",
        ["All Categories"] + all_categories
    )

    # 🔥 NOWY: wybór brandu
    all_brands = sorted(df_original_all[col_brand].dropna().unique())
    selected_brand_impact = st.selectbox(
        "Select Brand (License)",
        ["All Brands"] + all_brands
    )

    # ================= FUNCTIONS =================
    def calc_yoy_clean(new, old):
        if old < 0 and new == 0:
            return None

        if pd.isna(old) or old == 0:
            return 100 if new > 0 else 0
        elif old > 0 and new == 0:
            return -100
        else:
            return (new - old) / abs(old) * 100


    def yoy_label(val, special):
        if special:
            return "Recovery to 0 ⚠️"
        return yoy_format(val)


    # ================= DATA PREP =================
    df_impact = df_original_all.copy()

    # 🔥 filtr kategorii
    if selected_cat_impact != "All Categories":
        df_impact = df_impact[df_impact["Category Clean"] == selected_cat_impact]

    # 🔥 filtr brandu (NOWE)
    if selected_brand_impact != "All Brands":
        df_impact = df_impact[df_impact[col_brand] == selected_brand_impact]

    # 🔥 agregacja per klient
    impact = df_impact.groupby(col_customer).agg({
        val_old: "sum",
        val_new: "sum"
    }).reset_index()

    # 🔥 usuwamy klientów bez sprzedaży
    impact = impact[(impact[val_old] != 0) | (impact[val_new] != 0)]

    # ================= CALCULATIONS =================
    impact["Change Value"] = impact[val_new] - impact[val_old]

    impact["Special Case"] = (
        (impact[val_old] < 0) & (impact[val_new] == 0)
    )

    impact["YoY"] = impact.apply(
        lambda x: calc_yoy_clean(x[val_new], x[val_old]),
        axis=1
    )

    impact["YoY %"] = impact.apply(
        lambda x: yoy_label(x["YoY"], x["Special Case"]),
        axis=1
    )

    # ================= TOP GROWTH =================
    st.write("### 🟢 Top Growth Drivers")

    growth = impact[
        (impact["Change Value"] > 0) & (~impact["Special Case"])
    ].sort_values("Change Value", ascending=False).head(10)

    growth_special = impact[impact["Special Case"]].head(10)
    growth = pd.concat([growth, growth_special])

    if growth.empty:
        st.info("No growth generated by customers")
    else:
        st.dataframe(add_index(
            growth[[col_customer, val_old, val_new, "Change Value", "YoY %"]]
        ))

    # ================= TOP DECLINE =================
    st.write("### 🔴 Top Decline Drivers")

    decline = impact[
        (impact["Change Value"] < 0)
    ].sort_values("Change Value").head(10)

    decline_special = impact[impact["Special Case"]].head(10)
    decline = pd.concat([decline, decline_special])

    if decline.empty:
        st.success("No decline across customers")
    else:
        st.dataframe(add_index(
            decline[[col_customer, val_old, val_new, "Change Value", "YoY %"]]
        ))
