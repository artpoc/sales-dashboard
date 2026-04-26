# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ================= CONFIG =================
DISPLAY_DECIMALS = 0  # 0 or 1
MONTHS_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# ================= HELPERS & CORE UTILS =================
def add_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

def to_decimal(x):
    """
    Robust conversion from Excel-like cell to Decimal.
    Handles:
      - None / NaN / empty / '-' -> 0
      - spaces and NBSP as thousand separators
      - comma as decimal separator
      - parentheses for negatives: (1 234) -> -1234
      - currency symbols (€, EUR, $, PLN, zł etc.)
      - stray characters
    Returns Decimal('0') on failure.
    """
    try:
        if x is None:
            return Decimal('0')
        if isinstance(x, Decimal):
            return x
        if isinstance(x, (int, float)):
            return Decimal(str(x))
        s = str(x).strip()
        if s == "" or s.lower() in {"nan", "none", "-"}:
            return Decimal('0')

        negative = False
        if s.startswith("(") and s.endswith(")"):
            negative = True
            s = s[1:-1].strip()

        # remove spaces (including NBSP) and unify decimal separator
        s = s.replace("\xa0", "").replace(" ", "")
        s = s.replace(",", ".")
        # remove currency letters/symbols and any non-digit/dot/minus
        s = re.sub(r"[^\d\.\-]", "", s)

        if s == "" or s == "." or s == "-":
            return Decimal('0')

        # If multiple dots, keep last as decimal separator
        if s.count(".") > 1:
            parts = s.split(".")
            s = "".join(parts[:-1]) + "." + parts[-1]

        val = Decimal(s)
        if negative:
            val = -val
        return val
    except (InvalidOperation, Exception):
        return Decimal('0')

def safe_decimal(d) -> Decimal:
    try:
        if isinstance(d, Decimal):
            return d
        return to_decimal(d)
    except Exception:
        return Decimal('0')

def decimal_sum(series: pd.Series) -> Decimal:
    """
    Sum a pandas Series robustly returning Decimal.
    Accepts series of mixed types (Decimal, float, str).
    """
    try:
        total = Decimal('0')
        for v in series.tolist():
            total += safe_decimal(v)
        return total
    except Exception:
        try:
            return Decimal(str(series.sum()))
        except Exception:
            return Decimal('0')

def format_number_plain(d, decimals: int = DISPLAY_DECIMALS) -> str:
    d = safe_decimal(d)
    try:
        if decimals == 0:
            q = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return f"{int(q):,}".replace(",", " ")
        q = d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        s = f"{q:.1f}"
        parts = s.split(".")
        parts[0] = f"{int(Decimal(parts[0])):,}".replace(",", " ")
        return ".".join(parts)
    except (InvalidOperation, Exception):
        try:
            return str(int(d))
        except Exception:
            return "0"

def calc_yoy_clean(new: Decimal, old: Decimal):
    new = safe_decimal(new)
    old = safe_decimal(old)
    try:
        if old < 0 and new == 0:
            return None
        if old == 0:
            return Decimal('100') if new > 0 else Decimal('0')
        if old > 0 and new == 0:
            return Decimal('-100')
        return (new - old) / abs(old) * Decimal('100')
    except (InvalidOperation, Exception):
        return None

def yoy_label(val, special: bool = False) -> str:
    if special:
        return "Recovery to 0 ⚠️"
    if val is None:
        return "0%"
    try:
        v = float(val)
    except Exception:
        return "0%"
    if v > 0:
        return f"+{v:.0f}% 🟢"
    if v < 0:
        return f"{v:.0f}% 🔴"
    return "0%"

def normalize_category(x: str) -> str:
    x = str(x).lower()
    if "napkin" in x:
        return "Napkins"
    if "hat" in x:
        return "Hats"
    if "banner" in x:
        return "Banner"
    if "straw" in x:
        return "Straws"
    if "bag" in x:
        return "Bags"
    if "plate" in x:
        return "Plates"
    if "paper cup" in x:
        return "Paper Cups"
    if "plastic cup" in x:
        return "Plastic Cups"
    if "tablecover" in x:
        return "Tablecover"
    if "reusable" in x:
        return "Reusable"
    if "foil" in x:
        return "Foil"
    if "wood" in x:
        return "Wooden"
    if "candle" in x:
        return "Candles"
    if "latex" in x:
        return "Latex"
    if "invitation" in x:
        return "Invitations"
    if "mask" in x:
        return "Masks"
    if "pinata" in x:
        return "Pinata"
    if "article" in x:
        return "Articles"
    return "Other"

ALLOWED_CATEGORIES = [
    "Napkins", "Hats", "Banner", "Straws", "Bags", "Plates", "Paper Cups",
    "Tablecover", "Reusable", "Foil", "Wooden", "Candles", "Latex",
    "Invitations", "Articles", "Masks", "Pinata", "Plastic Cups"
]

def sort_by_col(df: pd.DataFrame, col: str, ascending: bool = False) -> pd.DataFrame:
    """
    Sort df by column col. If column contains Decimal-like values, convert to float for sorting.
    ascending: True -> ascending, False -> descending
    """
    if col not in df.columns:
        return df
    try:
        return df.sort_values(by=col, ascending=ascending)
    except Exception:
        tmp = df.copy()
        try:
            tmp[col] = tmp[col].apply(lambda x: float(safe_decimal(x)))
            return tmp.sort_values(by=col, ascending=ascending)
        except Exception:
            return df

def extract_year_from_header(col_name: str) -> str:
    digits = "".join(ch for ch in str(col_name) if ch.isdigit())
    if digits:
        return digits
    return str(col_name)

# ================= DATA LOADING FOR SINGLE-YEAR FILES =================
def load_single_year_file(file, label: str):
    """
    Returns:
      cleaned_df, cols, year_name, raw_df
    cleaned_df: filtered and normalized (Category Clean etc.) used for category-limited analyses
    raw_df: original dataframe with numeric columns converted to Decimal but WITHOUT category filtering,
            used to compute totals that must match Excel 1:1
    """
    if file is None:
        return None, None, None, None

    df_raw = pd.read_excel(file, dtype=object, engine="openpyxl")
    df_raw.columns = df_raw.columns.str.strip()

    # detect columns in raw
    month_col = None
    for c in df_raw.columns:
        if str(c).strip().lower() == "month":
            month_col = c
            break
    if month_col is None:
        month_col = df_raw.columns[0]

    customer_col = None
    for c in df_raw.columns:
        if "customer" in str(c).lower():
            customer_col = c
            break
    if customer_col is None:
        customer_col = df_raw.columns[1] if len(df_raw.columns) > 1 else df_raw.columns[0]

    country_col = None
    for c in df_raw.columns:
        if "country" in str(c).lower():
            country_col = c
            break
    if country_col is None:
        country_col = df_raw.columns[2] if len(df_raw.columns) > 2 else df_raw.columns[0]

    code_col = None
    for c in df_raw.columns:
        if "art" in str(c).lower() and "nr" in str(c).lower():
            code_col = c
            break
    if code_col is None:
        # fallback: first column that looks like code
        code_col = df_raw.columns[4] if len(df_raw.columns) > 4 else df_raw.columns[0]

    desc_col = None
    for c in df_raw.columns:
        if "description" in str(c).lower():
            desc_col = c
            break
    if desc_col is None:
        desc_col = df_raw.columns[5] if len(df_raw.columns) > 5 else df_raw.columns[0]

    brand_col = None
    for c in df_raw.columns:
        if "brand" in str(c).lower():
            brand_col = c
            break
    if brand_col is None:
        brand_col = df_raw.columns[6] if len(df_raw.columns) > 6 else df_raw.columns[0]

    cat_col = None
    for c in df_raw.columns:
        if "category" in str(c).lower():
            cat_col = c
            break
    if cat_col is None:
        cat_col = df_raw.columns[7] if len(df_raw.columns) > 7 else df_raw.columns[0]

    net_col = None
    qty_col = None
    for c in df_raw.columns:
        cl = str(c).lower()
        if net_col is None and ("net" in cl or "value" in cl or "sales" in cl):
            net_col = c
        elif qty_col is None and ("qty" in cl or "quantity" in cl or "pcs" in cl):
            qty_col = c
    if net_col is None:
        net_col = df_raw.columns[-2] if len(df_raw.columns) >= 2 else df_raw.columns[-1]
    if qty_col is None:
        qty_col = df_raw.columns[-1]

    # Convert numeric columns in raw_df to Decimal (but keep all rows)
    df_raw[net_col] = df_raw[net_col].apply(to_decimal)
    df_raw[qty_col] = df_raw[qty_col].apply(to_decimal)

    # Ensure textual columns exist and are strings in raw_df
    for c in [month_col, customer_col, country_col, code_col, desc_col, brand_col, cat_col]:
        if c in df_raw.columns:
            df_raw[c] = df_raw[c].astype(str).fillna("").replace("nan", "")
        else:
            df_raw[c] = ""

    # Create cleaned df from raw for category-limited analyses
    df = df_raw.copy()
    df["Category Clean"] = df[cat_col].apply(normalize_category)
    # Keep only allowed categories for category-specific analyses (but raw_df still contains everything)
    df = df[df["Category Clean"].isin(ALLOWED_CATEGORIES)]
    df = df[df[desc_col].notna()]
    df = df[df[desc_col].str.lower() != "none"]

    year_name = extract_year_from_header(net_col)

    cols = {
        "YearName": year_name,
        "Month": month_col,
        "Customer": customer_col,
        "Country": country_col,
        "Code": code_col,
        "Desc": desc_col,
        "Brand": brand_col,
        "Cat": cat_col,
        "Net": net_col,
        "Qty": qty_col,
    }
    return df, cols, year_name, df_raw

# ================= FILTERS =================
def create_single_filters(df: pd.DataFrame, cols: dict, unique_prefix: str, df_raw: pd.DataFrame = None):
    """
    Filtry dla jednego datasetu:
    - Country
    - Customer (tylko z wybranego Country)
    - Category
    Returns filtered cleaned df and meta including raw filtered df for accurate totals.
    """
    if df is None or cols is None:
        return None, None

    df_all = df.copy()
    df_all_raw = df_raw.copy() if df_raw is not None else None

    # Countries list from raw if available (so customers list is correct)
    if df_all_raw is not None:
        countries = ["All Countries"] + sorted(df_all_raw[cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
    else:
        countries = ["All Countries"] + sorted(df_all[cols["Country"]].replace("", pd.NA).dropna().unique().tolist())

    key_country = f"{unique_prefix}_country"
    selected_country = st.selectbox("Country", countries, key=key_country)

    # For customers list use raw filtered by country if available
    df_for_customers = df_all_raw.copy() if df_all_raw is not None else df_all.copy()
    if selected_country != "All Countries":
        df_for_customers = df_for_customers[df_for_customers[cols["Country"]] == selected_country]

    customers = ["All Customers"] + sorted(df_for_customers[cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
    key_customer = f"{unique_prefix}_customer"
    selected_customer = st.selectbox("Customer", customers, key=key_customer)

    # Category list from df_for_customers normalized
    df_for_categories = df_for_customers.copy()
    df_for_categories["Category Clean"] = df_for_categories[cols["Cat"]].apply(normalize_category)
    categories = ["All Categories"] + sorted(df_for_categories["Category Clean"].dropna().unique().tolist())
    key_category = f"{unique_prefix}_category"
    selected_category = st.selectbox("Category", categories, key=key_category)

    # Apply filters to cleaned df (df_all) and to raw df (df_all_raw) for totals if needed
    df_filtered = df_all.copy()
    if selected_country != "All Countries":
        df_filtered = df_filtered[df_filtered[cols["Country"]] == selected_country]
    if selected_customer != "All Customers":
        df_filtered = df_filtered[df_filtered[cols["Customer"]] == selected_customer]
    if selected_category != "All Categories":
        df_filtered = df_filtered[df_filtered["Category Clean"] == selected_category]

    df_filtered_raw = None
    if df_all_raw is not None:
        df_filtered_raw = df_all_raw.copy()
        if selected_country != "All Countries":
            df_filtered_raw = df_filtered_raw[df_filtered_raw[cols["Country"]] == selected_country]
        if selected_customer != "All Customers":
            df_filtered_raw = df_filtered_raw[df_filtered_raw[cols["Customer"]] == selected_customer]
        if selected_category != "All Categories":
            df_filtered_raw = df_filtered_raw[df_filtered_raw[cols["Cat"]].apply(normalize_category) == selected_category]

    meta = {
        "country": selected_country,
        "customer": selected_customer,
        "category": selected_category,
        "df_all": df_all,
        "df_all_raw": df_all_raw,
        "df_filtered_raw": df_filtered_raw,
    }
    return df_filtered, meta

def apply_shared_filters(dfs, cols, unique_prefix: str, raw_dfs=None):
    """
    Shared filters for multiple years in one view (Overview, Detailed L4L):
    - Country
    - Customer (dependent on Country)
    - Category
    Returns list of filtered cleaned dfs and meta including filtered raw dfs for accurate totals.
    """
    if not dfs:
        return [], None

    df_all_combined = pd.concat(dfs, ignore_index=True)
    df_all_raw_combined = pd.concat(raw_dfs, ignore_index=True) if raw_dfs is not None else None

    if df_all_raw_combined is not None:
        countries = ["All Countries"] + sorted(df_all_raw_combined[cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
    else:
        countries = ["All Countries"] + sorted(df_all_combined[cols["Country"]].replace("", pd.NA).dropna().unique().tolist())

    key_country = f"{unique_prefix}_country"
    selected_country = st.selectbox("Country", countries, key=key_country)

    df_for_customers = df_all_raw_combined.copy() if df_all_raw_combined is not None else df_all_combined.copy()
    if selected_country != "All Countries":
        df_for_customers = df_for_customers[df_for_customers[cols["Country"]] == selected_country]

    customers = ["All Customers"] + sorted(df_for_customers[cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
    key_customer = f"{unique_prefix}_customer"
    selected_customer = st.selectbox("Customer", customers, key=key_customer)

    df_for_categories = df_for_customers.copy()
    df_for_categories["Category Clean"] = df_for_categories[cols["Cat"]].apply(normalize_category)
    categories = ["All Categories"] + sorted(df_for_categories["Category Clean"].dropna().unique().tolist())
    key_category = f"{unique_prefix}_category"
    selected_category = st.selectbox("Category", categories, key=key_category)

    filtered_dfs = []
    for df in dfs:
        d = df.copy()
        if selected_country != "All Countries":
            d = d[d[cols["Country"]] == selected_country]
        if selected_customer != "All Customers":
            d = d[d[cols["Customer"]] == selected_customer]
        if selected_category != "All Categories":
            d = d[d["Category Clean"] == selected_category]
        filtered_dfs.append(d)

    filtered_raws = []
    if df_all_raw_combined is not None:
        for raw in raw_dfs:
            r = raw.copy()
            if selected_country != "All Countries":
                r = r[r[cols["Country"]] == selected_country]
            if selected_customer != "All Customers":
                r = r[r[cols["Customer"]] == selected_customer]
            if selected_category != "All Categories":
                r = r[r[cols["Cat"]].apply(normalize_category) == selected_category]
            filtered_raws.append(r)
    else:
        filtered_raws = [None] * len(dfs)

    meta = {
        "country": selected_country,
        "customer": selected_customer,
        "category": selected_category,
        "df_all_combined": df_all_combined,
        "df_all_raw_combined": df_all_raw_combined,
        "filtered_raws": filtered_raws,
    }
    return filtered_dfs, meta

# ================= RENDER HELPERS =================
def safe_plotly_pie(df_plot, names_col, values_col, title, key):
    """Create pie chart and register unique key to avoid duplicate element id errors."""
    fig = px.pie(df_plot, names=names_col, values=values_col, title=title)
    st.plotly_chart(fig, use_container_width=True, key=key)

# ================= DASHBOARD RENDERING (TWO-YEAR L4L STYLE) =================
def render_two_year_dashboard(
    df_new: pd.DataFrame,
    df_old: pd.DataFrame,
    cols_new: dict,
    cols_old: dict,
    context_name: str,
    unique_prefix: str,
    category_filter: str = "All Categories",
    df_new_raw: pd.DataFrame = None,
    df_old_raw: pd.DataFrame = None,
):
    """
    df_new, df_old: cleaned filtered dfs (Category Clean applied)
    df_new_raw, df_old_raw: raw dfs (no category filtering) used to compute totals that must match Excel
    """
    if df_new is None or df_old is None:
        st.warning("No data for this view.")
        return

    net_new = cols_new["Net"]
    qty_new = cols_new["Qty"]
    net_old = cols_old["Net"]
    qty_old = cols_old["Qty"]
    code_col = cols_new["Code"]
    desc_col = cols_new["Desc"]
    brand_col = cols_new["Brand"]
    cust_col = cols_new["Customer"]

    year_new = cols_new["YearName"]
    year_old = cols_old["YearName"]

    # Use raw filtered dfs for KPI totals if provided (ensures 1:1 match with Excel)
    s_new = decimal_sum(df_new_raw[net_new]) if df_new_raw is not None else decimal_sum(df_new[net_new])
    s_old = decimal_sum(df_old_raw[net_old]) if df_old_raw is not None else decimal_sum(df_old[net_old])
    q_new = decimal_sum(df_new_raw[qty_new]) if df_new_raw is not None else decimal_sum(df_new[qty_new])
    q_old = decimal_sum(df_old_raw[qty_old]) if df_old_raw is not None else decimal_sum(df_old[qty_old])

    st.markdown(f"### KPI ({year_old} vs {year_new})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Net {year_old} (EUR)", format_number_plain(s_old))
    c2.metric(
        f"Net {year_new} (EUR)",
        format_number_plain(s_new),
        yoy_label(calc_yoy_clean(s_new, s_old)),
    )
    c3.metric(f"Qty {year_old} (PCS)", format_number_plain(q_old))
    c4.metric(
        f"Qty {year_new} (PCS)",
        format_number_plain(q_new),
        yoy_label(calc_yoy_clean(q_new, q_old)),
    )

    st.divider()

    # CATEGORY PERFORMANCE (tylko gdy nie wybrano konkretnej kategorii)
    if category_filter == "All Categories":
        st.markdown("### Category Performance")

        cat_new = df_new.groupby("Category Clean").agg({net_new: decimal_sum}).reset_index().rename(columns={net_new: f"Net {year_new}"})
        cat_old = df_old.groupby("Category Clean").agg({net_old: decimal_sum}).reset_index().rename(columns={net_old: f"Net {year_old}"})
        cat = pd.merge(cat_new, cat_old, on="Category Clean", how="outer").fillna(Decimal('0'))

        cat[f"YoY {year_new} vs {year_old}"] = cat.apply(lambda x: calc_yoy_clean(x[f"Net {year_new}"], x[f"Net {year_old}"]), axis=1)
        cat["YoY %"] = cat[f"YoY {year_new} vs {year_old}"].apply(yoy_label)

        cat = sort_by_col(cat, f"Net {year_new}", ascending=False)

        plot_cat = cat.copy()
        plot_cat[f"Net {year_new}"] = plot_cat[f"Net {year_new}"].apply(lambda v: float(safe_decimal(v)))
        plot_cat[f"Net {year_old}"] = plot_cat[f"Net {year_old}"].apply(lambda v: float(safe_decimal(v)))

        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown(f"#### Category Pie {year_old}")
            safe_plotly_pie(plot_cat, "Category Clean", f"Net {year_old}", f"Category Pie {year_old}", key=f"{unique_prefix}_catpie_old")
        with pc2:
            st.markdown(f"#### Category Pie {year_new}")
            safe_plotly_pie(plot_cat, "Category Clean", f"Net {year_new}", f"Category Pie {year_new}", key=f"{unique_prefix}_catpie_new")

        cat_display = cat.copy()
        cat_display[f"Net {year_old}"] = cat_display[f"Net {year_old}"].apply(format_number_plain)
        cat_display[f"Net {year_new}"] = cat_display[f"Net {year_new}"].apply(format_number_plain)
        st.dataframe(add_index(cat_display[["Category Clean", f"Net {year_old}", f"Net {year_new}", "YoY %"]]))

        st.divider()

    # BRAND PERFORMANCE
    st.markdown("### Brand Performance")

    brand_new = df_new.groupby(brand_col).agg({net_new: decimal_sum}).reset_index().rename(columns={net_new: f"Net {year_new}"})
    brand_old = df_old.groupby(brand_col).agg({net_old: decimal_sum}).reset_index().rename(columns={net_old: f"Net {year_old}"})
    brand = pd.merge(brand_new, brand_old, on=brand_col, how="outer").fillna(Decimal('0'))

    brand[f"YoY {year_new} vs {year_old}"] = brand.apply(lambda x: calc_yoy_clean(x[f"Net {year_new}"], x[f"Net {year_old}"]), axis=1)
    brand["YoY %"] = brand[f"YoY {year_new} vs {year_old}"].apply(yoy_label)

    brand = sort_by_col(brand, f"Net {year_new}", ascending=False)

    bplot = brand.copy()
    bplot[f"Net {year_old}"] = bplot[f"Net {year_old}"].apply(lambda v: float(safe_decimal(v)))
    bplot[f"Net {year_new}"] = bplot[f"Net {year_new}"].apply(lambda v: float(safe_decimal(v)))

    bc1, bc2 = st.columns(2)
    with bc1:
        st.markdown(f"#### Brand Pie {year_old}")
        safe_plotly_pie(bplot, brand_col, f"Net {year_old}", f"Brand Pie {year_old}", key=f"{unique_prefix}_brandpie_old")
    with bc2:
        st.markdown(f"#### Brand Pie {year_new}")
        safe_plotly_pie(bplot, brand_col, f"Net {year_new}", f"Brand Pie {year_new}", key=f"{unique_prefix}_brandpie_new")

    brand_display = brand.copy()
    brand_display[f"Net {year_old}"] = brand_display[f"Net {year_old}"].apply(format_number_plain)
    brand_display[f"Net {year_new}"] = brand_display[f"Net {year_new}"].apply(format_number_plain)
    st.dataframe(add_index(brand_display[[brand_col, f"Net {year_old}", f"Net {year_new}", "YoY %"]]))

    st.divider()

    # TOP PRODUCTS (aggregated by product code)
    st.markdown("### Top Products (aggregated by Product Code)")

    if df_new.empty and df_old.empty:
        st.info("No data for selected filters.")
    else:
        base_new = df_new.copy()
        base_old = df_old.copy()

        t1, t2 = st.columns(2)

        with t1:
            st.write(f"#### Top 10 by Net {year_old}")
            d_old = base_old.groupby(code_col).agg({desc_col: "first", net_old: decimal_sum, qty_old: decimal_sum}).reset_index()
            d_old = d_old[d_old[net_old].apply(lambda x: safe_decimal(x) > 0)]
            d_old = sort_by_col(d_old, net_old, ascending=False)
            if d_old.empty:
                st.info("No sales in older year.")
            else:
                top_old = d_old.head(10)
                total_old_val = decimal_sum(d_old[net_old])
                if total_old_val == 0:
                    top_old["Share %"] = Decimal('0')
                else:
                    top_old["Share %"] = top_old[net_old].apply(lambda x: safe_decimal(x) / total_old_val * Decimal('100'))
                disp_old = top_old.copy()
                disp_old[net_old] = disp_old[net_old].apply(format_number_plain)
                disp_old[qty_old] = disp_old[qty_old].apply(format_number_plain)
                disp_old["Share %"] = disp_old["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
                st.dataframe(add_index(disp_old[[code_col, desc_col, net_old, qty_old, "Share %"]]))
                try:
                    share_top = decimal_sum(top_old[net_old]) / total_old_val * Decimal('100')
                except (InvalidOperation, Exception):
                    share_top = Decimal('0')
                st.write(f"Top 10 share: {format_number_plain(share_top)}%")

        with t2:
            st.write(f"#### Top 10 by Net {year_new}")
            d_new = base_new.groupby(code_col).agg({desc_col: "first", net_new: decimal_sum, qty_new: decimal_sum}).reset_index()
            d_new = d_new[d_new[net_new].apply(lambda x: safe_decimal(x) > 0)]
            d_new = sort_by_col(d_new, net_new, ascending=False)
            if d_new.empty:
                st.info("No sales in newer year.")
            else:
                top_new = d_new.head(10)
                total_new_val = decimal_sum(d_new[net_new])
                if total_new_val == 0:
                    top_new["Share %"] = Decimal('0')
                else:
                    top_new["Share %"] = top_new[net_new].apply(lambda x: safe_decimal(x) / total_new_val * Decimal('100'))
                disp_new = top_new.copy()
                disp_new[net_new] = disp_new[net_new].apply(format_number_plain)
                disp_new[qty_new] = disp_new[qty_new].apply(format_number_plain)
                disp_new["Share %"] = disp_new["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
                st.dataframe(add_index(disp_new[[code_col, desc_col, net_new, qty_new, "Share %"]]))
                try:
                    share_top_n = decimal_sum(top_new[net_new]) / total_new_val * Decimal('100')
                except (InvalidOperation, Exception):
                    share_top_n = Decimal('0')
                st.write(f"Top 10 share: {format_number_plain(share_top_n)}%")

    st.divider()

    # PARETO
    st.markdown("### Pareto Analysis")
    ptab = st.tabs([year_old, year_new])
    for tab, year, df_src, net_col, raw_src in zip(
        ptab,
        [year_old, year_new],
        [df_old, df_new],
        [net_old, net_new],
        [df_old_raw, df_new_raw],
    ):
        with tab:
            p = df_src.groupby(code_col).agg({desc_col: "first", "Category Clean": "first", net_col: decimal_sum}).reset_index()
            # include only SKUs with positive value
            p = p[p[net_col].apply(lambda x: safe_decimal(x) > 0)]
            if p.empty:
                st.info("No sales in this period.")
            else:
                p = sort_by_col(p, net_col, ascending=False)
                p["cum_value"] = p[net_col].cumsum()
                total_value = decimal_sum(p[net_col])
                if total_value == 0:
                    st.info("Total value is zero.")
                else:
                    p["cum_share"] = p["cum_value"].apply(lambda x: safe_decimal(x) / total_value)
                    top80 = p[p["cum_share"] <= Decimal('0.8')]
                    total_sku = p[code_col].nunique()
                    pareto_sku = top80[code_col].nunique()
                    sku_share = (Decimal(pareto_sku) / Decimal(total_sku) * Decimal('100')) if total_sku > 0 else Decimal('0')
                    st.write(f"Top SKU for 80%: {pareto_sku} / {total_sku} ({format_number_plain(sku_share)}% of SKU)")
                    p_display = top80[[code_col, desc_col, "Category Clean", net_col]].copy()
                    p_display[net_col] = p_display[net_col].apply(format_number_plain)
                    st.dataframe(add_index(p_display))

    st.divider()

    # ABC
    st.markdown("### ABC Analysis")
    atab = st.tabs([year_old, year_new])
    for tab, year, df_src, net_col in zip(
        atab,
        [year_old, year_new],
        [df_old, df_new],
        [net_old, net_new],
    ):
        with tab:
            a = df_src.groupby(code_col).agg({desc_col: "first", net_col: decimal_sum}).reset_index()
            a = a[a[net_col].apply(lambda x: safe_decimal(x) > 0)]
            if a.empty:
                st.info("No sales in this period.")
            else:
                a = sort_by_col(a, net_col, ascending=False).reset_index(drop=True)
                total_val = decimal_sum(a[net_col])
                if total_val == 0:
                    st.info("Total is zero.")
                else:
                    a["cum"] = a[net_col].cumsum().apply(lambda x: safe_decimal(x) / total_val)
                    a["segment"] = "C"
                    a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
                    a.loc[(a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')), "segment"] = "B"
                    seg_counts = a["segment"].value_counts()
                    st.write(f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}")
                    a_disp = a[[code_col, desc_col, net_col, "segment"]].copy()
                    a_disp[net_col] = a_disp[net_col].apply(format_number_plain)
                    st.dataframe(add_index(a_disp))

    st.divider()

    # L4L TABLE (aggregated by product code)
    st.markdown("### L4L Table")
    yoy_df_new = df_new.groupby(code_col).agg({desc_col: "first", net_new: decimal_sum, qty_new: decimal_sum}).reset_index()
    yoy_df_old = df_old.groupby(code_col).agg({net_old: decimal_sum, qty_old: decimal_sum}).reset_index()
    yoy = pd.merge(yoy_df_new, yoy_df_old, on=code_col, how="outer").fillna(Decimal('0'))
    yoy["YoY"] = yoy.apply(lambda x: calc_yoy_clean(x[net_new], x[net_old]), axis=1)
    yoy["YoY %"] = yoy["YoY"].apply(yoy_label)
    # default sort: newer year descending
    yoy = sort_by_col(yoy, net_new, ascending=False)

    yoy_disp = yoy.copy()
    yoy_disp[net_old] = yoy_disp[net_old].apply(format_number_plain)
    yoy_disp[net_new] = yoy_disp[net_new].apply(format_number_plain)
    yoy_disp[qty_old] = yoy_disp[qty_old].apply(format_number_plain)
    yoy_disp[qty_new] = yoy_disp[qty_new].apply(format_number_plain)

    st.dataframe(add_index(yoy_disp[[code_col, desc_col, net_old, net_new, qty_old, qty_new, "YoY %"]]))

    st.divider()

    # AUTO INSIGHTS (TOP 5, GROWTH, RISK)
    st.markdown("### Auto Insights")

    cat_new_ins = df_new.groupby("Category Clean").agg({net_new: decimal_sum}).reset_index().rename(columns={net_new: f"Net {year_new}"})
    cat_old_ins = df_old.groupby("Category Clean").agg({net_old: decimal_sum}).reset_index().rename(columns={net_old: f"Net {year_old}"})
    cat_ins = pd.merge(cat_new_ins, cat_old_ins, on="Category Clean", how="outer").fillna(Decimal('0'))
    cat_ins["YoY"] = cat_ins.apply(lambda x: calc_yoy_clean(x[f"Net {year_new}"], x[f"Net {year_old}"]), axis=1)
    cat_ins["YoY %"] = cat_ins["YoY"].apply(yoy_label)
    cat_ins = sort_by_col(cat_ins, f"Net {year_new}", ascending=False)

    st.write("#### Top 5 Categories")
    ic1, ic2 = st.columns(2)
    with ic1:
        top_old_cat = cat_ins.sort_values(f"Net {year_old}", ascending=False).head(5)
        disp_old_cat = top_old_cat.copy()
        disp_old_cat[f"Net {year_old}"] = disp_old_cat[f"Net {year_old}"].apply(format_number_plain)
        st.dataframe(add_index(disp_old_cat[["Category Clean", f"Net {year_old}"]]))
    with ic2:
        top_new_cat = cat_ins.sort_values(f"Net {year_new}", ascending=False).head(5)
        disp_new_cat = top_new_cat.copy()
        disp_new_cat[f"Net {year_new}"] = disp_new_cat[f"Net {year_new}"].apply(format_number_plain)
        st.dataframe(add_index(disp_new_cat[["Category Clean", f"Net {year_new}", "YoY %"]]))

    st.write("#### Top 5 Growth (L4L)")
    growth = cat_ins[cat_ins["YoY"] > 0].sort_values("YoY", ascending=False).head(5)
    if growth.empty:
        st.info("There is no growth in categories.")
    else:
        g_disp = growth.copy()
        g_disp[f"Net {year_old}"] = g_disp[f"Net {year_old}"].apply(format_number_plain)
        g_disp[f"Net {year_new}"] = g_disp[f"Net {year_new}"].apply(format_number_plain)
        st.dataframe(add_index(g_disp[["Category Clean", f"Net {year_old}", f"Net {year_new}", "YoY %"]]))

    st.write("#### Top 5 Risk")
    risk = cat_ins[cat_ins["YoY"] < 0].sort_values("YoY").head(5)
    if risk.empty:
        st.success("There is no risk in categories.")
    else:
        r_disp = risk.copy()
        r_disp[f"Net {year_old}"] = r_disp[f"Net {year_old}"].apply(format_number_plain)
        r_disp[f"Net {year_new}"] = r_disp[f"Net {year_new}"].apply(format_number_plain)
        st.dataframe(add_index(r_disp[["Category Clean", f"Net {year_old}", f"Net {year_new}", "YoY %"]]))

    st.divider()

    # CUSTOMER IMPACT
    st.markdown("### Customer Impact (Growth vs Decline)")

    all_categories = sorted(df_new["Category Clean"].dropna().unique().tolist() + df_old["Category Clean"].dropna().unique().tolist())
    all_categories = sorted(list(set(all_categories)))
    all_brands = sorted(df_new[brand_col].dropna().unique().tolist() + df_old[brand_col].dropna().unique().tolist())
    all_brands = sorted(list(set(all_brands)))

    sel_cat_imp = st.selectbox("Category for Impact Analysis", ["All Categories"] + all_categories, key=f"{unique_prefix}_impact_cat")
    sel_brand_imp = st.selectbox("Brand (License) for Impact Analysis", ["All Brands"] + all_brands, key=f"{unique_prefix}_impact_brand")

    df_imp_new = df_new.copy()
    df_imp_old = df_old.copy()
    if sel_cat_imp != "All Categories":
        df_imp_new = df_imp_new[df_imp_new["Category Clean"] == sel_cat_imp]
        df_imp_old = df_imp_old[df_imp_old["Category Clean"] == sel_cat_imp]
    if sel_brand_imp != "All Brands":
        df_imp_new = df_imp_new[df_imp_new[brand_col] == sel_brand_imp]
        df_imp_old = df_imp_old[df_imp_old[brand_col] == sel_brand_imp]

    cust_new = df_imp_new.groupby(cust_col).agg({net_new: decimal_sum}).reset_index().rename(columns={net_new: f"Net {year_new}"})
    cust_old = df_imp_old.groupby(cust_col).agg({net_old: decimal_sum}).reset_index().rename(columns={net_old: f"Net {year_old}"})
    impact = pd.merge(cust_new, cust_old, on=cust_col, how="outer").fillna(Decimal('0'))
    impact["Change Value"] = impact[f"Net {year_new}"] - impact[f"Net {year_old}"]
    impact["Special Case"] = ((impact[f"Net {year_old}"] < 0) & (impact[f"Net {year_new}"] == 0))
    impact["YoY"] = impact.apply(lambda x: calc_yoy_clean(x[f"Net {year_new}"], x[f"Net {year_old}"]), axis=1)
    impact["YoY %"] = impact.apply(lambda x: yoy_label(x["YoY"], x["Special Case"]), axis=1)

    st.write("#### Top Growth Drivers")
    growth_imp = impact[(impact["Change Value"] > 0) & (~impact["Special Case"])].sort_values("Change Value", ascending=False).head(10)
    growth_special = impact[impact["Special Case"]].head(10)
    growth_imp = pd.concat([growth_imp, growth_special])
    if growth_imp.empty:
        st.info("No growth generated by customers.")
    else:
        g_disp = growth_imp.copy()
        g_disp[f"Net {year_old}"] = g_disp[f"Net {year_old}"].apply(format_number_plain)
        g_disp[f"Net {year_new}"] = g_disp[f"Net {year_new}"].apply(format_number_plain)
        g_disp["Change Value"] = g_disp["Change Value"].apply(format_number_plain)
        st.dataframe(add_index(g_disp[[cust_col, f"Net {year_old}", f"Net {year_new}", "Change Value", "YoY %"]]))

    st.write("#### Top Decline Drivers")
    decline_imp = impact[impact["Change Value"] < 0].sort_values("Change Value").head(10)
    decline_special = impact[impact["Special Case"]].head(10)
    decline_imp = pd.concat([decline_imp, decline_special])
    if decline_imp.empty:
        st.success("No decline across customers.")
    else:
        d_disp = decline_imp.copy()
        d_disp[f"Net {year_old}"] = d_disp[f"Net {year_old}"].apply(format_number_plain)
        d_disp[f"Net {year_new}"] = d_disp[f"Net {year_new}"].apply(format_number_plain)
        d_disp["Change Value"] = d_disp["Change Value"].apply(format_number_plain)
        st.dataframe(add_index(d_disp[[cust_col, f"Net {year_old}", f"Net {year_new}", "Change Value", "YoY %"]]))

# ================= DASHBOARD FOR SINGLE YEAR (FULL YEAR ANALYSIS) =================
def render_single_year_dashboard(df: pd.DataFrame, cols: dict, year_name: str, unique_prefix: str, category_filter: str, df_raw: pd.DataFrame = None):
    """
    df: cleaned filtered df (Category Clean applied)
    df_raw: raw filtered df (no category filtering) used to compute totals that must match Excel
    """
    if df is None or cols is None:
        st.warning("No data for this view.")
        return

    net_col = cols["Net"]
    qty_col = cols["Qty"]
    code_col = cols["Code"]
    desc_col = cols["Desc"]
    brand_col = cols["Brand"]

    # Use raw totals for KPI if available (to match Excel 1:1), otherwise use cleaned df
    s_net = decimal_sum(df_raw[net_col]) if df_raw is not None else decimal_sum(df[net_col])
    s_qty = decimal_sum(df_raw[qty_col]) if df_raw is not None else decimal_sum(df[qty_col])

    st.markdown(f"### KPI ({year_name})")
    c1, c2 = st.columns(2)
    c1.metric(f"Net {year_name} (EUR)", format_number_plain(s_net))
    c2.metric(f"Qty {year_name} (PCS)", format_number_plain(s_qty))

    st.divider()

    # CATEGORY PERFORMANCE (tylko gdy All Categories)
    if category_filter == "All Categories":
        st.markdown("### Category Performance")
        cat = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index().rename(columns={net_col: f"Net {year_name}"})
        cat = sort_by_col(cat, f"Net {year_name}", ascending=False)
        plot_cat = cat.copy()
        plot_cat[f"Net {year_name}"] = plot_cat[f"Net {year_name}"].apply(lambda v: float(safe_decimal(v)))

        st.markdown(f"#### Category Pie {year_name}")
        safe_plotly_pie(plot_cat, "Category Clean", f"Net {year_name}", f"Category Pie {year_name}", key=f"{unique_prefix}_full_catpie_{year_name}")

        cat_disp = cat.copy()
        cat_disp[f"Net {year_name}"] = cat_disp[f"Net {year_name}"].apply(format_number_plain)
        st.dataframe(add_index(cat_disp[["Category Clean", f"Net {year_name}"]]))

        st.divider()

    # BRAND PERFORMANCE
    st.markdown("### Brand Performance")
    brand = df.groupby(brand_col).agg({net_col: decimal_sum}).reset_index().rename(columns={net_col: f"Net {year_name}"})
    brand = sort_by_col(brand, f"Net {year_name}", ascending=False)
    bplot = brand.copy()
    bplot[f"Net {year_name}"] = bplot[f"Net {year_name}"].apply(lambda v: float(safe_decimal(v)))

    st.markdown(f"#### Brand Pie {year_name}")
    safe_plotly_pie(bplot, brand_col, f"Net {year_name}", f"Brand Pie {year_name}", key=f"{unique_prefix}_full_brandpie_{year_name}")

    brand_disp = brand.copy()
    brand_disp[f"Net {year_name}"] = brand_disp[f"Net {year_name}"].apply(format_number_plain)
    st.dataframe(add_index(brand_disp[[brand_col, f"Net {year_name}"]]))

    st.divider()

    # TOP PRODUCTS
    st.markdown("### Top Products (aggregated by Product Code)")
    if df.empty:
        st.info("No data for selected filters.")
    else:
        d = df.groupby(code_col).agg({desc_col: "first", net_col: decimal_sum, qty_col: decimal_sum}).reset_index()
        d = d[d[net_col].apply(lambda x: safe_decimal(x) > 0)]
        d = sort_by_col(d, net_col, ascending=False)
        if d.empty:
            st.info("No sales.")
        else:
            top = d.head(10)
            total_val = decimal_sum(d[net_col])
            if total_val == 0:
                top["Share %"] = Decimal('0')
            else:
                top["Share %"] = top[net_col].apply(lambda x: safe_decimal(x) / total_val * Decimal('100'))
            disp = top.copy()
            disp[net_col] = disp[net_col].apply(format_number_plain)
            disp[qty_col] = disp[qty_col].apply(format_number_plain)
            disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
            st.dataframe(add_index(disp[[code_col, desc_col, net_col, qty_col, "Share %"]]))

    st.divider()

    # PARETO
    st.markdown("### Pareto Analysis")
    p = df.groupby(code_col).agg({desc_col: "first", "Category Clean": "first", net_col: decimal_sum}).reset_index()
    p = p[p[net_col].apply(lambda x: safe_decimal(x) > 0)]
    if p.empty:
        st.info("No sales.")
    else:
        p = sort_by_col(p, net_col, ascending=False)
        p["cum_value"] = p[net_col].cumsum()
        total_val = decimal_sum(p[net_col])
        if total_val == 0:
            st.info("Total value is zero.")
        else:
            p["cum_share"] = p["cum_value"].apply(lambda x: safe_decimal(x) / total_val)
            top80 = p[p["cum_share"] <= Decimal('0.8')]
            total_sku = p[code_col].nunique()
            pareto_sku = top80[code_col].nunique()
            sku_share = (Decimal(pareto_sku) / Decimal(total_sku) * Decimal('100')) if total_sku > 0 else Decimal('0')
            st.write(f"Top SKU for 80%: {pareto_sku} / {total_sku} ({format_number_plain(sku_share)}% of SKU)")
            p_disp = top80[[code_col, desc_col, "Category Clean", net_col]].copy()
            p_disp[net_col] = p_disp[net_col].apply(format_number_plain)
            st.dataframe(add_index(p_disp))

    st.divider()

    # ABC
    st.markdown("### ABC Analysis")
    a = df.groupby(code_col).agg({desc_col: "first", net_col: decimal_sum}).reset_index()
    a = a[a[net_col].apply(lambda x: safe_decimal(x) > 0)]
    if a.empty:
        st.info("No sales.")
    else:
        a = sort_by_col(a, net_col, ascending=False).reset_index(drop=True)
        total_val = decimal_sum(a[net_col])
        if total_val == 0:
            st.info("Total is zero.")
        else:
            a["cum"] = a[net_col].cumsum().apply(lambda x: safe_decimal(x) / total_val)
            a["segment"] = "C"
            a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
            a.loc[(a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')), "segment"] = "B"
            seg_counts = a["segment"].value_counts()
            st.write(f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}")
            a_disp = a[[code_col, desc_col, net_col, "segment"]].copy()
            a_disp[net_col] = a_disp[net_col].apply(format_number_plain)
            st.dataframe(add_index(a_disp))

    st.divider()

    # AUTO INSIGHTS (Top 5 Categories)
    st.markdown("### Auto Insights")
    cat_ins = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index().rename(columns={net_col: f"Net {year_name}"})
    cat_ins = sort_by_col(cat_ins, f"Net {year_name}", ascending=False)
    st.write("#### Top 5 Categories")
    top5 = cat_ins.head(5)
    disp = top5.copy()
    disp[f"Net {year_name}"] = disp[f"Net {year_name}"].apply(format_number_plain)
    st.dataframe(add_index(disp[["Category Clean", f"Net {year_name}"]]))

# ================= MAIN APP =================
st.set_page_config(layout="wide", page_title="Sales Intelligence Dashboard")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha")

st.markdown("### Excel Upload (3 separate years)")
c_up1, c_up2, c_up3 = st.columns(3)
with c_up1:
    file_two_years_ago = st.file_uploader("Older Year (2 years ago)", type=["xlsx"], key="upload_old2")
with c_up2:
    file_prev_year = st.file_uploader("Previous Year", type=["xlsx"], key="upload_prev")
with c_up3:
    file_current_year = st.file_uploader("Current Year (YTD)", type=["xlsx"], key="upload_curr")

if not file_prev_year and not file_current_year and not file_two_years_ago:
    st.info("Upload at least one Excel file.")
    st.stop()

# Load files: each returns cleaned df, cols, year_name, raw_df
df_old2, cols_old2, year_old2, df_old2_raw = load_single_year_file(file_two_years_ago, "older") if file_two_years_ago else (None, None, None, None)
df_prev, cols_prev, year_prev, df_prev_raw = load_single_year_file(file_prev_year, "prev") if file_prev_year else (None, None, None, None)
df_curr, cols_curr, year_curr, df_curr_raw = load_single_year_file(file_current_year, "curr") if file_current_year else (None, None, None, None)

st.divider()

tab_overview, tab_l4l, tab_full = st.tabs(
    [
        "📈 Overview — 3-year Like-for-Like",
        "📅 Detailed Like-for-Like",
        "📊 Full Year Analysis",
    ]
)

# ================= OVERVIEW: 3-YEAR L4L =================
with tab_overview:
    st.header("Overview — 3-year Like-for-Like")

    if df_prev is None or df_curr is None:
        st.warning("For 3-year L4L you need at least Current Year and Previous Year files.")
    else:
        months_curr = sorted(df_curr[cols_curr["Month"]].dropna().unique().tolist(), key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
        months_prev = sorted(df_prev[cols_prev["Month"]].dropna().unique().tolist(), key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
        common_months = [m for m in months_curr if m in months_prev]
        if df_old2 is not None:
            months_old2 = sorted(df_old2[cols_old2["Month"]].dropna().unique().tolist(), key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
            common_months = [m for m in common_months if m in months_old2]

        st.info(f"Detected common months for L4L: {', '.join(common_months)}" if common_months else "No common months detected.")

        selected_months = st.multiselect("Select months for 3-year L4L", MONTHS_ORDER, default=common_months, key="overview_months")

        if not selected_months:
            st.info("Select at least one month.")
        else:
            missing_curr = [m for m in selected_months if m not in df_curr[cols_curr["Month"]].unique().tolist()]
            missing_prev = [m for m in selected_months if m not in df_prev[cols_prev["Month"]].unique().tolist()]
            missing_old2 = []
            if df_old2 is not None:
                missing_old2 = [m for m in selected_months if m not in df_old2[cols_old2["Month"]].unique().tolist()]

            if missing_curr:
                st.error(f"Selected months exceed Current Year data: {', '.join(missing_curr)}")
            elif missing_prev:
                st.error(f"Selected months exceed Previous Year data: {', '.join(missing_prev)}")
            elif df_old2 is not None and missing_old2:
                st.error(f"Selected months exceed 2 Years Ago data: {', '.join(missing_old2)}")
            else:
                # Filter raw dfs by months for accurate totals
                df_curr_ytd_raw = df_curr_raw[df_curr_raw[cols_curr["Month"]].isin(selected_months)] if df_curr_raw is not None else None
                df_prev_ytd_raw = df_prev_raw[df_prev_raw[cols_prev["Month"]].isin(selected_months)] if df_prev_raw is not None else None
                df_old2_ytd_raw = df_old2_raw[df_old2_raw[cols_old2["Month"]].isin(selected_months)] if df_old2_raw is not None else None

                # Filter cleaned dfs by months for analyses
                df_curr_ytd = df_curr[df_curr[cols_curr["Month"]].isin(selected_months)]
                df_prev_ytd = df_prev[df_prev[cols_prev["Month"]].isin(selected_months)]
                df_old2_ytd = df_old2[df_old2[cols_old2["Month"]].isin(selected_months)] if df_old2 is not None else None

                val_curr = decimal_sum(df_curr_ytd_raw[cols_curr["Net"]]) if df_curr_ytd_raw is not None else decimal_sum(df_curr_ytd[cols_curr["Net"]])
                val_prev = decimal_sum(df_prev_ytd_raw[cols_prev["Net"]]) if df_prev_ytd_raw is not None else decimal_sum(df_prev_ytd[cols_prev["Net"]])
                val_old2 = decimal_sum(df_old2_ytd_raw[cols_old2["Net"]]) if (df_old2_ytd_raw is not None) else Decimal('0')

                c1, c2, c3 = st.columns(3)
                c1.metric(f"Net {year_old2} (EUR)" if df_old2 else "Net older (EUR)", format_number_plain(val_old2))
                c2.metric(f"Net {year_prev} (EUR)", format_number_plain(val_prev), yoy_label(calc_yoy_clean(val_prev, val_old2)) if df_old2 is not None else None)
                c3.metric(f"Net {year_curr} (EUR)", format_number_plain(val_curr), yoy_label(calc_yoy_clean(val_curr, val_prev)))

                chart_data = pd.DataFrame({
                    "Year": [year_old2 if df_old2 else "Older", year_prev, year_curr],
                    "Net": [float(safe_decimal(val_old2)), float(safe_decimal(val_prev)), float(safe_decimal(val_curr))]
                })
                st.plotly_chart(px.bar(chart_data, x="Year", y="Net", text="Net", title="3-year L4L Net"), use_container_width=True)

                st.divider()

                st.markdown("### Global Filters (Overview)")
                dfs_for_filters = [df_prev_ytd, df_curr_ytd]
                raw_for_filters = [df_prev_ytd_raw, df_curr_ytd_raw]
                if df_old2_ytd is not None:
                    dfs_for_filters.append(df_old2_ytd)
                    raw_for_filters.append(df_old2_ytd_raw)

                filtered_list, meta = apply_shared_filters(dfs_for_filters, cols_prev, unique_prefix="overview", raw_dfs=raw_for_filters)

                # Unpack filtered cleaned dfs and raw dfs
                if df_old2_ytd is not None:
                    df_prev_f, df_curr_f, df_old2_f = filtered_list
                    df_prev_f_raw, df_curr_f_raw, df_old2_f_raw = meta["filtered_raws"]
                else:
                    df_prev_f, df_curr_f = filtered_list
                    df_prev_f_raw, df_curr_f_raw = meta["filtered_raws"]
                    df_old2_f, df_old2_f_raw = None, None

                st.markdown("### Detailed L4L (Previous vs Current) — Overview")
                render_two_year_dashboard(
                    df_new=df_curr_f,
                    df_old=df_prev_f,
                    cols_new=cols_curr,
                    cols_old=cols_prev,
                    context_name="overview_l4l",
                    unique_prefix="overview_l4l",
                    category_filter=meta["category"],
                    df_new_raw=df_curr_f_raw,
                    df_old_raw=df_prev_f_raw,
                )

# ================= DETAILED L4L =================
with tab_l4l:
    st.header("Detailed Like-for-Like")

    year_options = []
    year_to_df = {}
    year_to_cols = {}
    year_to_raw = {}

    if df_old2 is not None:
        year_options.append(year_old2)
        year_to_df[year_old2] = df_old2
        year_to_cols[year_old2] = cols_old2
        year_to_raw[year_old2] = df_old2_raw
    if df_prev is not None:
        year_options.append(year_prev)
        year_to_df[year_prev] = df_prev
        year_to_cols[year_prev] = cols_prev
        year_to_raw[year_prev] = df_prev_raw
    if df_curr is not None:
        year_options.append(year_curr)
        year_to_df[year_curr] = df_curr
        year_to_cols[year_curr] = cols_curr
        year_to_raw[year_curr] = df_curr_raw

    if len(year_options) < 2:
        st.warning("Detailed L4L requires at least two year files.")
    else:
        st.markdown("#### Select years (older on the left, newer on the right)")
        # Ensure older on left, newer on right in UI
        left_year_option = st.selectbox("Older year", year_options, index=0, key="l4l_left_year")
        right_year_option = st.selectbox("Newer year", year_options, index=1 if len(year_options) > 1 else 0, key="l4l_right_year")

        if left_year_option == right_year_option:
            st.error("Older year and newer year must be different.")
        else:
            df_left = year_to_df[left_year_option]
            cols_left = year_to_cols[left_year_option]
            df_left_raw = year_to_raw[left_year_option]
            df_right = year_to_df[right_year_option]
            cols_right = year_to_cols[right_year_option]
            df_right_raw = year_to_raw[right_year_option]

            months_left = sorted(df_left[cols_left["Month"]].dropna().unique().tolist(), key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
            months_right = sorted(df_right[cols_right["Month"]].dropna().unique().tolist(), key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
            common_months = [m for m in months_left if m in months_right]

            st.info(f"Detected common months: {', '.join(common_months)}" if common_months else "No common months detected.")

            selected_months_l4l = st.multiselect("Select months for L4L", MONTHS_ORDER, default=common_months, key="detailed_l4l_months")

            if not selected_months_l4l:
                st.info("Select at least one month.")
            else:
                missing_left = [m for m in selected_months_l4l if m not in df_left[cols_left["Month"]].unique().tolist()]
                missing_right = [m for m in selected_months_l4l if m not in df_right[cols_right["Month"]].unique().tolist()]
                if missing_left:
                    st.error(f"Selected months exceed data for older year: {', '.join(missing_left)}")
                elif missing_right:
                    st.error(f"Selected months exceed data for newer year: {', '.join(missing_right)}")
                else:
                    df_left_l4l = df_left[df_left[cols_left["Month"]].isin(selected_months_l4l)]
                    df_right_l4l = df_right[df_right[cols_right["Month"]].isin(selected_months_l4l)]
                    df_left_l4l_raw = df_left_raw[df_left_raw[cols_left["Month"]].isin(selected_months_l4l)] if df_left_raw is not None else None
                    df_right_l4l_raw = df_right_raw[df_right_raw[cols_right["Month"]].isin(selected_months_l4l)] if df_right_raw is not None else None

                    st.markdown("### Filters for Detailed L4L")
                    filtered_list, meta = apply_shared_filters([df_left_l4l, df_right_l4l], cols_left, unique_prefix="l4l", raw_dfs=[df_left_l4l_raw, df_right_l4l_raw])
                    left_filtered, right_filtered = filtered_list
                    left_filtered_raw, right_filtered_raw = meta["filtered_raws"]

                    render_two_year_dashboard(
                        df_new=right_filtered,
                        df_old=left_filtered,
                        cols_new=cols_right,
                        cols_old=cols_left,
                        context_name="detailed_l4l",
                        unique_prefix="detailed_l4l",
                        category_filter=meta["category"],
                        df_new_raw=right_filtered_raw,
                        df_old_raw=left_filtered_raw,
                    )

# ================= FULL YEAR ANALYSIS =================
with tab_full:
    st.header("Full Year Analysis")

    available_years = []
    year_map_df = {}
    year_map_cols = {}
    year_map_raw = {}

    if df_old2 is not None:
        available_years.append(year_old2)
        year_map_df[year_old2] = df_old2
        year_map_cols[year_old2] = cols_old2
        year_map_raw[year_old2] = df_old2_raw
    if df_prev is not None:
        available_years.append(year_prev)
        year_map_df[year_prev] = df_prev
        year_map_cols[year_prev] = cols_prev
        year_map_raw[year_prev] = df_prev_raw
    if df_curr is not None:
        available_years.append(year_curr)
        year_map_df[year_curr] = df_curr
        year_map_cols[year_curr] = cols_curr
        year_map_raw[year_curr] = df_curr_raw

    if not available_years:
        st.info("No years available for full year analysis.")
    else:
        selected_full = st.selectbox("Select year for full year analysis", available_years, key="full_year_sel")
        df_selected = year_map_df[selected_full]
        cols_selected = year_map_cols[selected_full]
        df_selected_raw = year_map_raw[selected_full]

        st.markdown("### Filters for Full Year")
        filtered_selected, meta = create_single_filters(df_selected, cols_selected, unique_prefix="full", df_raw=df_selected_raw)

        # For full year KPI totals we use df_selected_raw filtered by selected filters (meta["df_filtered_raw"])
        df_filtered_raw = meta.get("df_filtered_raw", None)
        # In Full Year mode we hide Customer Impact (per request)
        render_single_year_dashboard(filtered_selected, cols_selected, selected_full, unique_prefix="full_dash", category_filter=meta["category"], df_raw=df_filtered_raw)
