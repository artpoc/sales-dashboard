import streamlit as st
import pandas as pd
import plotly.express as px
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ================= HELPERS & FUNCTIONS =================
def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1  # numerowanie od 1
    # Formatowanie wyświetlane: jeśli kolumna jest Decimal, zamieniamy na string z 2 miejscami
    for col in df.columns:
        if df[col].dtype == object and df[col].apply(lambda x: isinstance(x, Decimal)).any():
            df[col] = df[col].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}" if isinstance(x, Decimal) else x)
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].map(lambda x: f"{x:,.2f}" if pd.notna(x) else x)
    return df

def to_decimal(x):
    # Konwersja wartości z excela do Decimal, zachowując znaki ujemne i przecinki
    if pd.isna(x):
        return Decimal('0')
    if isinstance(x, Decimal):
        return x
    try:
        s = str(x).strip()
        # usuń spacje tysięczne
        s = s.replace(" ", "")
        # zamień przecinek na kropkę
        s = s.replace(",", ".")
        # pusty string -> 0
        if s == "":
            return Decimal('0')
        return Decimal(s)
    except (InvalidOperation, Exception):
        return Decimal('0')

def calc_yoy_clean(new, old):
    # new i old mogą być Decimal
    try:
        if old < 0 and new == 0:
            return None
        if old == 0:
            return Decimal('100') if new > 0 else Decimal('0')
        if old > 0 and new == 0:
            return Decimal('-100')
        return (new - old) / (abs(old)) * Decimal('100')
    except Exception:
        return None

def yoy_label(val, special=False):
    if special:
        return "Recovery to 0 ⚠️"
    if val is None:
        return "0%"
    try:
        # val może być Decimal
        v = float(val)
    except:
        return "0%"
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

def decimal_sum(series):
    # sumowanie serii zawierającej Decimal (dtype object)
    try:
        return sum(series.tolist(), Decimal('0'))
    except Exception:
        # fallback
        return Decimal(str(series.sum()))

def format_decimal_for_metric(d):
    # format Decimal do string z 2 miejscami i separatorem tysięcy
    if not isinstance(d, Decimal):
        try:
            d = Decimal(str(d))
        except:
            d = Decimal('0')
    q = d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    # format z separatorem tysięcy (używamy python format, ale Decimal -> float może być ok do formatowania)
    return f"{q:,}"

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

# Wczytujemy plik RAZ, jako object, żeby zachować oryginalne reprezentacje
df = pd.read_excel(file, engine='openpyxl', dtype=object)
df.columns = df.columns.str.strip()

# Bez wielokrotnego wczytywania — wykrycie kolumn dynamicznych
if len(df.columns) < 11:
    st.error("🚨 Brak wymaganych kolumn w pliku. Oczekiwano kolumn od A do K (min. 11 kolumn).")
    st.stop()

# kolumny dynamiczne (indeksy 7..10 odpowiadają H..K)
val_old = df.columns[7]
qty_old = df.columns[8]
val_new = df.columns[9]
qty_new = df.columns[10]

# ================= COLUMNS (stałe nazwy) =================
col_customer = "Customer Name"
col_country = "Country"
col_vat = "Vat ID Nr."
col_code = "Art. Nr."
col_desc = "Article description"
col_brand = "Brand Name"
col_cat = "Category"

# ================= CLEAN NUMERIC COLUMNS -> Decimal =================
# Konwertujemy tylko wymagane kolumny do Decimal (dtype object)
for c in [val_old, val_new, qty_old, qty_new]:
    if c in df.columns:
        df[c] = df[c].apply(to_decimal)
    else:
        # jeśli kolumna nie istnieje, dodajemy z zerami
        df[c] = Decimal('0')

# ================= COLUMNS NORMALIZATION =================
# Upewniamy się, że kolumny tekstowe są stringami
for c in [col_customer, col_country, col_vat, col_code, col_desc, col_brand, col_cat]:
    if c in df.columns:
        df[c] = df[c].astype(str).fillna("").replace("nan", "")
    else:
        df[c] = ""

# ================= COUNTRY FILTER =================
countries = ["All Countries"] + sorted(df[col_country].replace("", pd.NA).dropna().unique())
selected_country = st.selectbox("🌍 Select Country", countries)

if selected_country != "All Countries":
    df = df[df[col_country] == selected_country]

# ================= CATEGORY CLEAN & FILTER =================
ALLOWED_CATEGORIES = [
    "Napkins","Hats","Banner","Straws","Bags","Plates","Paper Cups",
    "Tablecover","Reusable","Foil","Wooden","Candles","Latex",
    "Invitations","Articles","Masks","Pinata","Plastic Cups"
]

df["Category Clean"] = df[col_cat].apply(lambda x: normalize_category(x))
df = df[df["Category Clean"].isin(ALLOWED_CATEGORIES)]

df_original_all = df.copy()

# ================= CUSTOMER FILTER =================
customers = ["All Customers"] + sorted(df[col_customer].replace("", pd.NA).dropna().unique())
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
    # zabezpieczenie na wypadek pustych df
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.write(f"**Customer:** {df[col_customer].iloc[0]}")
        c2.write(f"**Country:** {df[col_country].iloc[0]}")
        c3.write(f"**VAT:** {df[col_vat].iloc[0]}")
    else:
        st.write("Brak danych dla wybranego klienta")

# ================= CATEGORY SELECT =================
categories = ["All Categories"] + sorted(df["Category Clean"].dropna().unique())
selected = st.selectbox("📂 Select Category", categories)

if selected != "All Categories":
    df = df[df["Category Clean"] == selected]

df = df[df[col_desc].notna()]
df = df[df[col_desc].str.lower() != "none"]

st.divider()

# ================= KPI =================
st.markdown(f"## 💰 KPI (EUR / PCS)")

# Suma przy użyciu Decimal
s_old = decimal_sum(df[val_old])
s_new = decimal_sum(df[val_new])
q_old = decimal_sum(df[qty_old])
q_new = decimal_sum(df[qty_new])

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Sales {val_old}", format_decimal_for_metric(s_old))
c2.metric(f"Sales {val_new}", format_decimal_for_metric(s_new), yoy_label(calc_yoy_clean(s_new, s_old)))
c3.metric(f"Qty {qty_old}", f"{q_old:.0f}" if isinstance(q_old, Decimal) else f"{q_old:,.0f}")
c4.metric(f"Qty {qty_new}", f"{q_new:.0f}" if isinstance(q_new, Decimal) else f"{q_new:,.0f}", yoy_label(calc_yoy_clean(q_new, q_old)))

# ================= CATEGORY PERFORMANCE =================
if selected == "All Categories":
    st.markdown("## 📊 Category Performance")

    # agregacja na df_context (czyli bez filtra category jeśli All Categories)
    cat_perf = df_context.groupby("Category Clean").agg({
        val_old: lambda s: decimal_sum(s),
        val_new: lambda s: decimal_sum(s)
    }).reset_index()

    total_old = decimal_sum(cat_perf[val_old])
    total_new = decimal_sum(cat_perf[val_new])

    if total_old == 0 or total_new == 0:
        st.warning("No data for category performance")
    else:
        # obliczenia udziałów jako Decimal -> konwersja do float tylko do wykresu
        cat_perf[f"Share {val_old} %"] = cat_perf[val_old].apply(lambda x: (x / total_old * Decimal('100')) if total_old != 0 else Decimal('0'))
        cat_perf[f"Share {val_new} %"] = cat_perf[val_new].apply(lambda x: (x / total_new * Decimal('100')) if total_new != 0 else Decimal('0'))

        cat_perf["YoY"] = cat_perf.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
        cat_perf["YoY %"] = cat_perf["YoY"].apply(yoy_label)

        # przygotowanie do wykresu: konwersja wartości na float (plotly wymaga numeric)
        cat_perf_plot_old = cat_perf.copy()
        cat_perf_plot_old[val_old] = cat_perf_plot_old[val_old].apply(lambda x: float(x))
        cat_perf_plot_new = cat_perf.copy()
        cat_perf_plot_new[val_new] = cat_perf_plot_new[val_new].apply(lambda x: float(x))

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"### {val_old}")
            st.plotly_chart(px.pie(cat_perf_plot_old, names="Category Clean", values=val_old))

        with c2:
            st.markdown(f"### {val_new}")
            st.plotly_chart(px.pie(cat_perf_plot_new, names="Category Clean", values=val_new))

        st.markdown("### Category Comparison")
        display_df = cat_perf.sort_values(val_new, ascending=False)[[
            "Category Clean",
            val_old, f"Share {val_old} %",
            val_new, f"Share {val_new} %",
            "YoY %"
        ]].copy()

        # formatowanie udziałów i wartości do czytelnego widoku
        display_df[val_old] = display_df[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
        display_df[val_new] = display_df[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
        display_df[f"Share {val_old} %"] = display_df[f"Share {val_old} %"].apply(lambda x: f"{x.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%")
        display_df[f"Share {val_new} %"] = display_df[f"Share {val_new} %"].apply(lambda x: f"{x.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%")

        st.dataframe(add_index(display_df))

    st.divider()

# ================= BRAND PERFORMANCE =================
st.markdown("## 🏷️ Brand Performance")

# Używamy aktualnego df (już przefiltrowanego)
brand = df.groupby(col_brand).agg({
    val_old: lambda s: decimal_sum(s),
    val_new: lambda s: decimal_sum(s)
}).reset_index()

total_old = decimal_sum(brand[val_old])
total_new = decimal_sum(brand[val_new])

brand[f"Share {val_old} %"] = brand[val_old].apply(lambda x: (x / total_old * Decimal('100')) if total_old != 0 else Decimal('0'))
brand[f"Share {val_new} %"] = brand[val_new].apply(lambda x: (x / total_new * Decimal('100')) if total_new != 0 else Decimal('0'))

brand["YoY"] = brand.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
brand["YoY %"] = brand["YoY"].apply(yoy_label)

# wykresy wymagają float
brand_plot_old = brand.copy()
brand_plot_old[val_old] = brand_plot_old[val_old].apply(lambda x: float(x))
brand_plot_new = brand.copy()
brand_plot_new[val_new] = brand_plot_new[val_new].apply(lambda x: float(x))

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"### {val_old}")
    st.plotly_chart(px.pie(brand_plot_old, names=col_brand, values=val_old))

with c2:
    st.markdown(f"### {val_new}")
    st.plotly_chart(px.pie(brand_plot_new, names=col_brand, values=val_new))

# przygotowanie tabeli do wyświetlenia
brand_display = brand.copy()
brand_display[val_old] = brand_display[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
brand_display[val_new] = brand_display[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
brand_display[f"Share {val_old} %"] = brand_display[f"Share {val_old} %"].apply(lambda x: f"{x.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%")
brand_display[f"Share {val_new} %"] = brand_display[f"Share {val_new} %"].apply(lambda x: f"{x.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%")

st.dataframe(add_index(
    brand_display[[
        col_brand,
        val_old, f"Share {val_old} %",
        val_new, f"Share {val_new} %",
        "YoY %"
    ]].sort_values(by=val_new, ascending=False)
))

st.divider()

# ================= TOP PRODUCTS =================
st.markdown("## 🏆 Top Products")

if df.empty:
    st.warning("No data available for selected filters")
else:
    base_df = df.copy()
    c1, c2 = st.columns(2)

    # ================= OLD YEAR =================
    with c1:
        st.write(f"### {val_old}")

        d_old = base_df.groupby(col_code).agg({
            col_desc: "first",
            val_old: lambda s: decimal_sum(s),
            qty_old: lambda s: decimal_sum(s)
        }).reset_index()

        d_old = d_old[d_old[val_old] > 0]

        if d_old.empty:
            st.info(f"No sales in {val_old}")
        else:
            d_old = d_old.sort_values(val_old, ascending=False)
            top_old = d_old.head(10)

            total_old = decimal_sum(d_old[val_old])
            top_old["Share %"] = top_old[val_old].apply(lambda x: (x / total_old * Decimal('100')) if total_old != 0 else Decimal('0'))

            # formatowanie
            top_old_display = top_old.copy()
            top_old_display[val_old] = top_old_display[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
            top_old_display[qty_old] = top_old_display[qty_old].apply(lambda x: f"{int(x)}" if isinstance(x, Decimal) else x)
            top_old_display["Share %"] = top_old_display["Share %"].apply(lambda x: f"{x.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%")

            st.dataframe(add_index(
                top_old_display[[col_code, col_desc, val_old, qty_old, "Share %"]]
            ))

            st.write(f"Top 10 share: {(decimal_sum(top_old[val_old]) / total_old * Decimal('100')):.1f}%")

    # ================= NEW YEAR =================
    with c2:
        st.write(f"### {val_new}")

        d_new = base_df.groupby(col_code).agg({
            col_desc: "first",
            val_new: lambda s: decimal_sum(s),
            qty_new: lambda s: decimal_sum(s)
        }).reset_index()

        d_new = d_new[d_new[val_new] > 0]

        if d_new.empty:
            st.info(f"No sales in {val_new}")
        else:
            d_new = d_new.sort_values(val_new, ascending=False)
            top_new = d_new.head(10)

            total_new = decimal_sum(d_new[val_new])
            top_new["Share %"] = top_new[val_new].apply(lambda x: (x / total_new * Decimal('100')) if total_new != 0 else Decimal('0'))

            top_new_display = top_new.copy()
            top_new_display[val_new] = top_new_display[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
            top_new_display[qty_new] = top_new_display[qty_new].apply(lambda x: f"{int(x)}" if isinstance(x, Decimal) else x)
            top_new_display["Share %"] = top_new_display["Share %"].apply(lambda x: f"{x.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%")

            st.dataframe(add_index(
                top_new_display[[col_code, col_desc, val_new, qty_new, "Share %"]]
            ))

            st.write(f"Top 10 share: {(decimal_sum(top_new[val_new]) / total_new * Decimal('100')):.1f}%")

st.divider()

# ================= PARETO =================
st.markdown("## 📊 Pareto Analysis")

tab1, tab2 = st.tabs([val_old, val_new])

for year, val in zip([tab1, tab2], [val_old, val_new]):
    with year:
        # agregacja do poziomu SKU (unikalny Art. Nr.)
        p = df.groupby(col_code).agg({
            col_desc: "first",
            "Category Clean": "first",
            val: lambda s: decimal_sum(s)
        }).reset_index()

        p = p[p[val] > 0]

        if p.empty:
            st.info("No sales in this period")
        else:
            p = p.sort_values(val, ascending=False)
            p["cum_value"] = p[val].cumsum()  # cumsum działa na obiektach Decimal w pandas jeśli dtype object
            total_value = decimal_sum(p[val])
            # zabezpieczenie przed dzieleniem przez zero
            if total_value == 0:
                st.info("Total value is zero")
                continue
            p["cum_share"] = p["cum_value"].apply(lambda x: (x / total_value) if isinstance(x, Decimal) else Decimal(str(x)) / total_value)

            top80 = p[p["cum_share"] <= Decimal('0.8')]

            total_sku = p[col_code].nunique()
            pareto_sku = top80[col_code].nunique()
            sku_share = (Decimal(pareto_sku) / Decimal(total_sku) * Decimal('100')) if total_sku > 0 else Decimal('0')

            st.write(f"Top SKU for 80%: {pareto_sku} / {total_sku} ({sku_share:.1f}% of SKU)")

            # formatowanie do wyświetlenia
            p_display = top80[[col_code, col_desc, "Category Clean", val]].copy()
            p_display[val] = p_display[val].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")

            st.dataframe(add_index(p_display))

st.divider()

# ================= ABC =================
st.markdown("## 📊 ABC Analysis")

tab1, tab2 = st.tabs([val_old, val_new])

for year, val in zip([tab1, tab2], [val_old, val_new]):
    with year:
        # agregujemy obie kolumny, oraz col_desc
        a = df.groupby(col_code).agg({
            col_desc: "first",
            val_old: lambda s: decimal_sum(s),
            val_new: lambda s: decimal_sum(s)
        }).reset_index()

        # usuwamy zerowe SKU dla analizowanego val
        a = a[a[val] > 0]

        if a.empty:
            st.info("No sales in this period")
        else:
            a = a.sort_values(val, ascending=False).reset_index(drop=True)
            total_val = decimal_sum(a[val])
            if total_val == 0:
                st.info("Total is zero")
                continue
            # kumulacja jako Decimal
            a["cum"] = a[val].cumsum().apply(lambda x: x / total_val)
            a["segment"] = "C"
            a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
            a.loc[(a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')), "segment"] = "B"

            seg_counts = a["segment"].value_counts()

            st.write(f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}")

            a_display = a[[col_code, col_desc, val, "segment"]].copy()
            a_display[val] = a_display[val].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")

            st.dataframe(add_index(a_display))

st.divider()

# ================= YOY =================
st.markdown("## 📈 L4L Analysis")

df_yoy = df.groupby(col_code).agg({
    col_desc: "first",
    val_old: lambda s: decimal_sum(s),
    val_new: lambda s: decimal_sum(s),
    qty_old: lambda s: decimal_sum(s),
    qty_new: lambda s: decimal_sum(s)
}).reset_index()

df_yoy["YoY %"] = df_yoy.apply(lambda x: yoy_label(calc_yoy_clean(x[val_new], x[val_old])), axis=1)

# formatowanie wartości do wyświetlenia
df_yoy_display = df_yoy.copy()
for c in [val_old, val_new]:
    df_yoy_display[c] = df_yoy_display[c].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
for c in [qty_old, qty_new]:
    df_yoy_display[c] = df_yoy_display[c].apply(lambda x: f"{int(x)}" if isinstance(x, Decimal) else x)

st.dataframe(add_index(
    df_yoy_display.sort_values(val_new, ascending=False)[[col_code, col_desc, val_old, val_new, qty_old, qty_new, "YoY %"]]
))

st.divider()

# ================= AUTO INSIGHTS =================
st.markdown("## 🧠 Auto Insights")

cat = df_context.groupby("Category Clean").agg({
    val_old: lambda s: decimal_sum(s),
    val_new: lambda s: decimal_sum(s)
}).reset_index()

cat["YoY"] = cat.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
cat["YoY %"] = cat["YoY"].apply(yoy_label)

# ================= TOP 5 =================
st.write("### Top 5 Categories")

c1, c2 = st.columns(2)

with c1:
    st.write(f"#### {val_old}")
    top_old_cat = cat.sort_values(val_old, ascending=False).head(5)
    top_old_cat_display = top_old_cat.copy()
    top_old_cat_display[val_old] = top_old_cat_display[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    st.dataframe(add_index(top_old_cat_display[["Category Clean", val_old]]))

with c2:
    st.write(f"#### {val_new}")
    top_new_cat = cat.sort_values(val_new, ascending=False).head(5)
    top_new_cat_display = top_new_cat.copy()
    top_new_cat_display[val_new] = top_new_cat_display[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    st.dataframe(add_index(top_new_cat_display[["Category Clean", val_new, "YoY %"]]))

# ================= GROWTH =================
st.write("### Growth (L4L)")

growth = cat[cat["YoY"] > 0].sort_values("YoY", ascending=False).head(5)

if growth.empty:
    st.info("There is no growth in categories")
else:
    growth_display = growth.copy()
    growth_display[val_old] = growth_display[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    growth_display[val_new] = growth_display[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    st.dataframe(add_index(growth_display[["Category Clean", val_old, val_new, "YoY %"]]))

# ================= RISK =================
st.write("### Risk")

risk = cat[cat["YoY"] < 0].sort_values("YoY").head(5)

if risk.empty:
    st.success("There is no risk in categories")
else:
    risk_display = risk.copy()
    risk_display[val_old] = risk_display[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    risk_display[val_new] = risk_display[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    st.dataframe(add_index(risk_display[["Category Clean", val_old, val_new, "YoY %"]]))

st.divider()

# ================= CUSTOMER IMPACT =================
st.markdown("## 👥 Customer Impact (Growth vs Decline)")

all_categories = sorted(df_original_all["Category Clean"].dropna().unique())
selected_cat_impact = st.selectbox(
    "Select Category for Impact Analysis",
    ["All Categories"] + all_categories
)

all_brands = sorted(df_original_all[col_brand].dropna().unique())
selected_brand_impact = st.selectbox(
    "Select Brand (License)",
    ["All Brands"] + all_brands
)

df_impact = df_original_all.copy()

if selected_cat_impact != "All Categories":
    df_impact = df_impact[df_impact["Category Clean"] == selected_cat_impact]

if selected_brand_impact != "All Brands":
    df_impact = df_impact[df_impact[col_brand] == selected_brand_impact]

impact = df_impact.groupby(col_customer).agg({
    val_old: lambda s: decimal_sum(s),
    val_new: lambda s: decimal_sum(s)
}).reset_index()

impact = impact[(impact[val_old] != 0) | (impact[val_new] != 0)]

impact["Change Value"] = impact[val_new] - impact[val_old]
impact["Special Case"] = ((impact[val_old] < 0) & (impact[val_new] == 0))
impact["YoY"] = impact.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
impact["YoY %"] = impact.apply(lambda x: yoy_label(x["YoY"], x["Special Case"]), axis=1)

st.write("### 🟢 Top Growth Drivers")

growth = impact[(impact["Change Value"] > 0) & (~impact["Special Case"])].sort_values("Change Value", ascending=False).head(10)
growth_special = impact[impact["Special Case"]].head(10)
growth = pd.concat([growth, growth_special])

if growth.empty:
    st.info("No growth generated by customers")
else:
    growth_display = growth.copy()
    growth_display[val_old] = growth_display[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    growth_display[val_new] = growth_display[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    growth_display["Change Value"] = growth_display["Change Value"].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    st.dataframe(add_index(growth_display[[col_customer, val_old, val_new, "Change Value", "YoY %"]]))

st.write("### 🔴 Top Decline Drivers")

decline = impact[(impact["Change Value"] < 0)].sort_values("Change Value").head(10)
decline_special = impact[impact["Special Case"]].head(10)
decline = pd.concat([decline, decline_special])

if decline.empty:
    st.success("No decline across customers")
else:
    decline_display = decline.copy()
    decline_display[val_old] = decline_display[val_old].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    decline_display[val_new] = decline_display[val_new].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    decline_display["Change Value"] = decline_display["Change Value"].apply(lambda x: f"{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,}")
    st.dataframe(add_index(decline_display[[col_customer, val_old, val_new, "Change Value", "YoY %"]]))
