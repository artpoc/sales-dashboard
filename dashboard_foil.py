import streamlit as st
import pandas as pd
import plotly.express as px
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ================= HELPERS & FUNCTIONS =================
def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

def to_decimal(x):
    """Konwertuje wartość na Decimal zachowując dokładność.
    Obsługuje: None/NaN, int, float, str (z przecinkami i spacjami).
    """
    if pd.isna(x):
        return Decimal('0')
    if isinstance(x, Decimal):
        return x
    try:
        if isinstance(x, int):
            return Decimal(x)
        if isinstance(x, float):
            # konwersja przez str aby zachować widoczną wartość
            return Decimal(str(x))
        s = str(x).strip()
        s = s.replace(" ", "")
        s = s.replace(",", ".")
        if s == "":
            return Decimal('0')
        return Decimal(s)
    except (InvalidOperation, Exception):
        return Decimal('0')

def decimal_sum(series):
    try:
        return sum(series.tolist(), Decimal('0'))
    except Exception:
        return Decimal(str(series.sum()))

def calc_yoy_clean(new, old):
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

def format_no_decimals(d):
    """Format Decimal as integer string with thousands separator, no decimals."""
    if not isinstance(d, Decimal):
        try:
            d = Decimal(str(d))
        except:
            d = Decimal('0')
    q = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return f"{int(q):,}"

def sort_by_col_desc(df, col):
    """Sort descending by col if present; handle Decimal objects."""
    if col in df.columns:
        try:
            return df.sort_values(by=col, ascending=False)
        except Exception:
            tmp = df.copy()
            tmp[col] = tmp[col].apply(lambda x: float(x) if isinstance(x, Decimal) else float(Decimal(str(x))))
            return tmp.sort_values(by=col, ascending=False)
    return df

# ================= CONFIG & UI =================
st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha")

# ================= FILE UPLOAD =================
col1, col2 = st.columns(2)
with col1:
    file_l4l = st.file_uploader("📂 Upload L4L (2025 vs 2026)", type=["xlsx"])
with col2:
    file_full = st.file_uploader("📂 Upload Full Year (2024 vs 2025)", type=["xlsx"])

mode = st.radio("Select Analysis Mode", ["L4L (2025 vs 2026)", "Full Year (2024 vs 2025)"])
file = file_l4l if mode == "L4L (2025 vs 2026)" else file_full

if file is None:
    st.warning("⬆️ Upload file for selected mode")
    st.stop()

# ================= LOAD ONCE (read as object to preserve formatting) =================
df_raw = pd.read_excel(file, dtype=object, engine='openpyxl')
df_raw.columns = df_raw.columns.str.strip()

if len(df_raw.columns) < 11:
    st.error("🚨 Brak wymaganych kolumn w pliku. Oczekiwano kolumn od A do K (min. 11 kolumn).")
    st.stop()

# dynamic columns H..K -> indices 7..10
val_old = df_raw.columns[7]
qty_old = df_raw.columns[8]
val_new = df_raw.columns[9]
qty_new = df_raw.columns[10]

# expected textual columns
col_customer = "Customer Name"
col_country = "Country"
col_vat = "Vat ID Nr."
col_code = "Art. Nr."
col_desc = "Article description"
col_brand = "Brand Name"
col_cat = "Category"

# work copy
df = df_raw.copy()

# convert numeric columns to Decimal
for c in [val_old, val_new, qty_old, qty_new]:
    if c in df.columns:
        df[c] = df[c].apply(to_decimal)
    else:
        df[c] = Decimal('0')

# ensure text columns exist and are strings
for c in [col_customer, col_country, col_vat, col_code, col_desc, col_brand, col_cat]:
    if c in df.columns:
        df[c] = df[c].astype(str).fillna("").replace("nan", "")
    else:
        df[c] = ""

# Keep original totals (before any UI filters) to match Excel when no filters applied
df_original_all = df.copy()

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

# keep copy after category filtering for category-specific views
df_after_category = df.copy()

# ================= CUSTOMER FILTER =================
customers = ["All Customers"] + sorted(df[col_customer].replace("", pd.NA).dropna().unique())
selected_customer = st.selectbox("👤 Select Customer", customers)
if selected_customer != "All Customers":
    df = df[df[col_customer] == selected_customer]

# df_context: dataset used for category-agnostic analyses (respects country & customer filters)
df_context = df_after_category.copy() if selected_customer == "All Customers" else df.copy()

# ================= CUSTOMER INFO =================
st.subheader("👤 Customer Information")
if selected_customer == "All Customers":
    st.write("**Customer:** All Customers")
    st.write(f"**Total Clients:** {df_original_all[col_customer].nunique()}")
else:
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

# Use original totals only when no filters applied; otherwise use current filtered df
use_df_for_kpi = df if (selected != "All Categories" or selected_customer != "All Customers" or selected_country != "All Countries") else df_original_all

s_old = decimal_sum(use_df_for_kpi[val_old])
s_new = decimal_sum(use_df_for_kpi[val_new])
q_old = decimal_sum(use_df_for_kpi[qty_old])
q_new = decimal_sum(use_df_for_kpi[qty_new])

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Sales {val_old}", format_no_decimals(s_old))
c2.metric(f"Sales {val_new}", format_no_decimals(s_new), yoy_label(calc_yoy_clean(s_new, s_old)))
c3.metric(f"Qty {qty_old}", format_no_decimals(q_old))
c4.metric(f"Qty {qty_new}", format_no_decimals(q_new), yoy_label(calc_yoy_clean(q_new, q_old)))

# ================= CATEGORY PERFORMANCE =================
if selected == "All Categories":
    st.markdown("## 📊 Category Performance")

    cat_perf = df_context.groupby("Category Clean").agg({
        val_old: lambda s: decimal_sum(s),
        val_new: lambda s: decimal_sum(s)
    }).reset_index()

    # Combined table -> sort by newest year (val_new) descending
    cat_perf = sort_by_col_desc(cat_perf, val_new)

    total_old = decimal_sum(cat_perf[val_old])
    total_new = decimal_sum(cat_perf[val_new])

    if total_old == 0 and total_new == 0:
        st.warning("No data for category performance")
    else:
        cat_perf[f"Share {val_old} %"] = cat_perf[val_old].apply(lambda x: (x / total_old * Decimal('100')) if total_old != 0 else Decimal('0'))
        cat_perf[f"Share {val_new} %"] = cat_perf[val_new].apply(lambda x: (x / total_new * Decimal('100')) if total_new != 0 else Decimal('0'))

        cat_perf["YoY"] = cat_perf.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
        cat_perf["YoY %"] = cat_perf["YoY"].apply(yoy_label)

        # plotly needs floats
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

        display_df[val_old] = display_df[val_old].apply(format_no_decimals)
        display_df[val_new] = display_df[val_new].apply(format_no_decimals)
        display_df[f"Share {val_old} %"] = display_df[f"Share {val_old} %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")
        display_df[f"Share {val_new} %"] = display_df[f"Share {val_new} %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")

        st.dataframe(add_index(display_df))

    st.divider()

# ================= BRAND PERFORMANCE =================
st.markdown("## 🏷️ Brand Performance")

brand = df.groupby(col_brand).agg({
    val_old: lambda s: decimal_sum(s),
    val_new: lambda s: decimal_sum(s)
}).reset_index()

# Combined table -> sort by newest year (val_new)
brand = sort_by_col_desc(brand, val_new)

total_old = decimal_sum(brand[val_old])
total_new = decimal_sum(brand[val_new])

brand[f"Share {val_old} %"] = brand[val_old].apply(lambda x: (x / total_old * Decimal('100')) if total_old != 0 else Decimal('0'))
brand[f"Share {val_new} %"] = brand[val_new].apply(lambda x: (x / total_new * Decimal('100')) if total_new != 0 else Decimal('0'))

brand["YoY"] = brand.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
brand["YoY %"] = brand["YoY"].apply(yoy_label)

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

brand_display = brand.copy()
brand_display[val_old] = brand_display[val_old].apply(format_no_decimals)
brand_display[val_new] = brand_display[val_new].apply(format_no_decimals)
brand_display[f"Share {val_old} %"] = brand_display[f"Share {val_old} %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")
brand_display[f"Share {val_new} %"] = brand_display[f"Share {val_new} %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")

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

    # OLD YEAR panel: sort by val_old (since panel shows old-year values)
    with c1:
        st.write(f"### {val_old}")
        d_old = base_df.groupby(col_code).agg({
            col_desc: "first",
            val_old: lambda s: decimal_sum(s),
            qty_old: lambda s: decimal_sum(s)
        }).reset_index()

        # attach val_new for context but sorting for this panel is by val_old
        d_old = d_old.merge(
            base_df.groupby(col_code).agg({val_new: lambda s: decimal_sum(s)}).reset_index(),
            on=col_code, how="left"
        )
        d_old[val_new] = d_old[val_new].fillna(Decimal('0'))

        d_old = d_old[d_old[val_old] > 0]
        d_old = sort_by_col_desc(d_old, val_old)

        if d_old.empty:
            st.info(f"No sales in {val_old}")
        else:
            top_old = d_old.head(10)
            total_old = decimal_sum(d_old[val_old])
            top_old["Share %"] = top_old[val_old].apply(lambda x: (x / total_old * Decimal('100')) if total_old != 0 else Decimal('0'))

            top_old_display = top_old.copy()
            top_old_display[val_old] = top_old_display[val_old].apply(format_no_decimals)
            top_old_display[qty_old] = top_old_display[qty_old].apply(format_no_decimals)
            top_old_display["Share %"] = top_old_display["Share %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")

            st.dataframe(add_index(top_old_display[[col_code, col_desc, val_old, qty_old, "Share %"]]))
            st.write(f"Top 10 share: {int((decimal_sum(top_old[val_old]) / total_old * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")

    # NEW YEAR panel: sort by val_new
    with c2:
        st.write(f"### {val_new}")
        d_new = base_df.groupby(col_code).agg({
            col_desc: "first",
            val_new: lambda s: decimal_sum(s),
            qty_new: lambda s: decimal_sum(s)
        }).reset_index()

        d_new = d_new[d_new[val_new] > 0]
        d_new = sort_by_col_desc(d_new, val_new)

        if d_new.empty:
            st.info(f"No sales in {val_new}")
        else:
            top_new = d_new.head(10)
            total_new = decimal_sum(d_new[val_new])
            top_new["Share %"] = top_new[val_new].apply(lambda x: (x / total_new * Decimal('100')) if total_new != 0 else Decimal('0'))

            top_new_display = top_new.copy()
            top_new_display[val_new] = top_new_display[val_new].apply(format_no_decimals)
            top_new_display[qty_new] = top_new_display[qty_new].apply(format_no_decimals)
            top_new_display["Share %"] = top_new_display["Share %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")

            st.dataframe(add_index(top_new_display[[col_code, col_desc, val_new, qty_new, "Share %"]]))
            st.write(f"Top 10 share: {int((decimal_sum(top_new[val_new]) / total_new * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")

st.divider()

# ================= PARETO =================
st.markdown("## 📊 Pareto Analysis")

tab1, tab2 = st.tabs([val_old, val_new])
for year, val in zip([tab1, tab2], [val_old, val_new]):
    with year:
        p = df.groupby(col_code).agg({
            col_desc: "first",
            "Category Clean": "first",
            val: lambda s: decimal_sum(s)
        }).reset_index()

        # ensure we have val_new if needed for context
        if val_new in df.columns and val_new not in p.columns:
            p = p.merge(df.groupby(col_code).agg({val_new: lambda s: decimal_sum(s)}).reset_index(), on=col_code, how="left")
            p[val_new] = p[val_new].fillna(Decimal('0'))

        p = p[p[val] > 0]
        if p.empty:
            st.info("No sales in this period")
        else:
            # For per-panel view sort by the panel's val descending
            p = sort_by_col_desc(p, val)

            p["cum_value"] = p[val].cumsum()
            total_value = decimal_sum(p[val])
            if total_value == 0:
                st.info("Total value is zero")
                continue
            p["cum_share"] = p["cum_value"].apply(lambda x: (x / total_value) if isinstance(x, Decimal) else Decimal(str(x)) / total_value)

            top80 = p[p["cum_share"] <= Decimal('0.8')]

            total_sku = p[col_code].nunique()
            pareto_sku = top80[col_code].nunique()
            sku_share = (Decimal(pareto_sku) / Decimal(total_sku) * Decimal('100')) if total_sku > 0 else Decimal('0')

            st.write(f"Top SKU for 80%: {pareto_sku} / {total_sku} ({int(sku_share.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}% of SKU)")

            p_display = top80[[col_code, col_desc, "Category Clean", val]].copy()
            p_display[val] = p_display[val].apply(format_no_decimals)

            st.dataframe(add_index(p_display))

st.divider()

# ================= ABC =================
st.markdown("## 📊 ABC Analysis")

tab1, tab2 = st.tabs([val_old, val_new])
for year, val in zip([tab1, tab2], [val_old, val_new]):
    with year:
        a = df.groupby(col_code).agg({
            col_desc: "first",
            val_old: lambda s: decimal_sum(s),
            val_new: lambda s: decimal_sum(s)
        }).reset_index()

        a = a[a[val] > 0]
        if a.empty:
            st.info("No sales in this period")
        else:
            # per-panel sort by panel's val for ranking
            a = sort_by_col_desc(a, val)
            a = a.sort_values(val, ascending=False).reset_index(drop=True)
            total_val = decimal_sum(a[val])
            if total_val == 0:
                st.info("Total is zero")
                continue
            a["cum"] = a[val].cumsum().apply(lambda x: x / total_val)
            a["segment"] = "C"
            a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
            a.loc[(a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')), "segment"] = "B"

            seg_counts = a["segment"].value_counts()
            st.write(f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}")

            a_display = a[[col_code, col_desc, val, "segment"]].copy()
            a_display[val] = a_display[val].apply(format_no_decimals)

            st.dataframe(add_index(a_display))

st.divider()

# ================= L4L / YOY =================
st.markdown("## 📈 L4L Analysis")

df_yoy = df.groupby(col_code).agg({
    col_desc: "first",
    val_old: lambda s: decimal_sum(s),
    val_new: lambda s: decimal_sum(s),
    qty_old: lambda s: decimal_sum(s),
    qty_new: lambda s: decimal_sum(s)
}).reset_index()

# Combined table -> sort by newest year (val_new)
df_yoy = sort_by_col_desc(df_yoy, val_new)
df_yoy["YoY %"] = df_yoy.apply(lambda x: yoy_label(calc_yoy_clean(x[val_new], x[val_old])), axis=1)

df_yoy_display = df_yoy.copy()
for c in [val_old, val_new]:
    df_yoy_display[c] = df_yoy_display[c].apply(format_no_decimals)
for c in [qty_old, qty_new]:
    df_yoy_display[c] = df_yoy_display[c].apply(format_no_decimals)

st.dataframe(add_index(df_yoy_display[[col_code, col_desc, val_old, val_new, qty_old, qty_new, "YoY %"]]))

st.divider()

# ================= AUTO INSIGHTS =================
st.markdown("## 🧠 Auto Insights")

cat = df_context.groupby("Category Clean").agg({
    val_old: lambda s: decimal_sum(s),
    val_new: lambda s: decimal_sum(s)
}).reset_index()

# Combined -> sort by newest year
cat = sort_by_col_desc(cat, val_new)
cat["YoY"] = cat.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
cat["YoY %"] = cat["YoY"].apply(yoy_label)

st.write("### Top 5 Categories")
c1, c2 = st.columns(2)
with c1:
    st.write(f"#### {val_old}")
    top_old_cat = cat.sort_values(val_new, ascending=False).head(5)
    top_old_cat_display = top_old_cat.copy()
    top_old_cat_display[val_old] = top_old_cat_display[val_old].apply(format_no_decimals)
    st.dataframe(add_index(top_old_cat_display[["Category Clean", val_old]]))
with c2:
    st.write(f"#### {val_new}")
    top_new_cat = cat.sort_values(val_new, ascending=False).head(5)
    top_new_cat_display = top_new_cat.copy()
    top_new_cat_display[val_new] = top_new_cat_display[val_new].apply(format_no_decimals)
    st.dataframe(add_index(top_new_cat_display[["Category Clean", val_new, "YoY %"]]))

st.write("### Growth (L4L)")
growth = cat[cat["YoY"] > 0].sort_values("YoY", ascending=False).head(5)
if growth.empty:
    st.info("There is no growth in categories")
else:
    growth_display = growth.copy()
    growth_display[val_old] = growth_display[val_old].apply(format_no_decimals)
    growth_display[val_new] = growth_display[val_new].apply(format_no_decimals)
    st.dataframe(add_index(growth_display[["Category Clean", val_old, val_new, "YoY %"]]))

st.write("### Risk")
risk = cat[cat["YoY"] < 0].sort_values("YoY").head(5)
if risk.empty:
    st.success("There is no risk in categories")
else:
    risk_display = risk.copy()
    risk_display[val_old] = risk_display[val_old].apply(format_no_decimals)
    risk_display[val_new] = risk_display[val_new].apply(format_no_decimals)
    st.dataframe(add_index(risk_display[["Category Clean", val_old, val_new, "YoY %"]]))

st.divider()

# ================= CUSTOMER IMPACT =================
st.markdown("## 👥 Customer Impact (Growth vs Decline)")

all_categories = sorted(df_original_all["Category Clean"].dropna().unique()) if "Category Clean" in df_original_all.columns else []
selected_cat_impact = st.selectbox("Select Category for Impact Analysis", ["All Categories"] + all_categories)

all_brands = sorted(df_original_all[col_brand].dropna().unique()) if col_brand in df_original_all.columns else []
selected_brand_impact = st.selectbox("Select Brand (License)", ["All Brands"] + all_brands)

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
    growth_display[val_old] = growth_display[val_old].apply(format_no_decimals)
    growth_display[val_new] = growth_display[val_new].apply(format_no_decimals)
    growth_display["Change Value"] = growth_display["Change Value"].apply(format_no_decimals)
    st.dataframe(add_index(growth_display[[col_customer, val_old, val_new, "Change Value", "YoY %"]]))

st.write("### 🔴 Top Decline Drivers")
decline = impact[(impact["Change Value"] < 0)].sort_values("Change Value").head(10)
decline_special = impact[impact["Special Case"]].head(10)
decline = pd.concat([decline, decline_special])

if decline.empty:
    st.success("No decline across customers")
else:
    decline_display = decline.copy()
    decline_display[val_old] = decline_display[val_old].apply(format_no_decimals)
    decline_display[val_new] = decline_display[val_new].apply(format_no_decimals)
    decline_display["Change Value"] = decline_display["Change Value"].apply(format_no_decimals)
    st.dataframe(add_index(decline_display[[col_customer, val_old, val_new, "Change Value", "YoY %"]]))
