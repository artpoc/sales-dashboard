import streamlit as st
import pandas as pd
import plotly.express as px

# ================= HELPERS & FUNCTIONS =================
def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1  # Wymuszenie numerowania od 1 zamiast od 0
    
    # Zabezpieczenie dokładności liczb (eliminacja błędów zmiennoprzecinkowych z Pythona)
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].round(2)
        
    return df

def calc_yoy_clean(new, old):
    if old < 0 and new == 0:
        return None
    if pd.isna(old) or old == 0:
        return 100 if new > 0 else 0
    elif old > 0 and (pd.isna(new) or new == 0):
        return -100
    else:
        return (new - old) / abs(old) * 100

def yoy_label(val, special=False):
    if special:
        return "Recovery to 0 ⚠️"
    if val is None:
        return "0%"
    if val > 0:
        return f"+{val:.0f}% 🟢"
    elif val < 0:
        return f"{val:.0f}% 🔴"
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

# ================= CONFIG & UI =================
st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha")

# ================= FILE UPLOAD =================
col1, col2 = st.columns(2)

with col1:
    file_l4l = st.file_uploader("📂 Upload L4L (2025 vs 2026)", type=["xlsx"])

with col2:
    file_full = st.file_uploader("📂 Upload Full Year (2024 vs 2025)", type=["xlsx"])

mode = st.radio(
    "Select Analysis Mode",
    ["L4L (2025 vs 2026)", "Full Year (2024 vs 2025)"]
)

# ================= LOAD =================
file = file_l4l if mode == "L4L (2025 vs 2026)" else file_full

if file is None:
    st.warning("⬆️ Upload file for selected mode")
    st.stop()

def clean_number(x):
    if pd.isna(x):
        return 0
    x = str(x).replace(" ", "").replace(",", ".")
    try:
        return float(x)
    except:
        return 0

for c in [val_old, val_new]:
    df[c] = df[c].apply(clean_number)

for c in [qty_old, qty_new]:
    df[c] = df[c].apply(clean_number)
    
df.columns = df.columns.str.strip()

# ================= SAFE COLUMN DETECTION (DYNAMIC INDEX) =================
# Oczekujemy, że kolumny to odpowiednio: H(7), I(8), J(9), K(10)
if len(df.columns) < 11:
    st.error("🚨 Brak wymaganych kolumn w pliku. Oczekiwano kolumn od A do K (min. 11 kolumn).")
    st.stop()

val_old = df.columns[7]
qty_old = df.columns[8]
val_new = df.columns[9]
qty_new = df.columns[10]

# Konwersja na liczby z zachowaniem dokładności z Excela (wymuszone zaokrąglenie)
for c in [val_old, val_new]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).round(2)
for c in [qty_old, qty_new]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).round(2)

# ================= COLUMNS =================
col_customer = "Customer Name"
col_country = "Country"
col_vat = "Vat ID Nr."
col_code = "Art. Nr."
col_desc = "Article description"
col_brand = "Brand Name"
col_cat = "Category"

# ================= COUNTRY FILTER =================
countries = ["All Countries"] + sorted(df[col_country].dropna().unique())
selected_country = st.selectbox("🌍 Select Country", countries)

if selected_country != "All Countries":
    df = df[df[col_country] == selected_country]

# ================= CATEGORY =================
ALLOWED_CATEGORIES = [
    "Napkins","Hats","Banner","Straws","Bags","Plates","Paper Cups",
    "Tablecover","Reusable","Foil","Wooden","Candles","Latex",
    "Invitations","Articles","Masks","Pinata","Plastic Cups"
]

df["Category Clean"] = df[col_cat].fillna("").apply(normalize_category)
df = df[df["Category Clean"].isin(ALLOWED_CATEGORIES)]

df_original_all = df.copy()

# ================= CUSTOMER FILTER =================
customers = ["All Customers"] + sorted(df[col_customer].dropna().unique())
selected_customer = st.selectbox("👤 Select Customer", customers)

if selected_customer != "All Customers":
    df = df[df[col_customer] == selected_customer]

df_context = df_original_all if selected_customer == "All Customers" else df.copy()

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

# ================= CATEGORY SELECT =================
categories = ["All Categories"] + sorted(df["Category Clean"].unique())
selected = st.selectbox("📂 Select Category", categories)

if selected != "All Categories":
    df = df[df["Category Clean"] == selected]

df = df[df[col_desc].notna()]
df = df[df[col_desc].str.lower() != "none"]

st.divider()

# ================= KPI =================
st.markdown(f"## 💰 KPI (EUR / PCS)")

s_old, s_new = df[val_old].sum(), df[val_new].sum()
q_old, q_new = df[qty_old].sum(), df[qty_new].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Sales {val_old}", f"{s_old:,.2f}")
c2.metric(f"Sales {val_new}", f"{s_new:,.2f}", yoy_label(calc_yoy_clean(s_new, s_old)))
c3.metric(f"Qty {qty_old}", f"{q_old:,.0f}")
c4.metric(f"Qty {qty_new}", f"{q_new:,.0f}", yoy_label(calc_yoy_clean(q_new, q_old)))

# ================= CATEGORY PERFORMANCE =================
if selected == "All Categories":
    st.markdown("## 📊 Category Performance")

    cat_perf = df_context.groupby("Category Clean").agg({
        val_old: "sum",
        val_new: "sum"
    }).reset_index()

    total_old = cat_perf[val_old].sum()
    total_new = cat_perf[val_new].sum()

    if total_old == 0 or total_new == 0:
        st.warning("No data for category performance")
    else:
        cat_perf[f"Share {val_old} %"] = cat_perf[val_old] / total_old * 100
        cat_perf[f"Share {val_new} %"] = cat_perf[val_new] / total_new * 100

        cat_perf["YoY"] = cat_perf.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
        cat_perf["YoY %"] = cat_perf["YoY"].apply(yoy_label)

        cat_perf[f"Share {val_old} %"] = cat_perf[f"Share {val_old} %"].map(lambda x: f"{x:.1f}%")
        cat_perf[f"Share {val_new} %"] = cat_perf[f"Share {val_new} %"].map(lambda x: f"{x:.1f}%")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"### {val_old}")
            st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val_old))

        with c2:
            st.markdown(f"### {val_new}")
            st.plotly_chart(px.pie(cat_perf, names="Category Clean", values=val_new))

        st.markdown("### Category Comparison")
        st.dataframe(add_index(
            cat_perf.sort_values(val_new, ascending=False)[[
                "Category Clean",
                val_old, f"Share {val_old} %",
                val_new, f"Share {val_new} %",
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
total_old = brand[val_old].sum()
total_new = brand[val_new].sum()

brand[f"Share {val_old} %"] = brand[val_old] / total_old * 100 if total_old > 0 else 0
brand[f"Share {val_new} %"] = brand[val_new] / total_new * 100 if total_new > 0 else 0

# 🔥 YoY
brand["YoY"] = brand.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
brand["YoY %"] = brand["YoY"].apply(yoy_label)

# 🔥 format %
brand[f"Share {val_old} %"] = brand[f"Share {val_old} %"].map(lambda x: f"{x:.1f}%")
brand[f"Share {val_new} %"] = brand[f"Share {val_new} %"].map(lambda x: f"{x:.1f}%")

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"### {val_old}")
    st.plotly_chart(px.pie(brand, names=col_brand, values=val_old))

with c2:
    st.markdown(f"### {val_new}")
    st.plotly_chart(px.pie(brand, names=col_brand, values=val_new))

st.dataframe(add_index(
    brand[[
        col_brand,
        val_old, f"Share {val_old} %",
        val_new, f"Share {val_new} %",
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

    # ================= OLD YEAR =================
    with c1:
        st.write(f"### {val_old}")

    base_df = df_context.copy()

    d_old = base_df.groupby(col_code).agg({
        col_desc: "first",
        val_old: "sum",
        qty_old: "sum"
    }).reset_index()

    d_old = d_old[d_old[val_old] > 0]
    d_old = d_old.sort_values(val_old, ascending=False)
    top_old = d_old.head(10)

        # 🔥 tylko SKU ze sprzedażą
        d_old = d_old[d_old[val_old] > 0]

        if d_old.empty:
            st.info(f"No sales in {val_old}")
        else:
            top_old = d_old.sort_values(val_old, ascending=False).head(10)

            total_old = d_old[val_old].sum()
            top_old_sum = top_old[val_old].sum()

            # 🔥 udział %
            top_old["Share %"] = top_old[val_old] / total_old * 100

            st.dataframe(add_index(
                top_old[[col_code, col_desc, val_old, qty_old, "Share %"]]
            ))

            st.write(f"Top 10 share: {(top_old_sum/total_old*100):.1f}%")


    # ================= NEW YEAR =================
    with c2:
        st.write(f"### {val_new}")

        d_new = df.groupby([col_code, col_desc]).agg({
            val_new: "sum",
            qty_new: "sum"
        }).reset_index()

        # 🔥 tylko SKU ze sprzedażą
        d_new = d_new[d_new[val_new] > 0]

        if d_new.empty:
            st.info(f"No sales in {val_new}")
        else:
            top_new = d_new.sort_values(val_new, ascending=False).head(10)

            total_new = d_new[val_new].sum()
            top_new_sum = top_new[val_new].sum()

            # 🔥 udział %
            top_new["Share %"] = top_new[val_new] / total_new * 100

            st.dataframe(add_index(
                top_new[[col_code, col_desc, val_new, qty_new, "Share %"]]
            ))

            st.write(f"Top 10 share: {(top_new_sum/total_new*100):.1f}%")

st.divider()

# ================= PARETO =================
st.markdown("## 📊 Pareto Analysis")

tab1, tab2 = st.tabs([val_old, val_new])

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
            st.info("No sales in this period")
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

tab1, tab2 = st.tabs([val_old, val_new])

for year, val in zip([tab1, tab2], [val_old, val_new]):
    with year:
        a = df.groupby([col_code, col_desc]).agg({
            val_old:"sum",
            val_new:"sum"
        }).reset_index()

        # 🔥 usuwamy zerowe SKU
        a = a[a[val] > 0]

        a = a.sort_values(val, ascending=False)
        a["cum"] = a[val].cumsum() / a[val].sum()

        a["segment"] = "C"
        a.loc[a["cum"] <= 0.7, "segment"] = "A"
        a.loc[(a["cum"] > 0.7) & (a["cum"] <= 0.9), "segment"] = "B"

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

df_yoy["YoY %"] = df_yoy.apply(lambda x: yoy_label(calc_yoy_clean(x[val_new], x[val_old])), axis=1)

st.dataframe(add_index(
    df_yoy.sort_values(val_new, ascending=False)
    [[col_code, col_desc, val_old, val_new, qty_old, qty_new, "YoY %"]]
))

st.divider()

# ================= AUTO INSIGHTS =================
st.markdown("## 🧠 Auto Insights")

cat = df_context.groupby("Category Clean").agg({
    val_old: "sum",
    val_new: "sum"
}).reset_index()

cat["YoY"] = cat.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
cat["YoY %"] = cat["YoY"].apply(yoy_label)

# ================= TOP 3 =================
st.write("### Top 5 Categories")

c1, c2 = st.columns(2)

with c1:
    st.write(f"#### {val_old}")
    top_old_cat = cat.sort_values(val_old, ascending=False).head(5)
    st.dataframe(add_index(top_old_cat[["Category Clean", val_old]]))

with c2:
    st.write(f"#### {val_new}")
    top_new_cat = cat.sort_values(val_new, ascending=False).head(5)
    st.dataframe(add_index(top_new_cat[["Category Clean", val_new, "YoY %"]]))

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

# 🔥 wybór brandu
all_brands = sorted(df_original_all[col_brand].dropna().unique())
selected_brand_impact = st.selectbox(
    "Select Brand (License)",
    ["All Brands"] + all_brands
)

# ================= DATA PREP =================
df_impact = df_original_all.copy()

# 🔥 filtr kategorii
if selected_cat_impact != "All Categories":
    df_impact = df_impact[df_impact["Category Clean"] == selected_cat_impact]

# 🔥 filtr brandu
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
