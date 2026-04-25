# app.py
import streamlit as st
import pandas as pd
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import plotly.express as px

# =========================
# CONFIGURATION
# =========================
# Display decimals in tables: 0 (integers) or 1 (one decimal place)
DISPLAY_DECIMALS = 0

# Month ordering for L4L selection (English month names expected in Excel)
MONTHS_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# =========================
# HELPERS & PRECISION
# =========================
def to_decimal(x):
    """Convert Excel cell to Decimal preserving visible precision."""
    if pd.isna(x):
        return Decimal('0')
    if isinstance(x, Decimal):
        return x
    try:
        # ints -> Decimal directly; floats -> Decimal(str(x)) to preserve representation
        if isinstance(x, int):
            return Decimal(x)
        if isinstance(x, float):
            return Decimal(str(x))
        s = str(x).strip()
        # remove thousands separators (space) and unify decimal separator
        s = s.replace(" ", "").replace(",", ".")
        if s == "" or s.lower() == "nan":
            return Decimal('0')
        return Decimal(s)
    except (InvalidOperation, Exception):
        return Decimal('0')

def decimal_sum(series):
    """Sum a pandas Series of Decimal values safely."""
    try:
        return sum(series.tolist(), Decimal('0'))
    except Exception:
        # fallback to pandas sum then convert
        return Decimal(str(series.sum()))

def format_number_plain(d, decimals=DISPLAY_DECIMALS):
    """Return number as plain string without thousands separators.
    decimals: 0 or 1
    """
    if not isinstance(d, Decimal):
        d = to_decimal(d)
    if decimals == 0:
        q = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return f"{int(q)}"
    else:
        q = d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        # ensure one decimal place
        return f"{q:.1f}"

def calc_yoy_clean(new, old):
    """Calculate YoY percent using Decimal. Returns Decimal or None for special case."""
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
    """Sort descending by col if present; keep numeric type for sorting."""
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
    """Read Excel into DataFrame with dtype=object to avoid pandas coercion."""
    if file is None:
        return None
    df = pd.read_excel(file, dtype=object, engine='openpyxl')
    df.columns = df.columns.str.strip()
    return df

def detect_columns_for_three_files(df):
    """
    Expect Excel layout with at least:
    Month, Customer Name, Country, Vat ID Nr., Art. Nr., Article description, Brand Name, Category, Net Value, Quantity
    But column positions may vary. We'll try to detect by name heuristics.
    Returns a mapping of expected column names to actual df columns.
    """
    cols = {c: None for c in [
        "Month", "Customer", "Country", "Vat", "Code", "Desc", "Brand", "Category", "NetValue", "Quantity"
    ]}
    # Lowercase mapping of actual columns
    lower_map = {col.lower(): col for col in df.columns}
    for key in list(lower_map.keys()):
        # match heuristics
        if "month" in key and cols["Month"] is None:
            cols["Month"] = lower_map[key]
        if "customer" in key and cols["Customer"] is None:
            cols["Customer"] = lower_map[key]
        if "country" in key and cols["Country"] is None:
            cols["Country"] = lower_map[key]
        if "vat" in key and cols["Vat"] is None:
            cols["Vat"] = lower_map[key]
        if ("art" in key or "art." in key or "art nr" in key or "art nr." in key or "art nr" in key) and cols["Code"] is None:
            cols["Code"] = lower_map[key]
        if ("article" in key or "description" in key or "desc" in key) and cols["Desc"] is None:
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
    # Fallback: if NetValue or Quantity not found, try to use last two numeric columns
    if cols["NetValue"] is None or cols["Quantity"] is None:
        # try to find numeric-like columns by sampling
        numeric_candidates = []
        for col in df.columns:
            sample = df[col].dropna().astype(str).head(10).tolist()
            # if many entries look numeric
            numeric_count = sum(1 for s in sample if any(ch.isdigit() for ch in s))
            if numeric_count >= 1:
                numeric_candidates.append(col)
        # choose last two candidates as NetValue and Quantity if available
        if len(numeric_candidates) >= 2:
            if cols["NetValue"] is None:
                cols["NetValue"] = numeric_candidates[-2]
            if cols["Quantity"] is None:
                cols["Quantity"] = numeric_candidates[-1]
    return cols

def prepare_df_for_analysis(df, cols_map):
    """Normalize columns, convert numeric columns to Decimal, create Category Clean."""
    df = df.copy()
    # Ensure columns exist
    for k, v in cols_map.items():
        if v is None or v not in df.columns:
            # create empty column
            df[v if v is not None else k] = ""
    # Convert numeric columns
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

st.markdown("### Upload Excel files (three files supported)")
col1, col2, col3 = st.columns(3)
with col1:
    file_current = st.file_uploader("Upload Current Year (partial YTD)", type=["xlsx"], key="file_current")
with col2:
    file_prev = st.file_uploader("Upload Previous Year (full)", type=["xlsx"], key="file_prev")
with col3:
    file_old = st.file_uploader("Upload Two Years Ago (full)", type=["xlsx"], key="file_old")

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
# GLOBAL FILTERS (reset on view change)
# We'll store filter selections in session_state and reset when main view changes
# =========================
if "main_view" not in st.session_state:
    st.session_state.main_view = None

# Tabs for main views
tab_overview, tab_l4l, tab_full = st.tabs(["Overview (3-year L4L)", "Like-for-Like (L4L)", "Full Year Analysis"])

# Helper to reset global filters
def reset_global_filters():
    for k in ["filter_country", "filter_customer", "filter_category"]:
        if k in st.session_state:
            del st.session_state[k]

# =========================
# Render functions (single place)
# =========================
def render_dashboard(df, df_original_all, cols_map, context_name=""):
    """
    df: filtered dataframe to use for most views (after country/customer/category filters)
    df_original_all: original dataset (before some filters) used for KPI when no filters applied
    cols_map: mapping of columns for this dataset
    """
    # Column names
    month_col = cols_map["Month"]
    cust_col = cols_map["Customer"]
    country_col = cols_map["Country"]
    vat_col = cols_map["Vat"]
    code_col = cols_map["Code"]
    desc_col = cols_map["Desc"]
    brand_col = cols_map["Brand"]
    cat_col = cols_map["Category"]
    net_col = cols_map["NetValue"]
    qty_col = cols_map["Quantity"]

    # KPI
    st.markdown("## 💰 KPI (Net / Qty)")
    # If no filters applied (country/customer/category all default), show totals from original_all to match Excel
    no_filters = (
        (st.session_state.get("filter_country", "All Countries") == "All Countries") and
        (st.session_state.get("filter_customer", "All Customers") == "All Customers") and
        (st.session_state.get("filter_category", "All Categories") == "All Categories")
    )
    use_df_for_kpi = df_original_all if no_filters and df_original_all is not None else df

    s_old = decimal_sum(use_df_for_kpi[net_col]) if net_col in use_df_for_kpi.columns else Decimal('0')
    q_old = decimal_sum(use_df_for_kpi[qty_col]) if qty_col in use_df_for_kpi.columns else Decimal('0')

    # For L4L comparisons we may have separate older/newer files; here we display the dataset's own net/qty
    c1, c2 = st.columns(2)
    c1.metric(f"Net ({context_name})", format_number_plain(s_old))
    c2.metric(f"Qty ({context_name})", format_number_plain(q_old))

    st.divider()

    # CATEGORY PERFORMANCE (combined table sorted by newest year net)
    st.markdown("## 📊 Category Performance")
    cat_perf = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
    # If we have another dataset to compare (e.g., previous year), the calling code should merge; here we show single dataset category ranking
    cat_perf = sort_by_col_desc(cat_perf, net_col)
    if cat_perf.empty:
        st.info("No category data")
    else:
        display = cat_perf.copy()
        display[net_col] = display[net_col].apply(format_number_plain)
        st.dataframe(add_index(display))

    st.divider()

    # BRAND PERFORMANCE
    st.markdown("## 🏷️ Brand Performance")
    brand = df.groupby(brand_col).agg({net_col: decimal_sum}).reset_index()
    brand = sort_by_col_desc(brand, net_col)
    if brand.empty:
        st.info("No brand data")
    else:
        # Pie chart requires numeric floats
        brand_plot = brand.copy()
        brand_plot[net_col] = brand_plot[net_col].apply(lambda x: float(x))
        c1, c2 = st.columns([1, 2])
        with c1:
            st.dataframe(add_index(brand.assign(**{net_col: brand[net_col].apply(format_number_plain)})))
        with c2:
            st.plotly_chart(px.pie(brand_plot, names=brand_col, values=net_col), use_container_width=True)

    st.divider()

    # TOP PRODUCTS (two panels: net and qty)
    st.markdown("## 🏆 Top Products")
    base_df = df.copy()
    c1, c2 = st.columns(2)
    with c1:
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
    with c2:
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

    # PARETO (per-panel: sort by panel's net)
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

    # L4L / YOY table (combined table sorted by newest year net)
    st.markdown("## 📈 L4L / YoY (SKU level)")
    yoy = df.groupby(code_col).agg({desc_col: "first", net_col: decimal_sum, qty_col: decimal_sum}).reset_index()
    yoy = sort_by_col_desc(yoy, net_col)
    if yoy.empty:
        st.info("No data")
    else:
        yoy_display = yoy.copy()
        yoy_display[net_col] = yoy_display[net_col].apply(format_number_plain)
        yoy_display[qty_col] = yoy_display[qty_col].apply(format_number_plain)
        st.dataframe(add_index(yoy_display[[code_col, desc_col, net_col, qty_col]]))

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

    # Customer impact (growth vs decline) - using df_original_all for baseline if no filters
    st.markdown("## 👥 Customer Impact (Growth vs Decline)")
    # For impact we need previous period to compare; calling code should provide merged datasets if needed.
    st.info("Customer impact table requires both current and previous datasets to compute change. Use the main tabs to compare years.")

# =========================
# MAIN TABS: Overview, L4L, Full Year
# =========================

# Helper to create filter widgets and apply them to a dataset
def create_and_apply_filters(df_ref, cols_map, prefix="global"):
    """Create country/customer/category filters and apply to df_ref. Persist selections in session_state."""
    if df_ref is None:
        return None
    country_col = cols_map["Country"]
    cust_col = cols_map["Customer"]
    cat_col = "Category Clean"

    # Build options
    countries = ["All Countries"] + sorted(df_ref[country_col].replace("", pd.NA).dropna().unique().tolist())
    customers = ["All Customers"] + sorted(df_ref[cust_col].replace("", pd.NA).dropna().unique().tolist())
    categories = ["All Categories"] + sorted(df_ref[cat_col].dropna().unique().tolist())

    # Restore or create session_state keys
    sc = st.session_state
    key_country = f"filter_country_{prefix}"
    key_customer = f"filter_customer_{prefix}"
    key_category = f"filter_category_{prefix}"

    if key_country not in sc:
        sc[key_country] = "All Countries"
    if key_customer not in sc:
        sc[key_customer] = "All Customers"
    if key_category not in sc:
        sc[key_category] = "All Categories"

    # Widgets
    sc[key_country] = st.selectbox("Country", countries, index=countries.index(sc[key_country]) if sc[key_country] in countries else 0, key=key_country)
    sc[key_customer] = st.selectbox("Customer", customers, index=customers.index(sc[key_customer]) if sc[key_customer] in customers else 0, key=key_customer)
    sc[key_category] = st.selectbox("Category", categories, index=categories.index(sc[key_category]) if sc[key_category] in categories else 0, key=key_category)

    # Apply filters
    d = df_ref.copy()
    if sc[key_country] != "All Countries":
        d = d[d[country_col] == sc[key_country]]
    if sc[key_customer] != "All Customers":
        d = d[d[cust_col] == sc[key_customer]]
    if sc[key_category] != "All Categories":
        d = d[d[cat_col] == sc[key_category]]
    return d

# TAB: Overview (3-year L4L)
with tab_overview:
    st.header("Overview — 3-year Like-for-Like (YTD sync)")
    # Reset global filters when switching to this tab
    if st.session_state.main_view != "overview":
        reset_global_filters()
        st.session_state.main_view = "overview"

    if df_curr is None or df_prev is None:
        st.info("Upload at least current year and previous year files to see 3-year overview.")
    else:
        # Determine months present in current-year file
        months_present = df_curr_original[cols_curr["Month"]].dropna().unique().tolist()
        months_present_sorted = sorted(months_present, key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
        st.info(f"Detected months in current-year file: {', '.join(months_present_sorted)}")
        # Use those months to filter previous and old year for L4L
        df_prev_l4l = df_prev_original[df_prev_original[cols_prev["Month"]].isin(months_present_sorted)] if df_prev_original is not None else None
        df_old_l4l = df_old_original[df_old_original[cols_old["Month"]].isin(months_present_sorted)] if df_old_original is not None else None

        # Show KPIs for three years (if available)
        val_curr = decimal_sum(df_curr_original[cols_curr["NetValue"]]) if df_curr_original is not None else Decimal('0')
        val_prev = decimal_sum(df_prev_l4l[cols_prev["NetValue"]]) if df_prev_l4l is not None else Decimal('0')
        val_old = decimal_sum(df_old_l4l[cols_old["NetValue"]]) if df_old_l4l is not None else Decimal('0')

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Year (YTD)", format_number_plain(val_curr))
        c2.metric("Previous Year (L4L)", format_number_plain(val_prev), yoy_label(calc_yoy_clean(val_curr, val_prev)))
        c3.metric("Two Years Ago (L4L)", format_number_plain(val_old), yoy_label(calc_yoy_clean(val_prev, val_old)))

        # Small bar chart
        chart_df = pd.DataFrame({
            "Year": ["Two Years Ago", "Previous Year", "Current Year"],
            "Net": [float(val_old), float(val_prev), float(val_curr)]
        })
        st.plotly_chart(px.bar(chart_df, x="Year", y="Net", text="Net", title="3-year L4L Net (YTD)"), use_container_width=True)

# TAB: Like-for-Like (detailed)
with tab_l4l:
    st.header("Like-for-Like (L4L) — choose months to compare")
    # Reset global filters when switching to this tab
    if st.session_state.main_view != "l4l":
        reset_global_filters()
        st.session_state.main_view = "l4l"

    if df_curr is None:
        st.info("Upload current-year file to use L4L analysis.")
    else:
        # Global filters applied to all datasets (we use current-year as reference for options)
        filtered_curr = create_and_apply_filters(df_curr_original, cols_curr, prefix="l4l")
        # Choose months to analyze (from current-year original)
        available_months = df_curr_original[cols_curr["Month"]].dropna().unique().tolist()
        available_months_sorted = sorted(available_months, key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
        selected_months = st.multiselect("Select months to include in L4L", available_months_sorted, default=available_months_sorted)
        if not selected_months:
            st.info("Select at least one month.")
        else:
            # Filter datasets by selected months
            curr_for_analysis = filtered_curr[filtered_curr[cols_curr["Month"]].isin(selected_months)]
            prev_for_analysis = df_prev_original[df_prev_original[cols_prev["Month"]].isin(selected_months)] if df_prev_original is not None else None
            old_for_analysis = df_old_original[df_old["Month"]].isin(selected_months) if df_old_original is not None else None

            # If previous/old exist, apply same global filters to them
            if prev_for_analysis is not None:
                # apply country/customer/category filters from session_state
                sc = st.session_state
                country_sel = sc.get("filter_country_l4l", "All Countries")
                cust_sel = sc.get("filter_customer_l4l", "All Customers")
                cat_sel = sc.get("filter_category_l4l", "All Categories")
                if country_sel != "All Countries":
                    prev_for_analysis = prev_for_analysis[prev_for_analysis[cols_prev["Country"]] == country_sel]
                if cust_sel != "All Customers":
                    prev_for_analysis = prev_for_analysis[prev_for_analysis[cols_prev["Customer"]] == cust_sel]
                if cat_sel != "All Categories":
                    prev_for_analysis = prev_for_analysis[prev_for_analysis["Category Clean"] == cat_sel]
            # Render dashboard for current-year (L4L) using current-year columns
            render_dashboard(curr_for_analysis, df_curr_original, cols_curr, context_name="Current Year (L4L)")

# TAB: Full Year Analysis
with tab_full:
    st.header("Full Year Analysis (Previous Year vs Two Years Ago)")
    # Reset global filters when switching to this tab
    if st.session_state.main_view != "full":
        reset_global_filters()
        st.session_state.main_view = "full"

    if df_prev is None:
        st.info("Upload previous-year file to use Full Year analysis.")
    else:
        # Global filters applied to previous-year dataset
        filtered_prev = create_and_apply_filters(df_prev_original, cols_prev, prefix="full")
        # Render dashboard for previous year
        render_dashboard(filtered_prev, df_prev_original, cols_prev, context_name="Previous Year")

        # If two-years-ago file exists, allow side-by-side comparison
        if df_old is not None:
            st.markdown("### Compare with Two Years Ago")
            # Apply same filters to old dataset
            sc = st.session_state
            country_sel = sc.get("filter_country_full", "All Countries")
            cust_sel = sc.get("filter_customer_full", "All Customers")
            cat_sel = sc.get("filter_category_full", "All Categories")
            filtered_old = df_old_original.copy()
            if country_sel != "All Countries":
                filtered_old = filtered_old[filtered_old[cols_old["Country"]] == country_sel]
            if cust_sel != "All Customers":
                filtered_old = filtered_old[filtered_old[cols_old["Customer"]] == cust_sel]
            if cat_sel != "All Categories":
                filtered_old = filtered_old[filtered_old["Category Clean"] == cat_sel]
            # Render old dataset dashboard (separate)
            render_dashboard(filtered_old, df_old_original, cols_old, context_name="Two Years Ago")

# =========================
# END
# =========================
