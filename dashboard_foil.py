# app.py
import streamlit as st
import pandas as pd
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import plotly.express as px

# =========================
# CONFIGURATION
# =========================
DISPLAY_DECIMALS = 0  # 0 => integers, 1 => one decimal place
MONTHS_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# =========================
# HELPERS & PRECISION
# =========================
def to_decimal(x):
    if pd.isna(x):
        return Decimal('0')
    if isinstance(x, Decimal):
        return x
    try:
        if isinstance(x, int):
            return Decimal(x)
        if isinstance(x, float):
            return Decimal(str(x))
        s = str(x).strip().replace(" ", "").replace(",", ".")
        if s == "" or s.lower() == "nan":
            return Decimal('0')
        return Decimal(s)
    except (InvalidOperation, Exception):
        return Decimal('0')

def decimal_sum(series):
    try:
        return sum(series.tolist(), Decimal('0'))
    except Exception:
        return Decimal(str(series.sum()))

def format_number_plain(d, decimals=DISPLAY_DECIMALS):
    if not isinstance(d, Decimal):
        d = to_decimal(d)
    if decimals == 0:
        q = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return f"{int(q)}"
    else:
        q = d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return f"{q:.1f}"

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

def sort_by_col_desc(df, col):
    if col in df.columns:
        try:
            return df.sort_values(by=col, ascending=False)
        except Exception:
            tmp = df.copy()
            tmp[col] = tmp[col].apply(lambda x: float(x) if isinstance(x, Decimal) else float(Decimal(str(x))))
            return tmp.sort_values(by=col, ascending=False)
    return df

def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

# =========================
# DATA LOADING & PREP
# =========================
def load_excel_as_df(file):
    if file is None:
        return None
    df = pd.read_excel(file, dtype=object, engine='openpyxl')
    df.columns = df.columns.str.strip()
    return df

def detect_columns_for_three_files(df):
    cols = {
        "Month": None, "Customer": None, "Country": None, "Vat": None,
        "Code": None, "Desc": None, "Brand": None, "Category": None,
        "NetValue": None, "Quantity": None
    }
    if df is None:
        # return synthetic names to avoid KeyError later
        for k in cols:
            cols[k] = f"__missing_{k}__"
        return cols

    lower_map = {col.lower(): col for col in df.columns}
    for key in lower_map:
        if "month" in key and cols["Month"] is None:
            cols["Month"] = lower_map[key]
        if "customer" in key and cols["Customer"] is None:
            cols["Customer"] = lower_map[key]
        if "country" in key and cols["Country"] is None:
            cols["Country"] = lower_map[key]
        if "vat" in key and cols["Vat"] is None:
            cols["Vat"] = lower_map[key]
        if ("art" in key or "art." in key or "art nr" in key or "artnr" in key or "art number" in key) and cols["Code"] is None:
            cols["Code"] = lower_map[key]
        if ("description" in key or "article" in key or "desc" in key) and cols["Desc"] is None:
            cols["Desc"] = lower_map[key]
        if "brand" in key and cols["Brand"] is None:
            cols["Brand"] = lower_map[key]
        if "category" in key and cols["Category"] is None:
            cols["Category"] = lower_map[key]
        if ("net" in key and "value" in key) or ("netvalue" in key) or ("net_value" in key) or ("net value" in key):
            if cols["NetValue"] is None:
                cols["NetValue"] = lower_map[key]
        if ("qty" in key or "quantity" in key) and cols["Quantity"] is None:
            cols["Quantity"] = lower_map[key]

    # Fallback: pick last two numeric-like columns if NetValue/Quantity missing
    if cols["NetValue"] is None or cols["Quantity"] is None:
        numeric_candidates = []
        for col in df.columns:
            sample = df[col].dropna().astype(str).head(10).tolist()
            numeric_count = sum(1 for s in sample if any(ch.isdigit() for ch in s))
            if numeric_count >= 1:
                numeric_candidates.append(col)
        if len(numeric_candidates) >= 2:
            if cols["NetValue"] is None:
                cols["NetValue"] = numeric_candidates[-2]
            if cols["Quantity"] is None:
                cols["Quantity"] = numeric_candidates[-1]

    # Ensure every key has a string column name (fallback to synthetic)
    for k in cols:
        if cols[k] is None:
            cols[k] = f"__missing_{k}__"
    return cols

def prepare_df_for_analysis(df, cols_map):
    if df is None:
        return None
    df = df.copy()
    # Ensure mapped columns exist
    for k, col in cols_map.items():
        if col not in df.columns:
            df[col] = "" if k not in ("NetValue", "Quantity") else Decimal('0')
    # Convert numeric columns to Decimal
    nv = cols_map["NetValue"]
    q = cols_map["Quantity"]
    df[nv] = df[nv].apply(to_decimal)
    df[q] = df[q].apply(to_decimal)
    # Ensure text columns are strings
    for key in ["Month", "Customer", "Country", "Vat", "Code", "Desc", "Brand", "Category"]:
        col = cols_map.get(key)
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("").replace("nan", "")
        else:
            df[col] = ""
    # Category clean
    df["Category Clean"] = df[cols_map["Category"]].apply(normalize_category)
    # Remove rows with empty description or 'none'
    df = df[df[cols_map["Desc"]].notna()]
    df = df[df[cols_map["Desc"]].str.lower() != "none"]
    return df

# =========================
# UI: file upload and detection
# =========================
st.set_page_config(layout="wide", page_title="Sales Intelligence")
st.title("📊 Sales Intelligence Dashboard")

st.markdown("### Upload Excel files (3 files supported)")
col1, col2, col3 = st.columns(3)
with col1:
    file_current = st.file_uploader("Current Year (partial YTD)", type=["xlsx"], key="file_current")
with col2:
    file_prev = st.file_uploader("Previous Year (full)", type=["xlsx"], key="file_prev")
with col3:
    file_old = st.file_uploader("Two Years Ago (full)", type=["xlsx"], key="file_old")

if not file_current and not file_prev and not file_old:
    st.info("Upload at least one file to start. Recommended: upload all three for full multi-year analysis.")
    st.stop()

# Load raw DataFrames
df_curr_raw = load_excel_as_df(file_current) if file_current else None
df_prev_raw = load_excel_as_df(file_prev) if file_prev else None
df_old_raw = load_excel_as_df(file_old) if file_old else None

# Detect columns and prepare
cols_curr = detect_columns_for_three_files(df_curr_raw) if df_curr_raw is not None else None
cols_prev = detect_columns_for_three_files(df_prev_raw) if df_prev_raw is not None else None
cols_old = detect_columns_for_three_files(df_old_raw) if df_old_raw is not None else None

df_curr = prepare_df_for_analysis(df_curr_raw, cols_curr) if df_curr_raw is not None else None
df_prev = prepare_df_for_analysis(df_prev_raw, cols_prev) if df_prev_raw is not None else None
df_old = prepare_df_for_analysis(df_old_raw, cols_old) if df_old_raw is not None else None

# Keep original copies (raw totals) to match Excel when no filters applied
df_curr_original = df_curr.copy() if df_curr is not None else None
df_prev_original = df_prev.copy() if df_prev is not None else None
df_old_original = df_old.copy() if df_old is not None else None

# =========================
# SESSION STATE: main view tracking and safe filter reset
# =========================
if "main_view" not in st.session_state:
    st.session_state.main_view = None

def reset_global_filters_for_prefix(prefixes=("l4l", "full")):
    for p in prefixes:
        for k in ("filter_country", "filter_customer", "filter_category"):
            key = f"{k}_{p}"
            if key in st.session_state:
                del st.session_state[key]

# =========================
# Filter widget helper (robust)
# =========================
def create_and_apply_filters(df_ref, cols_map, prefix="global"):
    if df_ref is None:
        return None

    country_col = cols_map["Country"]
    cust_col = cols_map["Customer"]
    cat_col = "Category Clean"

    # Build options safely
    try:
        countries = ["All Countries"] + sorted(df_ref[country_col].replace("", pd.NA).dropna().unique().tolist())
    except Exception:
        countries = ["All Countries"]
    try:
        customers = ["All Customers"] + sorted(df_ref[cust_col].replace("", pd.NA).dropna().unique().tolist())
    except Exception:
        customers = ["All Customers"]
    try:
        categories = ["All Categories"] + sorted(df_ref[cat_col].dropna().unique().tolist())
    except Exception:
        categories = ["All Categories"]

    # Widget keys
    key_country = f"filter_country_{prefix}"
    key_customer = f"filter_customer_{prefix}"
    key_category = f"filter_category_{prefix}"

    # Determine default indices safely
    def safe_index(lst, val):
        try:
            return lst.index(val)
        except Exception:
            return 0

    # Create widgets (do not write directly to session_state before widget call)
    sel_country = st.selectbox("Country", countries, index=safe_index(countries, st.session_state.get(key_country, "All Countries")), key=key_country)
    sel_customer = st.selectbox("Customer", customers, index=safe_index(customers, st.session_state.get(key_customer, "All Customers")), key=key_customer)
    sel_category = st.selectbox("Category", categories, index=safe_index(categories, st.session_state.get(key_category, "All Categories")), key=key_category)

    # Apply filters
    d = df_ref.copy()
    if sel_country != "All Countries":
        d = d[d[country_col] == sel_country]
    if sel_customer != "All Customers":
        d = d[d[cust_col] == sel_customer]
    if sel_category != "All Categories":
        d = d[d[cat_col] == sel_category]
    return d

# =========================
# Dashboard rendering (single place)
# =========================
def render_dashboard(df, df_original_all, cols_map, context_name="Dataset"):
    if df is None:
        st.info("No data for this view.")
        return

    month_col = cols_map["Month"]
    cust_col = cols_map["Customer"]
    country_col = cols_map["Country"]
    code_col = cols_map["Code"]
    desc_col = cols_map["Desc"]
    brand_col = cols_map["Brand"]
    net_col = cols_map["NetValue"]
    qty_col = cols_map["Quantity"]

    # KPI
    st.markdown("## 💰 KPI (Net / Qty)")
    # Determine whether to use original totals to match Excel (no filters)
    no_filters = (
        (st.session_state.get(f"filter_country_l4l", "All Countries") == "All Countries") and
        (st.session_state.get(f"filter_customer_l4l", "All Customers") == "All Customers") and
        (st.session_state.get(f"filter_category_l4l", "All Categories") == "All Categories")
    )
    use_df_for_kpi = df_original_all if df_original_all is not None and no_filters else df

    total_net = decimal_sum(use_df_for_kpi[net_col]) if net_col in use_df_for_kpi.columns else Decimal('0')
    total_qty = decimal_sum(use_df_for_kpi[qty_col]) if qty_col in use_df_for_kpi.columns else Decimal('0')

    c1, c2 = st.columns(2)
    c1.metric(f"Net ({context_name})", format_number_plain(total_net))
    c2.metric(f"Qty ({context_name})", format_number_plain(total_qty))

    st.divider()

    # Category performance (sorted by net descending)
    st.markdown("## 📊 Category Performance")
    cat_perf = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
    cat_perf = sort_by_col_desc(cat_perf, net_col)
    if cat_perf.empty:
        st.info("No category data")
    else:
        disp = cat_perf.copy()
        disp[net_col] = disp[net_col].apply(format_number_plain)
        st.dataframe(add_index(disp))

    st.divider()

    # Brand performance
    st.markdown("## 🏷️ Brand Performance")
    brand = df.groupby(brand_col).agg({net_col: decimal_sum}).reset_index()
    brand = sort_by_col_desc(brand, net_col)
    if brand.empty:
        st.info("No brand data")
    else:
        brand_disp = brand.copy()
        brand_disp[net_col] = brand_disp[net_col].apply(format_number_plain)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.dataframe(add_index(brand_disp))
        with c2:
            plot_df = brand.copy()
            plot_df[net_col] = plot_df[net_col].apply(lambda x: float(x))
            st.plotly_chart(px.pie(plot_df, names=brand_col, values=net_col), use_container_width=True)

    st.divider()

    # Top products (two panels)
    st.markdown("## 🏆 Top Products")
    base_df = df.copy()
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Top SKUs by Net")
        sku_net = base_df.groupby([code_col, desc_col]).agg({net_col: decimal_sum, qty_col: decimal_sum}).reset_index()
        sku_net = sort_by_col_desc(sku_net, net_col)
        if sku_net.empty:
            st.info("No SKUs")
        else:
            top_net = sku_net.head(20).copy()
            top_net[net_col] = top_net[net_col].apply(format_number_plain)
            top_net[qty_col] = top_net[qty_col].apply(format_number_plain)
            st.dataframe(add_index(top_net[[code_col, desc_col, net_col, qty_col]]))
    with col2:
        st.write("### Top SKUs by Quantity")
        sku_qty = base_df.groupby([code_col, desc_col]).agg({qty_col: decimal_sum, net_col: decimal_sum}).reset_index()
        sku_qty = sort_by_col_desc(sku_qty, qty_col)
        if sku_qty.empty:
            st.info("No SKUs")
        else:
            top_qty = sku_qty.head(20).copy()
            top_qty[net_col] = top_qty[net_col].apply(format_number_plain)
            top_qty[qty_col] = top_qty[qty_col].apply(format_number_plain)
            st.dataframe(add_index(top_qty[[code_col, desc_col, qty_col, net_col]]))

    st.divider()

    # Pareto (per-panel)
    st.markdown("## 📊 Pareto Analysis")
    ptab1, ptab2 = st.tabs(["Net Pareto", "Qty Pareto"])
    with ptab1:
        p = df.groupby(code_col).agg({desc_col: "first", net_col: decimal_sum}).reset_index()
        p = sort_by_col_desc(p, net_col)
        if p.empty:
            st.info("No data")
        else:
            p["cum_value"] = p[net_col].cumsum()
            total_value = decimal_sum(p[net_col])
            if total_value == 0:
                st.info("Total is zero")
            else:
                p["cum_share"] = p["cum_value"].apply(lambda x: (x / total_value))
                top80 = p[p["cum_share"] <= Decimal('0.8')]
                top80[net_col] = top80[net_col].apply(format_number_plain)
                st.dataframe(add_index(top80[[code_col, desc_col, net_col]]))
    with ptab2:
        p = df.groupby(code_col).agg({desc_col: "first", qty_col: decimal_sum}).reset_index()
        p = sort_by_col_desc(p, qty_col)
        if p.empty:
            st.info("No data")
        else:
            p["cum_value"] = p[qty_col].cumsum()
            total_value = decimal_sum(p[qty_col])
            if total_value == 0:
                st.info("Total is zero")
            else:
                p["cum_share"] = p["cum_value"].apply(lambda x: (x / total_value))
                top80 = p[p["cum_share"] <= Decimal('0.8')]
                top80[qty_col] = top80[qty_col].apply(format_number_plain)
                st.dataframe(add_index(top80[[code_col, desc_col, qty_col]]))

    st.divider()

    # ABC (per-panel)
    st.markdown("## 📊 ABC Analysis")
    atab1, atab2 = st.tabs(["ABC by Net", "ABC by Qty"])
    with atab1:
        a = df.groupby([code_col, desc_col]).agg({net_col: decimal_sum}).reset_index()
        a = sort_by_col_desc(a, net_col)
        if a.empty:
            st.info("No data")
        else:
            total_val = decimal_sum(a[net_col])
            if total_val == 0:
                st.info("Total is zero")
            else:
                a["cum"] = a[net_col].cumsum().apply(lambda x: x / total_val)
                a["segment"] = "C"
                a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
                a.loc[(a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')), "segment"] = "B"
                a[net_col] = a[net_col].apply(format_number_plain)
                st.dataframe(add_index(a[[code_col, desc_col, net_col, "segment"]]))
    with atab2:
        a = df.groupby([code_col, desc_col]).agg({qty_col: decimal_sum}).reset_index()
        a = sort_by_col_desc(a, qty_col)
        if a.empty:
            st.info("No data")
        else:
            total_val = decimal_sum(a[qty_col])
            if total_val == 0:
                st.info("Total is zero")
            else:
                a["cum"] = a[qty_col].cumsum().apply(lambda x: x / total_val)
                a["segment"] = "C"
                a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
                a.loc[(a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')), "segment"] = "B"
                a[qty_col] = a[qty_col].apply(format_number_plain)
                st.dataframe(add_index(a[[code_col, desc_col, qty_col, "segment"]]))

    st.divider()

    # L4L / YOY (SKU level) - combined table sorted by net descending
    st.markdown("## 📈 SKU-level (Net / Qty)")
    yoy = df.groupby(code_col).agg({desc_col: "first", net_col: decimal_sum, qty_col: decimal_sum}).reset_index()
    yoy = sort_by_col_desc(yoy, net_col)
    if yoy.empty:
        st.info("No data")
    else:
        yoy_disp = yoy.copy()
        yoy_disp[net_col] = yoy_disp[net_col].apply(format_number_plain)
        yoy_disp[qty_col] = yoy_disp[qty_col].apply(format_number_plain)
        st.dataframe(add_index(yoy_disp[[code_col, desc_col, net_col, qty_col]]))

    st.divider()

    # Auto insights (top categories)
    st.markdown("## 🧠 Auto Insights")
    cat_summary = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
    cat_summary = sort_by_col_desc(cat_summary, net_col)
    if cat_summary.empty:
        st.info("No category insights")
    else:
        top5 = cat_summary.head(5).copy()
        top5[net_col] = top5[net_col].apply(format_number_plain)
        st.write("Top 5 Categories by Net")
        st.dataframe(add_index(top5))

    st.divider()

    # Customer impact note (requires two datasets to compute change)
    st.markdown("## 👥 Customer Impact (Growth vs Decline)")
    st.info("To compute customer-level growth/decline you need to compare two datasets (e.g., current vs previous). Use the main tabs to compare years.")

# =========================
# MAIN TABS
# =========================
tab_overview, tab_l4l, tab_full = st.tabs(["Overview (3-year L4L)", "Like-for-Like (L4L)", "Full Year Analysis"])

# TAB: Overview (3-year L4L)
with tab_overview:
    if st.session_state.main_view != "overview":
        reset_global_filters_for_prefix(("l4l", "full"))
        st.session_state.main_view = "overview"

    st.header("Overview — 3-year Like-for-Like (YTD sync)")
    if df_curr_original is None or df_prev_original is None:
        st.info("Upload at least current-year and previous-year files to see the overview.")
    else:
        months_present = df_curr_original[cols_curr["Month"]].dropna().unique().tolist()
        months_sorted = sorted(months_present, key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
        st.info(f"Detected months in current-year file: {', '.join(months_sorted)}")

        prev_l4l = df_prev_original[df_prev_original[cols_prev["Month"]].isin(months_sorted)] if df_prev_original is not None else None
        old_l4l = df_old_original[df_old_original[cols_old["Month"]].isin(months_sorted)] if df_old_original is not None else None

        val_curr = decimal_sum(df_curr_original[cols_curr["NetValue"]]) if df_curr_original is not None else Decimal('0')
        val_prev = decimal_sum(prev_l4l[cols_prev["NetValue"]]) if prev_l4l is not None else Decimal('0')
        val_old = decimal_sum(old_l4l[cols_old["NetValue"]]) if old_l4l is not None else Decimal('0')

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Year (YTD)", format_number_plain(val_curr))
        c2.metric("Previous Year (L4L)", format_number_plain(val_prev), yoy_label(calc_yoy_clean(val_curr, val_prev)))
        c3.metric("Two Years Ago (L4L)", format_number_plain(val_old), yoy_label(calc_yoy_clean(val_prev, val_old)))

        chart_df = pd.DataFrame({
            "Year": ["Two Years Ago", "Previous Year", "Current Year"],
            "Net": [float(val_old), float(val_prev), float(val_curr)]
        })
        st.plotly_chart(px.bar(chart_df, x="Year", y="Net", text="Net", title="3-year L4L Net (YTD)"), use_container_width=True)

# TAB: Like-for-Like (detailed) with year selection and month range
with tab_l4l:
    if st.session_state.main_view != "l4l":
        reset_global_filters_for_prefix(("l4l",))
        st.session_state.main_view = "l4l"

    st.header("Like-for-Like (L4L) — choose years and months to compare")
    # Determine available datasets (files uploaded)
    available_years = []
    dataset_map = {}
    if df_curr_original is not None:
        available_years.append("Current Year")
        dataset_map["Current Year"] = (df_curr_original, cols_curr)
    if df_prev_original is not None:
        available_years.append("Previous Year")
        dataset_map["Previous Year"] = (df_prev_original, cols_prev)
    if df_old_original is not None:
        available_years.append("Two Years Ago")
        dataset_map["Two Years Ago"] = (df_old_original, cols_old)

    if len(available_years) < 2:
        st.info("Upload at least two files to compare years in L4L.")
    else:
        # Year selection dropdowns
        col_a, col_b = st.columns(2)
        with col_a:
            left_year = st.selectbox("Select first year (A)", available_years, index=0, key="l4l_left_year")
        with col_b:
            # default to next available year if possible
            default_right = available_years[1] if len(available_years) > 1 else available_years[0]
            right_year = st.selectbox("Select second year (B)", available_years, index=available_years.index(default_right), key="l4l_right_year")

        if left_year == right_year:
            st.warning("Choose two different years to compare.")
        else:
            # Month range selection: union of months present in both selected datasets
            df_left, cols_left = dataset_map[left_year]
            df_right, cols_right = dataset_map[right_year]

            months_left = df_left[cols_left["Month"]].dropna().unique().tolist()
            months_right = df_right[cols_right["Month"]].dropna().unique().tolist()
            months_union = sorted(list(set(months_left) | set(months_right)), key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)

            selected_months = st.multiselect("Select months to include in comparison", months_union, default=months_union)

            # Global filters (apply to both datasets) — use current-year as reference for options if available, else left dataset
            ref_df_for_filters = df_curr_original if df_curr_original is not None else df_left
            ref_cols_for_filters = cols_curr if df_curr_original is not None else cols_left
            filtered_ref = create_and_apply_filters(ref_df_for_filters, ref_cols_for_filters, prefix="l4l")

            # Apply same filter selections to left and right datasets
            sc = st.session_state
            country_sel = sc.get("filter_country_l4l", "All Countries")
            cust_sel = sc.get("filter_customer_l4l", "All Customers")
            cat_sel = sc.get("filter_category_l4l", "All Categories")

            def apply_same_filters_to(df_src, cols_map):
                if df_src is None:
                    return None
                d = df_src.copy()
                if country_sel != "All Countries":
                    d = d[d[cols_map["Country"]] == country_sel]
                if cust_sel != "All Customers":
                    d = d[d[cols_map["Customer"]] == cust_sel]
                if cat_sel != "All Categories":
                    d = d[d["Category Clean"] == cat_sel]
                return d

            left_filtered = apply_same_filters_to(df_left, cols_left)
            right_filtered = apply_same_filters_to(df_right, cols_right)

            # Filter by selected months
            if selected_months:
                left_filtered = left_filtered[left_filtered[cols_left["Month"]].isin(selected_months)]
                right_filtered = right_filtered[right_filtered[cols_right["Month"]].isin(selected_months)]
            else:
                st.info("Select at least one month to compare.")

            # Show side-by-side KPIs and render dashboards for each selected year
            st.markdown("### Comparison KPIs")
            left_net = decimal_sum(left_filtered[cols_left["NetValue"]]) if left_filtered is not None else Decimal('0')
            right_net = decimal_sum(right_filtered[cols_right["NetValue"]]) if right_filtered is not None else Decimal('0')

            l1, l2 = st.columns(2)
            l1.metric(f"{left_year} Net (selected months)", format_number_plain(left_net))
            l2.metric(f"{right_year} Net (selected months)", format_number_plain(right_net), yoy_label(calc_yoy_clean(right_net, left_net)))

            st.markdown("### Left Year Dashboard")
            render_dashboard(left_filtered, df_left, cols_left, context_name=left_year)

            st.markdown("### Right Year Dashboard")
            render_dashboard(right_filtered, df_right, cols_right, context_name=right_year)

# TAB: Full Year Analysis with year selection
with tab_full:
    if st.session_state.main_view != "full":
        reset_global_filters_for_prefix(("full",))
        st.session_state.main_view = "full"

    st.header("Full Year Analysis — choose which year to analyze")
    # Build list of available full-year datasets (previous and two-years-ago)
    full_year_options = []
    full_map = {}
    if df_prev_original is not None:
        full_year_options.append("Previous Year (Full)")
        full_map["Previous Year (Full)"] = (df_prev_original, cols_prev)
    if df_old_original is not None:
        full_year_options.append("Two Years Ago (Full)")
        full_map["Two Years Ago (Full)"] = (df_old_original, cols_old)

    if not full_year_options:
        st.info("Upload at least one full-year file (previous year or two years ago) to use Full Year analysis.")
    else:
        selected_full = st.selectbox("Select full-year dataset to analyze", full_year_options, key="full_selected_year")
        df_selected, cols_selected = full_map[selected_full]

        # Global filters for full-year (separate prefix)
        filtered_selected = create_and_apply_filters(df_selected, cols_selected, prefix="full")

        # Render dashboard for selected full-year dataset
        render_dashboard(filtered_selected, df_selected, cols_selected, context_name=selected_full)

        # If both full-year datasets are present, offer side-by-side comparison
        if len(full_year_options) == 2:
            st.markdown("### Compare the two full-year datasets")
            other = [o for o in full_year_options if o != selected_full][0]
            df_other, cols_other = full_map[other]

            # Apply same filters to the other dataset using session_state selections for 'full'
            sc = st.session_state
            country_sel = sc.get("filter_country_full", "All Countries")
            cust_sel = sc.get("filter_customer_full", "All Customers")
            cat_sel = sc.get("filter_category_full", "All Categories")
            other_filtered = df_other.copy()
            if country_sel != "All Countries":
                other_filtered = other_filtered[other_filtered[cols_other["Country"]] == country_sel]
            if cust_sel != "All Customers":
                other_filtered = other_filtered[other_filtered[cols_other["Customer"]] == cust_sel]
            if cat_sel != "All Categories":
                other_filtered = other_filtered[other_filtered["Category Clean"] == cat_sel]

            st.markdown(f"#### Comparison: {selected_full} vs {other}")
            net_sel = decimal_sum(filtered_selected[cols_selected["NetValue"]]) if filtered_selected is not None else Decimal('0')
            net_other = decimal_sum(other_filtered[cols_other["NetValue"]]) if other_filtered is not None else Decimal('0')
            c1, c2 = st.columns(2)
            c1.metric(f"{selected_full} Net", format_number_plain(net_sel))
            c2.metric(f"{other} Net", format_number_plain(net_other), yoy_label(calc_yoy_clean(net_sel, net_other)))

            st.markdown(f"##### Dashboard for {other}")
            render_dashboard(other_filtered, df_other, cols_other, context_name=other)

# End of file
