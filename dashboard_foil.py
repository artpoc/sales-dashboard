import streamlit as st
import pandas as pd
import plotly.express as px
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, getcontext

# ===== PERFECT ENGINE INTEGRATION =====
getcontext().prec = 28

def clean_number(x):
    if isinstance(x, Decimal):
        return x
    if x is None or pd.isna(x):
        return Decimal('0')
    s = str(x)
    s = s.replace("\xa0","").replace("\u202f","").replace(" ","")
    s = s.replace(",", ".")
    if s in ["", "-", "nan", "None"]:
        return Decimal('0')
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal('0')

def sum_decimal(series):
    total = Decimal('0')
    for v in series:
        total += clean_number(v)
    return total

def to_int(d):
    try:
        return int(clean_number(d).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except:
        return 0

def yoy_calc(new, old):
    new, old = clean_number(new), clean_number(old)
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
    """Format YoY percentage with arrows and colors."""
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
    elif v < 0:
        return f"{v:.0f}% 🔴"
    return "0%"

def percent_label(val) -> str:
    """Format standard percentage values."""
    try:
        v = float(val)
        return f"{v:.1f}%"
    except Exception:
        return "0.0%"

def fix_sku(df, col):
    df[col] = df[col].astype(str).str.strip()
    return df
# ===== END ENGINE =====

# ================= CONFIG =================
DISPLAY_DECIMALS = 0  # 0 or 1
MONTHS_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

SHORT_MONTHS = {
    "January": "JAN", "February": "FEB", "March": "MAR", "April": "APR", "May": "MAY", "June": "JUN",
    "July": "JUL", "August": "AUG", "September": "SEP", "October": "OCT", "November": "NOV", "December": "DEC",
    "Total": "∑", "Avg Month": "AVG / Month"
}

# ================= FLAT UI COLORS - SPANISH PALETTE =================
# Z palety usunięto zbyt jasny 'Swan White' (#f7f1e3), aby wykresy były wyraźne.
SPANISH_PALETTE = [
    "#40407a", "#706fd3", "#34ace0", "#33d9b2", "#2c2c54",
    "#474787", "#aaa69d", "#227093", "#218c74", "#ff5252",
    "#ff793f", "#d1ccc0", "#ffb142", "#ffda79", "#b33939",
    "#cd6133", "#84817a", "#cc8e35", "#ccae62"
]

def normalize_month(x) -> str:
    """Potężny i agresywny tłumacz wszelkich formatów miesięcy na czysty angielski standard"""
    if pd.isna(x): return ""
    if hasattr(x, 'strftime'): return x.strftime("%B")
    
    x_str = str(x).strip().lower()
    if x_str.endswith(".0"): x_str = x_str[:-2]
    
    exact_map = {
        "1": "January", "01": "January", "january": "January", "styczeń": "January", "styczen": "January",
        "2": "February", "02": "February", "february": "February", "luty": "February",
        "3": "March", "03": "March", "march": "March", "marzec": "March",
        "4": "April", "04": "April", "april": "April", "kwiecień": "April", "kwiecien": "April",
        "5": "May", "05": "May", "may": "May", "maj": "May",
        "6": "June", "06": "June", "june": "June", "czerwiec": "June",
        "7": "July", "07": "July", "july": "July", "lipiec": "July",
        "8": "August", "08": "August", "august": "August", "sierpień": "August", "sierpien": "August",
        "9": "September", "09": "September", "september": "September", "wrzesień": "September", "wrzesien": "September",
        "10": "October", "october": "October", "październik": "October", "pazdziernik": "October",
        "11": "November", "november": "November", "listopad": "November",
        "12": "December", "december": "December", "grudzień": "December", "grudzien": "December"
    }
    
    if x_str in exact_map: 
        return exact_map[x_str]
    
    if "jan" in x_str or "sty" in x_str: return "January"
    if "feb" in x_str or "lut" in x_str: return "February"
    if "mar" in x_str: return "March"
    if "apr" in x_str or "kwi" in x_str: return "April"
    if "may" in x_str or "maj" in x_str: return "May"
    if "jun" in x_str or "cze" in x_str: return "June"
    if "jul" in x_str or "lip" in x_str: return "July"
    if "aug" in x_str or "sie" in x_str: return "August"
    if "sep" in x_str or "wrz" in x_str: return "September"
    if "oct" in x_str or "paź" in x_str or "paz" in x_str: return "October"
    if "nov" in x_str or "lis" in x_str: return "November"
    if "dec" in x_str or "gru" in x_str: return "December"
    
    try:
        dt = pd.to_datetime(x_str)
        return dt.strftime("%B")
    except:
        pass
    
    return str(x).strip().capitalize()

# ================= HELPERS & CORE UTILS =================
def add_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

def format_number_plain(d, decimals: int = DISPLAY_DECIMALS) -> str:
    d = clean_number(d)
    try:
        if decimals == 0:
            q = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return f"{int(q)}"
        q = d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return f"{q:.1f}"
    except (InvalidOperation, Exception):
        try:
            return str(int(d))
        except Exception:
            return "0"

def to_display_num(d):
    d = clean_number(d)
    try:
        if DISPLAY_DECIMALS == 0:
            return int(d.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        else:
            return float(d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
    except Exception:
        return 0

def normalize_category(x: str) -> str:
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
    if "article" in x: return "Other" 
    if "horn" in x: return "Horns"
    return "Other"

ALLOWED_CATEGORIES = [
    "Napkins", "Hats", "Banner", "Straws", "Bags", "Plates", "Paper Cups",
    "Tablecover", "Reusable", "Foil", "Wooden", "Candles", "Latex",
    "Invitations", "Masks", "Pinata", "Plastic Cups", "Horns", "Other"
]

def sort_by_col_desc(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col not in df.columns:
        return df
    try:
        return df.sort_values(by=col, ascending=False)
    except Exception:
        tmp = df.copy()
        try:
            tmp[col] = tmp[col].apply(lambda x: float(clean_number(x)))
            return tmp.sort_values(by=col, ascending=False)
        except Exception:
            return df

def extract_year_from_header(col_name: str) -> str:
    digits = "".join(ch for ch in str(col_name) if ch.isdigit())
    if digits:
        return digits
    return str(col_name)

# ================= DATA LOADING FOR SINGLE-YEAR FILES =================
def load_single_year_file(file, label: str):
    if file is None:
        return None, None, None

    df = pd.read_excel(file, dtype=object, engine="openpyxl")
    df.columns = df.columns.str.strip()

    month_col = None
    for c in df.columns:
        cl = str(c).strip().lower()
        if "month" in cl or "mies" in cl or "m-c" in cl:
            month_col = c
            break
    if month_col is None: month_col = df.columns[0]

    customer_col = None
    for c in df.columns:
        cl = str(c).strip().lower()
        if "customer" in cl or "klient" in cl or "odbiorca" in cl or "nabywca" in cl:
            customer_col = c
            break
    if customer_col is None: customer_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    country_col = None
    for c in df.columns:
        if "country" in str(c).lower() or "kraj" in str(c).lower():
            country_col = c
            break
    if country_col is None: country_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]

    code_col = None
    for c in df.columns:
        if "art" in str(c).lower() and "nr" in str(c).lower() or "code" in str(c).lower():
            code_col = c
            break
    if code_col is None: code_col = df.columns[4] if len(df.columns) > 4 else df.columns[0]

    desc_col = None
    for c in df.columns:
        if "description" in str(c).lower() or "opis" in str(c).lower():
            desc_col = c
            break
    if desc_col is None: desc_col = df.columns[5] if len(df.columns) > 5 else df.columns[0]

    brand_col = None
    for c in df.columns:
        if "brand" in str(c).lower() or "marka" in str(c).lower() or "licencja" in str(c).lower():
            brand_col = c
            break
    if brand_col is None: brand_col = df.columns[6] if len(df.columns) > 6 else df.columns[0]

    cat_col = None
    for c in df.columns:
        if "category" in str(c).lower() or "kategoria" in str(c).lower():
            cat_col = c
            break
    if cat_col is None: cat_col = df.columns[7] if len(df.columns) > 7 else df.columns[0]

    net_col = None
    qty_col = None
    for c in df.columns:
        cl = str(c).lower()
        if net_col is None and ("net" in cl or "value" in cl or "sales" in cl or "warto" in cl):
            net_col = c
        elif qty_col is None and ("qty" in cl or "quantity" in cl or "pcs" in cl or "ilo" in cl):
            qty_col = c
    if net_col is None: net_col = df.columns[-2] if len(df.columns) >= 2 else df.columns[-1]
    if qty_col is None: qty_col = df.columns[-1]

    df[net_col] = df[net_col].apply(clean_number)
    df[qty_col] = df[qty_col].apply(clean_number)

    # STANDARDIZING COLUMNS
    df["Month_Clean"] = df[month_col].apply(normalize_month)
    df["Customer_Clean"] = df[customer_col].astype(str).fillna("").replace("nan", "")
    df["Country_Clean"] = df[country_col].astype(str).fillna("").replace("nan", "").str.strip()
    df["Code_Clean"] = df[code_col].astype(str).fillna("").replace("nan", "").str.strip()
    df["Desc_Clean"] = df[desc_col].astype(str).fillna("").replace("nan", "")
    df["Brand_Clean"] = df[brand_col].astype(str).fillna("").replace("nan", "")
    df["Category_Clean"] = df[cat_col].astype(str).fillna("").replace("nan", "").apply(normalize_category)

    df = df[df["Category_Clean"].isin(ALLOWED_CATEGORIES)]
    df = df[df["Desc_Clean"].notna()]
    df = df[df["Desc_Clean"].str.lower() != "none"]

    year_name = extract_year_from_header(net_col)

    cols = {
        "YearName": year_name,
        "Month": "Month_Clean",
        "Customer": "Customer_Clean",
        "Country": "Country_Clean",
        "Code": "Code_Clean",
        "Desc": "Desc_Clean",
        "Brand": "Brand_Clean",
        "Cat": "Category_Clean",
        "Net": net_col,
        "Qty": qty_col,
    }
    return df, cols, year_name

# ================= FILTERS =================
def create_single_filters(df: pd.DataFrame, cols: dict, unique_prefix: str):
    if df is None or cols is None:
        return None, None

    df_all = df.copy()

    countries = ["All Countries"] + sorted(
        df_all[cols["Country"]].replace("", pd.NA).dropna().unique().tolist()
    )
    key_country = f"{unique_prefix}_country"
    selected_country = st.selectbox("Country", countries, key=key_country)

    df_for_customers = df_all.copy()
    if selected_country != "All Countries":
        df_for_customers = df_for_customers[df_for_customers[cols["Country"]] == selected_country]

    customers = ["All Customers"] + sorted(
        df_for_customers[cols["Customer"]].replace("", pd.NA).dropna().unique().tolist()
    )
    key_customer = f"{unique_prefix}_customer"
    selected_customer = st.selectbox("Customer", customers, key=key_customer)

    categories = ["All Categories"] + sorted(
        df_for_customers[cols["Cat"]].dropna().unique().tolist()
    )
    key_category = f"{unique_prefix}_category"
    selected_category = st.selectbox("Category", categories, key=key_category)

    df_filtered = df_all.copy()
    if selected_country != "All Countries":
        df_filtered = df_filtered[df_filtered[cols["Country"]] == selected_country]
    if selected_customer != "All Customers":
        df_filtered = df_filtered[df_filtered[cols["Customer"]] == selected_customer]
    if selected_category != "All Categories":
        df_filtered = df_filtered[df_filtered[cols["Cat"]] == selected_category]

    meta = {
        "country": selected_country,
        "customer": selected_customer,
        "category": selected_category,
        "df_all": df_all,
    }
    return df_filtered, meta


def apply_shared_filters(dfs, cols, unique_prefix: str, default_months=None, show_months=True):
    if not dfs:
        return [], None

    df_all = pd.concat(dfs, ignore_index=True)

    if show_months:
        c1, c2, c3, c4 = st.columns(4)
    else:
        c1, c2, c3 = st.columns(3)

    countries = ["All Countries"] + sorted(
        df_all[cols["Country"]].replace("", pd.NA).dropna().unique().tolist()
    )
    key_country = f"{unique_prefix}_country"
    selected_country = c1.selectbox("🌎 Country", countries, key=key_country)

    df_for_customers = df_all.copy()
    if selected_country != "All Countries":
        df_for_customers = df_for_customers[df_for_customers[cols["Country"]] == selected_country]

    customers = ["All Customers"] + sorted(
        df_for_customers[cols["Customer"]].replace("", pd.NA).dropna().unique().tolist()
    )
    key_customer = f"{unique_prefix}_customer"
    selected_customer = c2.selectbox("🏢 Customer", customers, key=key_customer)

    categories = ["All Categories"] + sorted(
        df_for_customers[cols["Cat"]].dropna().unique().tolist()
    )
    key_category = f"{unique_prefix}_category"
    selected_category = c3.selectbox("📦 Category", categories, key=key_category)

    if show_months:
        options_m = MONTHS_ORDER
        default_m = default_months if (default_months is not None and len(default_months) > 0) else MONTHS_ORDER
        default_m = [m for m in default_m if m in options_m]
        
        key_months = f"{unique_prefix}_months"
        
        selected_months = c4.multiselect("📅 Months", options=options_m, default=default_m, key=key_months)
    else:
        selected_months = default_months if (default_months is not None and len(default_months) > 0) else MONTHS_ORDER

    filtered_dfs = []
    for df in dfs:
        d = df.copy()
        if selected_country != "All Countries":
            d = d[d[cols["Country"]] == selected_country]
        if selected_customer != "All Customers":
            d = d[d[cols["Customer"]] == selected_customer]
        if selected_category != "All Categories":
            d = d[d[cols["Cat"]] == selected_category]
        if selected_months and show_months:
            d = d[d[cols["Month"]].isin(selected_months)]
        filtered_dfs.append(d)

    meta = {
        "country": selected_country,
        "customer": selected_customer,
        "category": selected_category,
        "months": selected_months,
        "df_all": df_all,
    }
    return filtered_dfs, meta


# ================= DASHBOARD RENDERING (TWO-YEAR L4L STYLE) =================
def render_two_year_dashboard(
    df_new: pd.DataFrame,
    df_old: pd.DataFrame,
    cols_new: dict,
    cols_old: dict,
    context_name: str,
    unique_prefix: str,
    category_filter: str = "All Categories",
    color_map: dict = None
):
    color_map = color_map or {}
    
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
    cat_col = cols_new["Cat"]

    year_new = cols_new["YearName"]
    year_old = cols_old["YearName"]

    st.markdown(f"### KPI ({year_old} vs {year_new})")

    s_new = sum_decimal(df_new[net_new])
    s_old = sum_decimal(df_old[net_old])
    q_new = sum_decimal(df_new[qty_new])
    q_old = sum_decimal(df_old[qty_old])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Net {year_old} (EUR)", format_number_plain(s_old))
    c2.metric(
        f"Net {year_new} (EUR)",
        format_number_plain(s_new),
        yoy_label(yoy_calc(s_new, s_old)),
    )
    c3.metric(f"Qty {year_old} (PCS)", format_number_plain(q_old))
    c4.metric(
        f"Qty {year_new} (PCS)",
        format_number_plain(q_new),
        yoy_label(yoy_calc(q_new, q_old)),
    )

    st.divider()

    # CATEGORY PERFORMANCE
    if category_filter == "All Categories":
        st.markdown("### Category Performance")

        cat_new = (
            df_new.groupby(cat_col)
            .agg({net_new: sum_decimal})
            .reset_index()
            .rename(columns={net_new: f"Net {year_new}"})
        )
        cat_old = (
            df_old.groupby(cat_col)
            .agg({net_old: sum_decimal})
            .reset_index()
            .rename(columns={net_old: f"Net {year_old}"})
        )
        cat = pd.merge(cat_new, cat_old, on=cat_col, how="outer").fillna(Decimal('0'))

        cat[f"YoY {year_new} vs {year_old}"] = cat.apply(
            lambda x: yoy_calc(x.get(f"Net {year_new}", Decimal('0')), x.get(f"Net {year_old}", Decimal('0'))), axis=1
        ) if not cat.empty else []

        cat = sort_by_col_desc(cat, f"Net {year_new}")

        plot_cat = cat.copy()
        plot_cat[f"Net {year_new}"] = plot_cat.get(f"Net {year_new}", pd.Series(dtype=float)).apply(
            lambda v: float(clean_number(v))
        )
        plot_cat[f"Net {year_old}"] = plot_cat.get(f"Net {year_old}", pd.Series(dtype=float)).apply(
            lambda v: float(clean_number(v))
        )
        plot_cat.loc[plot_cat[f"Net {year_new}"] < 0, f"Net {year_new}"] = 0
        plot_cat.loc[plot_cat[f"Net {year_old}"] < 0, f"Net {year_old}"] = 0

        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown(f"#### Category Pie {year_old}")
            st.plotly_chart(
                px.pie(plot_cat, names=cat_col, values=f"Net {year_old}", color=cat_col, color_discrete_map=color_map),
                use_container_width=True,
                key=f"{unique_prefix}_cat_pie_{year_old}"
            )
        with pc2:
            st.markdown(f"#### Category Pie {year_new}")
            st.plotly_chart(
                px.pie(plot_cat, names=cat_col, values=f"Net {year_new}", color=cat_col, color_discrete_map=color_map),
                use_container_width=True,
                key=f"{unique_prefix}_cat_pie_{year_new}"
            )

        cat_display = cat.copy()
        cat_display[f"Net {year_old}"] = cat_display.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        cat_display[f"Net {year_new}"] = cat_display.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        cat_display["YoY (%)"] = cat_display.get(f"YoY {year_new} vs {year_old}", pd.Series(dtype=str)).apply(yoy_label)
        
        st.dataframe(
            add_index(
                cat_display[
                    [
                        cat_col,
                        f"Net {year_old}",
                        f"Net {year_new}",
                        "YoY (%)",
                    ]
                ]
            )
        )

        st.divider()

    # BRAND PERFORMANCE
    st.markdown("### Brand Performance")

    brand_new = (
        df_new.groupby(brand_col)
        .agg({net_new: sum_decimal})
        .reset_index()
        .rename(columns={net_new: f"Net {year_new}"})
    )
    brand_old = (
        df_old.groupby(brand_col)
        .agg({net_old: sum_decimal})
        .reset_index()
        .rename(columns={net_old: f"Net {year_old}"})
    )
    brand = pd.merge(brand_new, brand_old, on=brand_col, how="outer").fillna(Decimal('0'))

    brand[f"YoY {year_new} vs {year_old}"] = brand.apply(
        lambda x: yoy_calc(x.get(f"Net {year_new}", Decimal('0')), x.get(f"Net {year_old}", Decimal('0'))), axis=1
    ) if not brand.empty else []

    brand = sort_by_col_desc(brand, f"Net {year_new}")

    bplot = brand.copy()
    bplot[f"Net {year_old}"] = bplot.get(f"Net {year_old}", pd.Series(dtype=float)).apply(
        lambda v: float(clean_number(v))
    )
    bplot[f"Net {year_new}"] = bplot.get(f"Net {year_new}", pd.Series(dtype=float)).apply(
        lambda v: float(clean_number(v))
    )
    bplot.loc[bplot[f"Net {year_old}"] < 0, f"Net {year_old}"] = 0
    bplot.loc[bplot[f"Net {year_new}"] < 0, f"Net {year_new}"] = 0

    bc1, bc2 = st.columns(2)
    with bc1:
        st.markdown(f"#### Brand Pie {year_old}")
        st.plotly_chart(
            px.pie(bplot, names=brand_col, values=f"Net {year_old}", color=brand_col, color_discrete_map=color_map),
            use_container_width=True,
            key=f"{unique_prefix}_brand_pie_{year_old}"
        )
    with bc2:
        st.markdown(f"#### Brand Pie {year_new}")
        st.plotly_chart(
            px.pie(bplot, names=brand_col, values=f"Net {year_new}", color=brand_col, color_discrete_map=color_map),
            use_container_width=True,
            key=f"{unique_prefix}_brand_pie_{year_new}"
        )

    brand_display = brand.copy()
    brand_display[f"Net {year_old}"] = brand_display.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
    brand_display[f"Net {year_new}"] = brand_display.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
    brand_display["YoY (%)"] = brand_display.get(f"YoY {year_new} vs {year_old}", pd.Series(dtype=str)).apply(yoy_label)
    
    st.dataframe(
        add_index(
            brand_display[
                [
                    brand_col,
                    f"Net {year_old}",
                    f"Net {year_new}",
                    "YoY (%)",
                ]
            ]
        )
    )

    st.divider()

    # TOP PRODUCTS
    st.markdown("### Top Products")

    if df_new.empty and df_old.empty:
        st.info("No data for selected filters.")
    else:
        base_new = df_new.copy()
        base_old = df_old.copy()

        t1, t2 = st.columns(2)

        with t1:
            st.write(f"#### Top 10 by Net {year_old}")
            d_old = (
                base_old.groupby(code_col)
                .agg({
                    desc_col: "first",
                    net_old: sum_decimal,
                    qty_old: sum_decimal,
                })
                .reset_index()
            )
            d_old = d_old[d_old[net_old].apply(lambda x: clean_number(x) > 0)]
            d_old = sort_by_col_desc(d_old, net_old)
            if d_old.empty:
                st.info("No sales in older year.")
            else:
                top_old = d_old.head(10)
                total_old_val = sum_decimal(d_old[net_old])
                if total_old_val == 0:
                    top_old["Share (%)"] = 0.0
                else:
                    top_old["Share (%)"] = top_old[net_old].apply(
                        lambda x: percent_label(clean_number(x) / total_old_val * Decimal('100'))
                    )
                disp_old = top_old.copy()
                disp_old[net_old] = disp_old.get(net_old, pd.Series(dtype=int)).apply(to_display_num)
                disp_old[qty_old] = disp_old.get(qty_old, pd.Series(dtype=int)).apply(to_display_num)
                
                st.dataframe(
                    add_index(
                        disp_old[[code_col, desc_col, net_old, qty_old, "Share (%)"]]
                    )
                )
                try:
                    share_top = (
                        sum_decimal(top_old[net_old]) / total_old_val * Decimal('100')
                    )
                except (InvalidOperation, Exception):
                    share_top = Decimal('0')
                st.write(f"Top 10 share: {format_number_plain(share_top)}%")

        with t2:
            st.write(f"#### Top 10 by Net {year_new}")
            d_new = (
                base_new.groupby(code_col)
                .agg({
                    desc_col: "first",
                    net_new: sum_decimal,
                    qty_new: sum_decimal,
                })
                .reset_index()
            )
            d_new = d_new[d_new[net_new].apply(lambda x: clean_number(x) > 0)]
            d_new = sort_by_col_desc(d_new, net_new)
            if d_new.empty:
                st.info("No sales in newer year.")
            else:
                top_new = d_new.head(10)
                total_new_val = sum_decimal(d_new[net_new])
                if total_new_val == 0:
                    top_new["Share (%)"] = 0.0
                else:
                    top_new["Share (%)"] = top_new[net_new].apply(
                        lambda x: percent_label(clean_number(x) / total_new_val * Decimal('100'))
                    )
                disp_new = top_new.copy()
                disp_new[net_new] = disp_new.get(net_new, pd.Series(dtype=int)).apply(to_display_num)
                disp_new[qty_new] = disp_new.get(qty_new, pd.Series(dtype=int)).apply(to_display_num)
                
                st.dataframe(
                    add_index(
                        disp_new[[code_col, desc_col, net_new, qty_new, "Share (%)"]]
                    )
                )
                try:
                    share_top_n = (
                        sum_decimal(top_new[net_new]) / total_new_val * Decimal('100')
                    )
                except (InvalidOperation, Exception):
                    share_top_n = Decimal('0')
                st.write(f"Top 10 share: {format_number_plain(share_top_n)}%")

    st.divider()

    # PARETO
    st.markdown("### Pareto Analysis")
    ptab = st.tabs([year_old, year_new])
    for tab, year, df_src, net_col in zip(
        ptab,
        [year_old, year_new],
        [df_old, df_new],
        [net_old, net_new],
    ):
        with tab:
            p = (
                df_src.groupby(code_col)
                .agg({
                    desc_col: "first",
                    cat_col: "first",
                    net_col: sum_decimal,
                })
                .reset_index()
            )
            p = p[p[net_col].apply(lambda x: clean_number(x) > 0)]
            if p.empty:
                st.info("No sales in this period.")
            else:
                p = sort_by_col_desc(p, net_col)
                p["cum_value"] = p[net_col].cumsum()
                total_value = sum_decimal(p[net_col])
                if total_value == 0:
                    st.info("Total value is zero.")
                else:
                    p["cum_share"] = p["cum_value"].apply(
                        lambda x: clean_number(x) / total_value
                    )
                    top80 = p[p["cum_share"] <= Decimal('0.8')]
                    total_sku = p[code_col].nunique()
                    pareto_sku = top80[code_col].nunique()
                    sku_share = (
                        Decimal(pareto_sku) / Decimal(total_sku) * Decimal('100')
                        if total_sku > 0
                        else Decimal('0')
                    )
                    st.write(
                        f"Top SKU for 80%: {pareto_sku} / {total_sku} ({format_number_plain(sku_share)}% of SKU)"
                    )
                    p_display = top80[[code_col, desc_col, cat_col, net_col]].copy()
                    p_display[net_col] = p_display.get(net_col, pd.Series(dtype=int)).apply(to_display_num)
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
            a = (
                df_src.groupby(code_col)
                .agg({desc_col: "first", net_col: sum_decimal})
                .reset_index()
            )
            a = a[a[net_col].apply(lambda x: clean_number(x) > 0)]
            if a.empty:
                st.info("No sales in this period.")
            else:
                a = sort_by_col_desc(a, net_col).reset_index(drop=True)
                total_val = sum_decimal(a[net_col])
                if total_val == 0:
                    st.info("Total is zero.")
                else:
                    a["cum"] = a[net_col].cumsum().apply(
                        lambda x: clean_number(x) / total_val
                    )
                    a["segment"] = "C"
                    a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
                    a.loc[
                        (a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')),
                        "segment",
                    ] = "B"
                    seg_counts = a["segment"].value_counts()
                    st.write(
                        f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}"
                    )
                    a_display = a[[code_col, desc_col, net_col, "segment"]].copy()
                    a_display[net_col] = a_display.get(net_col, pd.Series(dtype=int)).apply(to_display_num)
                    st.dataframe(add_index(a_display))

    st.divider()

    # L4L TABLE (Group strictly by Code to prevent split rows)
    st.markdown("### L4L Table")
    yoy_df_new = (
        df_new.groupby(code_col)
        .agg({desc_col: "first", net_new: sum_decimal, qty_new: sum_decimal})
        .reset_index()
    )
    yoy_df_old = (
        df_old.groupby(code_col)
        .agg({desc_col: "first", net_old: sum_decimal, qty_old: sum_decimal})
        .reset_index()
    )
    yoy = pd.merge(yoy_df_new, yoy_df_old, on=code_col, how="outer", suffixes=("", "_old"))
    yoy[desc_col] = yoy[desc_col].fillna(yoy[f"{desc_col}_old"])
    yoy = yoy.drop(columns=[f"{desc_col}_old"]).fillna(Decimal('0'))

    yoy["YoY"] = yoy.apply(
        lambda x: yoy_calc(x.get(net_new, 0), x.get(net_old, 0)), axis=1
    ) if not yoy.empty else []
    yoy = sort_by_col_desc(yoy, net_new)

    yoy_disp = yoy.copy()
    yoy_disp[net_old] = yoy_disp.get(net_old, pd.Series(dtype=int)).apply(to_display_num)
    yoy_disp[net_new] = yoy_disp.get(net_new, pd.Series(dtype=int)).apply(to_display_num)
    yoy_disp[qty_old] = yoy_disp.get(qty_old, pd.Series(dtype=int)).apply(to_display_num)
    yoy_disp[qty_new] = yoy_disp.get(qty_new, pd.Series(dtype=int)).apply(to_display_num)
    yoy_disp["YoY (%)"] = yoy_disp.get("YoY", pd.Series(dtype=str)).apply(yoy_label)

    st.dataframe(
        add_index(
            yoy_disp[
                [
                    code_col,
                    desc_col,
                    net_old,
                    net_new,
                    qty_old,
                    qty_new,
                    "YoY (%)",
                ]
            ]
        )
    )

    st.divider()

    # AUTO INSIGHTS (TOP 5, GROWTH, DECLINE) FOR 2 YEARS
    is_cat_all = (category_filter == "All Categories")
    st.markdown("### Auto Insights (Category Focus)" if is_cat_all else f"### Auto Insights (SKU Focus - {category_filter})")
    
    if is_cat_all:
        cat_new_ins = df_new.groupby(cat_col).agg({net_new: sum_decimal}).reset_index()
        cat_old_ins = df_old.groupby(cat_col).agg({net_old: sum_decimal}).reset_index()
        cat_ins = pd.merge(cat_new_ins, cat_old_ins, on=cat_col, how="outer").fillna(Decimal('0'))
        g_cols = [cat_col]
        disp_prefix = [cat_col]
    else:
        cat_new_ins = df_new.groupby(code_col).agg({desc_col: "first", net_new: sum_decimal}).reset_index()
        cat_old_ins = df_old.groupby(code_col).agg({desc_col: "first", net_old: sum_decimal}).reset_index()
        cat_ins = pd.merge(cat_new_ins, cat_old_ins, on=code_col, how="outer", suffixes=("", "_old"))
        cat_ins[desc_col] = cat_ins[desc_col].fillna(cat_ins[f"{desc_col}_old"])
        cat_ins = cat_ins.drop(columns=[f"{desc_col}_old"]).fillna(Decimal('0'))
        g_cols = [code_col, desc_col]
        cat_ins = cat_ins.rename(columns={code_col: "Code", desc_col: "Description"})
        disp_prefix = ["Code", "Description"]

    cat_ins = cat_ins.rename(columns={net_new: f"Net {year_new}", net_old: f"Net {year_old}"})

    cat_ins["Change_Raw"] = cat_ins.apply(
        lambda x: clean_number(x.get(f"Net {year_new}", Decimal('0'))) - clean_number(x.get(f"Net {year_old}", Decimal('0'))), axis=1
    )
    cat_ins["YoY"] = cat_ins.apply(
        lambda x: yoy_calc(x.get(f"Net {year_new}", Decimal('0')), x.get(f"Net {year_old}", Decimal('0'))), axis=1
    ) if not cat_ins.empty else []
    
    cat_ins = sort_by_col_desc(cat_ins, "Change_Raw")

    st.write("#### Top 5 " + ("Categories" if is_cat_all else "SKUs"))
    ic1, ic2 = st.columns(2)
    with ic1:
        top_old_cat = cat_ins.sort_values(f"Net {year_old}", ascending=False).head(5)
        disp_old_cat = top_old_cat.copy()
        disp_old_cat[f"Net {year_old}"] = disp_old_cat.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        st.dataframe(add_index(disp_old_cat[disp_prefix + [f"Net {year_old}"]]))
    with ic2:
        top_new_cat = cat_ins.sort_values(f"Net {year_new}", ascending=False).head(5)
        disp_new_cat = top_new_cat.copy()
        disp_new_cat[f"Net {year_new}"] = disp_new_cat.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        disp_new_cat["YoY (%)"] = disp_new_cat.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(add_index(disp_new_cat[disp_prefix + [f"Net {year_new}", "YoY (%)"]]))

    st.write("#### Top 5 Growth (L4L)")
    growth = cat_ins[cat_ins["Change_Raw"] > 0].sort_values("Change_Raw", ascending=False).head(5)
    if growth.empty:
        st.info("No growth found.")
    else:
        g_disp = growth.copy()
        g_disp[f"Net {year_old}"] = g_disp.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        g_disp[f"Net {year_new}"] = g_disp.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        g_disp[f"Change {year_new} vs {year_old}"] = g_disp["Change_Raw"].apply(to_display_num)
        g_disp["YoY (%)"] = g_disp.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(add_index(g_disp[disp_prefix + [f"Net {year_old}", f"Net {year_new}", f"Change {year_new} vs {year_old}", "YoY (%)"]]))

    st.write("#### Top 5 Decline (L4L)")
    decline = cat_ins[cat_ins["Change_Raw"] < 0].sort_values("Change_Raw", ascending=True).head(5)
    if decline.empty:
        st.success("No decline found.")
    else:
        d_disp = decline.copy()
        d_disp[f"Net {year_old}"] = d_disp.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        d_disp[f"Net {year_new}"] = d_disp.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        d_disp[f"Change {year_new} vs {year_old}"] = d_disp["Change_Raw"].apply(to_display_num)
        d_disp["YoY (%)"] = d_disp.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(add_index(d_disp[disp_prefix + [f"Net {year_old}", f"Net {year_new}", f"Change {year_new} vs {year_old}", "YoY (%)"]]))


    st.divider()

    # CUSTOMER IMPACT
    st.markdown("### Customer Impact (Growth vs Decline)")

    all_categories = sorted(
        df_new[cat_col].dropna().unique().tolist()
        + df_old[cat_col].dropna().unique().tolist()
    )
    all_categories = sorted(list(set(all_categories)))
    all_brands = sorted(
        df_new[brand_col].dropna().unique().tolist()
        + df_old[brand_col].dropna().unique().tolist()
    )
    all_brands = sorted(list(set(all_brands)))

    sel_cat_imp = st.selectbox(
        "Category for Impact Analysis",
        ["All Categories"] + all_categories,
        key=f"{unique_prefix}_impact_cat",
    )
    sel_brand_imp = st.selectbox(
        "Brand (License) for Impact Analysis",
        ["All Brands"] + all_brands,
        key=f"{unique_prefix}_impact_brand",
    )

    df_imp_new = df_new.copy()
    df_imp_old = df_old.copy()
    if sel_cat_imp != "All Categories":
        df_imp_new = df_imp_new[df_imp_new[cat_col] == sel_cat_imp]
        df_imp_old = df_imp_old[df_imp_old[cat_col] == sel_cat_imp]
    if sel_brand_imp != "All Brands":
        df_imp_new = df_imp_new[df_imp_new[brand_col] == sel_brand_imp]
        df_imp_old = df_imp_old[df_imp_old[brand_col] == sel_brand_imp]

    cust_new = (
        df_imp_new.groupby(cust_col)
        .agg({net_new: sum_decimal})
        .reset_index()
        .rename(columns={net_new: f"Net {year_new}"})
    )
    cust_old = (
        df_imp_old.groupby(cust_col)
        .agg({net_old: sum_decimal})
        .reset_index()
        .rename(columns={net_old: f"Net {year_old}"})
    )
    impact = pd.merge(
        cust_new, cust_old, on=cust_col, how="outer"
    ).fillna(Decimal('0'))
    
    impact["Change Value Raw"] = impact.get(f"Net {year_new}", Decimal('0')) - impact.get(f"Net {year_old}", Decimal('0'))
    impact["Special Case"] = (
        (impact.get(f"Net {year_old}", Decimal('0')) < 0) & (impact.get(f"Net {year_new}", Decimal('0')) == 0)
    )
    impact["YoY"] = impact.apply(
        lambda x: yoy_calc(x.get(f"Net {year_new}", 0), x.get(f"Net {year_old}", 0)), axis=1
    ) if not impact.empty else []

    st.write("#### Top Growth Drivers")
    growth_imp = impact[
        (impact["Change Value Raw"] > 0) & (~impact["Special Case"])
    ].sort_values("Change Value Raw", ascending=False).head(10)
    growth_special = impact[impact["Special Case"]].head(10)
    growth_imp = pd.concat([growth_imp, growth_special])
    if growth_imp.empty:
        st.info("No growth generated by customers.")
    else:
        g_disp = growth_imp.copy()
        g_disp[f"Net {year_old}"] = g_disp.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        g_disp[f"Net {year_new}"] = g_disp.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        g_disp["Change Value"] = g_disp.get("Change Value Raw", pd.Series(dtype=int)).apply(to_display_num)
        g_disp["YoY (%)"] = g_disp.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(
            add_index(
                g_disp[
                    [
                        cust_col,
                        f"Net {year_old}",
                        f"Net {year_new}",
                        "Change Value",
                        "YoY (%)",
                    ]
                ]
            )
        )

    st.write("#### Top Decline Drivers")
    decline_imp = impact[impact["Change Value Raw"] < 0].sort_values(
        "Change Value Raw"
    ).head(10)
    decline_special = impact[impact["Special Case"]].head(10)
    decline_imp = pd.concat([decline_imp, decline_special])
    if decline_imp.empty:
        st.success("No decline across customers.")
    else:
        d_disp = decline_imp.copy()
        d_disp[f"Net {year_old}"] = d_disp.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        d_disp[f"Net {year_new}"] = d_disp.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        d_disp["Change Value"] = d_disp.get("Change Value Raw", pd.Series(dtype=int)).apply(to_display_num)
        d_disp["YoY (%)"] = d_disp.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(
            add_index(
                d_disp[
                    [
                        cust_col,
                        f"Net {year_old}",
                        f"Net {year_new}",
                        "Change Value",
                        "YoY (%)",
                    ]
                ]
            )
        )


# ================= DASHBOARD FOR SINGLE YEAR (FULL YEAR ANALYSIS) =================
def render_single_year_dashboard(
    df: pd.DataFrame, cols: dict, year_name: str, unique_prefix: str, category_filter: str, color_map: dict = None
):
    color_map = color_map or {}
    
    if df is None or cols is None:
        st.warning("No data for this view.")
        return

    net_col = cols["Net"]
    qty_col = cols["Qty"]
    code_col = cols["Code"]
    desc_col = cols["Desc"]
    brand_col = cols["Brand"]
    cat_col = cols["Cat"]

    st.markdown(f"### KPI ({year_name})")

    s_net = sum_decimal(df[net_col])
    s_qty = sum_decimal(df[qty_col])

    c1, c2 = st.columns(2)
    c1.metric(f"Net {year_name} (EUR)", format_number_plain(s_net))
    c2.metric(f"Qty {year_name} (PCS)", format_number_plain(s_qty))

    st.divider()

    # CATEGORY PERFORMANCE
    if category_filter == "All Categories":
        st.markdown("### Category Performance")
        cat = (
            df.groupby(cat_col)
            .agg({net_col: sum_decimal})
            .reset_index()
            .rename(columns={net_col: f"Net {year_name}"})
        )
        cat = sort_by_col_desc(cat, f"Net {year_name}")
        plot_cat = cat.copy()
        plot_cat[f"Net {year_name}"] = plot_cat.get(f"Net {year_name}", pd.Series(dtype=float)).apply(
            lambda v: float(clean_number(v))
        )

        st.markdown(f"#### Category Pie {year_name}")
        st.plotly_chart(
            px.pie(plot_cat, names=cat_col, values=f"Net {year_name}", color=cat_col, color_discrete_map=color_map),
            use_container_width=True,
            key=f"{unique_prefix}_cat_pie_{year_name}"
        )

        cat_disp = cat.copy()
        cat_disp[f"Net {year_name}"] = cat_disp.get(f"Net {year_name}", pd.Series(dtype=int)).apply(to_display_num)
        st.dataframe(add_index(cat_disp[[cat_col, f"Net {year_name}"]]))

        st.divider()

    # BRAND PERFORMANCE
    st.markdown("### Brand Performance")
    brand = (
        df.groupby(brand_col)
        .agg({net_col: sum_decimal})
        .reset_index()
        .rename(columns={net_col: f"Net {year_name}"})
    )
    brand = sort_by_col_desc(brand, f"Net {year_name}")
    bplot = brand.copy()
    bplot[f"Net {year_name}"] = bplot.get(f"Net {year_name}", pd.Series(dtype=float)).apply(
        lambda v: float(clean_number(v))
    )

    st.markdown(f"#### Brand Pie {year_name}")
    st.plotly_chart(
        px.pie(bplot, names=brand_col, values=f"Net {year_name}", color=brand_col, color_discrete_map=color_map),
        use_container_width=True,
        key=f"{unique_prefix}_brand_pie_{year_name}"
    )

    brand_disp = brand.copy()
    brand_disp[f"Net {year_name}"] = brand_disp.get(f"Net {year_name}", pd.Series(dtype=int)).apply(to_display_num)
    st.dataframe(add_index(brand_disp[[brand_col, f"Net {year_name}"]]))

    st.divider()

    # TOP PRODUCTS
    st.markdown("### Top Products")
    if df.empty:
        st.info("No data for selected filters.")
    else:
        d = (
            df.groupby(code_col)
            .agg({desc_col: "first", net_col: sum_decimal, qty_col: sum_decimal})
            .reset_index()
        )
        d = d[d[net_col].apply(lambda x: clean_number(x) > 0)]
        d = sort_by_col_desc(d, net_col)
        if d.empty:
            st.info("No sales.")
        else:
            top = d.head(10)
            total_val = sum_decimal(d[net_col])
            if total_val == 0:
                top["Share (%)"] = 0.0
            else:
                top["Share (%)"] = top[net_col].apply(
                    lambda x: percent_label(clean_number(x) / total_val * Decimal('100'))
                )
            disp = top.copy()
            disp[net_col] = disp.get(net_col, pd.Series(dtype=int)).apply(to_display_num)
            disp[qty_col] = disp.get(qty_col, pd.Series(dtype=int)).apply(to_display_num)
            st.dataframe(
                add_index(disp[[code_col, desc_col, net_col, qty_col, "Share (%)"]])
            )

    st.divider()

    # PARETO
    st.markdown("### Pareto Analysis")
    p = (
        df.groupby(code_col)
        .agg({desc_col: "first", cat_col: "first", net_col: sum_decimal})
        .reset_index()
    )
    p = p[p[net_col].apply(lambda x: clean_number(x) > 0)]
    if p.empty:
        st.info("No sales.")
    else:
        p = sort_by_col_desc(p, net_col)
        p["cum_value"] = p[net_col].cumsum()
        total_val = sum_decimal(p[net_col])
        if total_val == 0:
            st.info("Total value is zero.")
        else:
            p["cum_share"] = p["cum_value"].apply(
                lambda x: clean_number(x) / total_val
            )
            top80 = p[p["cum_share"] <= Decimal('0.8')]
            total_sku = p[code_col].nunique()
            pareto_sku = top80[code_col].nunique()
            sku_share = (
                Decimal(pareto_sku) / Decimal(total_sku) * Decimal('100')
                if total_sku > 0
                else Decimal('0')
            )
            st.write(
                f"Top SKU for 80%: {pareto_sku} / {total_sku} ({format_number_plain(sku_share)}% of SKU)"
            )
            p_disp = top80[[code_col, desc_col, cat_col, net_col]].copy()
            p_disp[net_col] = p_disp.get(net_col, pd.Series(dtype=int)).apply(to_display_num)
            st.dataframe(add_index(p_disp))

    st.divider()

    # ABC
    st.markdown("### ABC Analysis")
    a = (
        df.groupby(code_col)
        .agg({desc_col: "first", net_col: sum_decimal})
        .reset_index()
    )
    a = a[a[net_col].apply(lambda x: clean_number(x) > 0)]
    if a.empty:
        st.info("No sales.")
    else:
        a = sort_by_col_desc(a, net_col).reset_index(drop=True)
        total_val = sum_decimal(a[net_col])
        if total_val == 0:
            st.info("Total is zero.")
        else:
            a["cum"] = a[net_col].cumsum().apply(
                lambda x: clean_number(x) / total_val
            )
            a["segment"] = "C"
            a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
            a.loc[
                (a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')),
                "segment",
            ] = "B"
            seg_counts = a["segment"].value_counts()
            st.write(
                f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}"
            )
            a_disp = a[[code_col, desc_col, net_col, "segment"]].copy()
            a_disp[net_col] = a_disp.get(net_col, pd.Series(dtype=int)).apply(to_display_num)
            st.dataframe(add_index(a_disp))

    st.divider()

    # AUTO INSIGHTS (Top 5 Categories)
    if category_filter == "All Categories":
        st.markdown("### Auto Insights")
        cat_ins = (
            df.groupby(cat_col)
            .agg({net_col: sum_decimal})
            .reset_index()
            .rename(columns={net_col: f"Net {year_name}"})
        )
        cat_ins = sort_by_col_desc(cat_ins, f"Net {year_name}")
        st.write("#### Top 5 Categories")
        top5 = cat_ins.head(5)
        disp = top5.copy()
        disp[f"Net {year_name}"] = disp.get(f"Net {year_name}", pd.Series(dtype=int)).apply(to_display_num)
        st.dataframe(add_index(disp[[cat_col, f"Net {year_name}"]]))


# ================= MAIN APP INITIALIZATION =================
st.set_page_config(layout="wide", page_title="Sales Intelligence Dashboard")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha")

def update_cached_file(file_obj, state_key, label):
    keys_to_del = ["ov_months", "l4l_months", "cr_months", "co_months", "br_months", "ch_months"]
    if file_obj is None:
        st.session_state[state_key] = (None, None, None)
        st.session_state[f"{state_key}_id"] = None
        for k in keys_to_del: st.session_state.pop(k, None)
    elif st.session_state.get(f"{state_key}_id") != file_obj.file_id:
        file_obj.seek(0)
        st.session_state[state_key] = load_single_year_file(file_obj, label)
        st.session_state[f"{state_key}_id"] = file_obj.file_id
        for k in keys_to_del: st.session_state.pop(k, None)

for key in ['data_older', 'data_prev', 'data_curr']:
    if key not in st.session_state: st.session_state[key] = (None, None, None)

st.markdown("### Excel Upload (3 separate years)")
c_up1, c_up2, c_up3 = st.columns(3)
with c_up1: update_cached_file(st.file_uploader("Older Year (2 years ago)", type=["xlsx"], key="up1"), 'data_older', "older")
with c_up2: update_cached_file(st.file_uploader("Previous Year", type=["xlsx"], key="up2"), 'data_prev', "prev")
with c_up3: update_cached_file(st.file_uploader("Current Year (YTD)", type=["xlsx"], key="up3"), 'data_curr', "curr")

df_old2, cols_old2, year_old2 = st.session_state['data_older']
df_prev, cols_prev, year_prev = st.session_state['data_prev']
df_curr, cols_curr, year_curr = st.session_state['data_curr']

if df_prev is None and df_curr is None and df_old2 is None:
    st.info("Upload at least one Excel file.")
    st.stop()

# GLOBAL COLOR MAP GENERATION
GLOBAL_COLOR_MAP = {"Other": "#808080"}
all_loaded_dfs_for_colors = [d for d in [df_curr, df_prev, df_old2] if d is not None]

if len(all_loaded_dfs_for_colors) > 0:
    all_cat, all_br, all_co, all_cu, all_y = set(), set(), set(), set(), []
    for d, c, y in zip([df_old2, df_prev, df_curr], [cols_old2, cols_prev, cols_curr], [year_old2, year_prev, year_curr]):
        if d is not None:
            all_cat.update(d[c["Cat"]].dropna().unique())
            all_br.update(d[c["Brand"]].dropna().unique())
            all_co.update(d[c["Country"]].dropna().unique())
            all_cu.update(d[c["Customer"]].dropna().unique())
            if str(y) not in all_y: all_y.append(str(y))
    
    year_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, y in enumerate(all_y): GLOBAL_COLOR_MAP[y] = year_colors[i % len(year_colors)]
    
    c_idx = 0
    for item in sorted(list(all_cat)) + sorted(list(all_br)) + sorted(list(all_co)) + sorted(list(all_cu)):
        if item not in GLOBAL_COLOR_MAP:
            GLOBAL_COLOR_MAP[item] = SPANISH_PALETTE[c_idx % len(SPANISH_PALETTE)]
            c_idx += 1

st.divider()

# TABS DECLARATION (EXACTLY ONCE)
tab_overview, tab_l4l, tab_full, tab_customer, tab_country, tab_brand, tab_churn = st.tabs([
    "📈 Overview", "📅 Detailed L4L", "📊 Full Year Analysis", "👥 Customer Review", "🌍 Country Review", "🏷️ Brand Review", "⚠️ Churn & Acquisition"
])

hierarchy_df, hierarchy_cols = (df_curr, cols_curr) if df_curr is not None else ((df_prev, cols_prev) if df_prev is not None else (df_old2, cols_old2))
hierarchy_months = sorted([m for m in hierarchy_df[hierarchy_cols["Month"]].dropna().unique().tolist() if m in MONTHS_ORDER], key=lambda x: MONTHS_ORDER.index(x)) if hierarchy_df is not None else []
st.sidebar.info(f"ℹ️ Default months detected: {', '.join(hierarchy_months) if hierarchy_months else 'None'}")

def style_monthly_table(df):
    def color_cells(s):
        if "∆" in str(s.get('Year', '')):
            return ["background-color: rgba(144,238,144,0.4); color: black;" if "🟢" in str(v) else "background-color: rgba(255,182,193,0.4); color: black;" if "🔴" in str(v) else "" for v in s]
        return [""] * len(s)
    return df.style.apply(color_cells, axis=1)

# ================= TAB: OVERVIEW =================
with tab_overview:
    st.header("Overview — 3-year Comparison")
    loaded_dfs = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if not loaded_dfs: st.warning("Please upload data.")
    else:
        filtered_dfs, meta = apply_shared_filters(loaded_dfs, hierarchy_cols, "ov", default_months=hierarchy_months)
        df_curr_f, df_prev_f, df_old2_f = (filtered_dfs[0] if df_curr is not None else None), (filtered_dfs[1 if df_curr is not None else 0] if df_prev is not None else None), (filtered_dfs[-1] if df_old2 is not None else None)

        st.divider()
        st.markdown("### Net Value Comparison (Global Filters Applied)")
        vals, years = [], []
        for df_f, y, c in zip([df_old2_f, df_prev_f, df_curr_f], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if df_f is not None: vals.append(float(sum_decimal(df_f[c["Net"]]))); years.append(y)
        if vals: st.plotly_chart(px.bar(pd.DataFrame({"Year": years, "Net": vals}), x="Year", y="Net", text="Net", color="Year", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

        def render_3y_analysis(group_col, title, dfs, year_list, cols_list, display_name):
            st.divider(); st.markdown(f"### {title}")
            g_dfs = [(df.groupby(group_col).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"}), y) for df, y, c in zip(dfs, year_list, cols_list) if df is not None]
            if g_dfs:
                master = g_dfs[0][0]
                for g, y in g_dfs[1:]: master = pd.merge(master, g, on=group_col, how="outer")
                master = master.fillna(Decimal('0'))
                g_dfs_c = sorted(g_dfs, key=lambda x: x[1])
                y_newest = g_dfs_c[-1][1]
                if len(g_dfs_c) >= 2: master[f"YoY {y_newest} vs {g_dfs_c[-2][1]}"] = master.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {g_dfs_c[-2][1]}", 0)), axis=1) if not master.empty else []
                master = sort_by_col_desc(master, f"Net {y_newest}")

                pie_cols = st.columns(len(g_dfs_c))
                for i, (g, y) in enumerate(g_dfs_c):
                    plot_df = master.copy()
                    plot_df[f"Net {y}"] = plot_df.get(f"Net {y}").apply(lambda v: max(0, float(clean_number(v))))
                    tot = plot_df[f"Net {y}"].sum()
                    if tot > 0:
                        plot_df.loc[plot_df[f"Net {y}"] / tot < 0.005, group_col] = 'Other'
                        plot_df = plot_df.groupby(group_col, as_index=False)[[f"Net {y}"]].sum()
                    with pie_cols[i]: st.plotly_chart(px.pie(plot_df, names=group_col, values=f"Net {y}", title=f"{display_name} {y}", color=group_col, color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)
                
                disp = master.copy()
                for _, y in g_dfs_c: disp[f"Net {y}"] = disp.get(f"Net {y}").apply(to_display_num)
                if len(g_dfs_c) >= 2: disp[f"YoY {y_newest} vs {g_dfs_c[-2][1]} (%)"] = disp.get(f"YoY {y_newest} vs {g_dfs_c[-2][1]}").apply(yoy_label)
                st.dataframe(add_index(disp.rename(columns={group_col: display_name})[[display_name] + [f"Net {y}" for _,y in g_dfs_c] + ([f"YoY {y_newest} vs {g_dfs_c[-2][1]} (%)"] if len(g_dfs_c)>=2 else [])]), use_container_width=True)

        dfs_cat = [df.copy()[df.copy()[c["Cat"]] == meta["category"]] if meta["category"] != "All Categories" else df for df, c in zip([df_curr_f, df_prev_f, df_old2_f], [cols_curr, cols_prev, cols_old2]) if df is not None]
        if meta["category"] == "All Categories": render_3y_analysis(hierarchy_cols["Cat"], "Category Comparison", dfs_cat, [year_curr, year_prev, year_old2], [cols_curr, cols_prev, cols_old2], "Category")
        render_3y_analysis(hierarchy_cols["Brand"], "Brand Comparison", [df_curr_f, df_prev_f, df_old2_f], [year_curr, year_prev, year_old2], [cols_curr, cols_prev, cols_old2], "Brand")

        st.divider()
        is_cat_all = (meta["category"] == "All Categories")
        st.markdown("### Auto Insights (Category Focus)" if is_cat_all else f"### Auto Insights (SKU Focus - {meta['category']})")
        
        ins_dfs_ov = []
        for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if orig_d is not None:
                d_f = orig_d.copy()
                if meta["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta["country"]]
                if meta["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta["customer"]]
                if not is_cat_all: d_f = d_f[d_f[c["Cat"]] == meta["category"]]
                if meta["months"]: d_f = d_f[d_f[c["Month"]].isin(meta["months"])]
                
                if not d_f.empty:
                    if is_cat_all: ins_dfs_ov.append((d_f.groupby(c["Cat"]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"}), y, c["Cat"]))
                    else: ins_dfs_ov.append((d_f.groupby(c["Code"]).agg({c["Desc"]: "first", c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"}), y, c["Code"]))
                
        if len(ins_dfs_ov) >= 2:
            if is_cat_all:
                c_master_key = ins_dfs_ov[0][2]
                master_ins_ov = ins_dfs_ov[0][0]
                for g, y, _ in ins_dfs_ov[1:]: master_ins_ov = pd.merge(master_ins_ov, g, on=c_master_key, how="outer")
                master_ins_ov = master_ins_ov.fillna(Decimal('0'))
                disp_prefix = [c_master_key]
            else:
                c_code = ins_dfs_ov[0][2]
                c_desc = hierarchy_cols["Desc"]
                master_ins_ov = ins_dfs_ov[0][0]
                for g, y, _ in ins_dfs_ov[1:]:
                    master_ins_ov = pd.merge(master_ins_ov, g, on=c_code, how="outer", suffixes=("", "_y"))
                    master_ins_ov[c_desc] = master_ins_ov[c_desc].fillna(master_ins_ov[c_desc + "_y"])
                    master_ins_ov = master_ins_ov.drop(columns=[c_desc + "_y"])
                for col in master_ins_ov.columns:
                    if "Net" in col: master_ins_ov[col] = master_ins_ov[col].fillna(Decimal('0'))
                master_ins_ov = master_ins_ov.rename(columns={c_code: "Code", c_desc: "Description"})
                disp_prefix = ["Code", "Description"]
            
            ins_chrono_ov = sorted(ins_dfs_ov, key=lambda x: x[1])
            ov_years = [item[1] for item in ins_chrono_ov]
            y_newest = ov_years[-1]
            y1 = ov_years[-2]
            
            master_ins_ov["Change_1_Raw"] = master_ins_ov.apply(lambda x: clean_number(x.get(f"Net {y_newest}", Decimal('0'))) - clean_number(x.get(f"Net {y1}", Decimal('0'))), axis=1)
            master_ins_ov["YoY_1"] = master_ins_ov.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0)), axis=1)
            
            if len(ov_years) >= 2:
                master_ins_ov[f"Change {y_newest} vs {y1}"] = master_ins_ov["Change_1_Raw"].apply(to_display_num)
                master_ins_ov[f"YoY {y_newest} vs {y1} (%)"] = master_ins_ov["YoY_1"].apply(yoy_label)
                display_cols = disp_prefix + [f"Net {y}" for y in ov_years] + [f"Change {y_newest} vs {y1}", f"YoY {y_newest} vs {y1} (%)"]

            c1, c2 = st.columns(2)
            with c1:
                st.write("#### Top 5 Growth" + (" Categories" if is_cat_all else " SKUs"))
                growth = master_ins_ov[master_ins_ov["Change_1_Raw"] > 0].sort_values("Change_1_Raw", ascending=False).head(5)
                if not growth.empty:
                    disp = growth.copy()
                    for y in ov_years: disp[f"Net {y}"] = disp.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                    st.dataframe(add_index(disp[display_cols]))
                else: st.info("No growth found.")
                    
            with c2:
                st.write("#### Top 5 Decline" + (" Categories" if is_cat_all else " SKUs"))
                decline = master_ins_ov[master_ins_ov["Change_1_Raw"] < 0].sort_values("Change_1_Raw", ascending=True).head(5)
                if not decline.empty:
                    disp = decline.copy()
                    for y in ov_years: disp[f"Net {y}"] = disp.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                    st.dataframe(add_index(disp[display_cols]))
                else: st.success("No decline found.")

# ================= TAB: DETAILED L4L =================
with tab_l4l:
    st.header("Detailed Like-for-Like")
    year_ops = [y for d, y in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr]) if d is not None]
    if len(year_ops) < 2: st.warning("Requires at least two year files.")
    else:
        left_y = st.selectbox("Older year", year_ops, index=0, key="l4l_l")
        right_y = st.selectbox("Newer year", year_ops, index=1 if len(year_ops)>1 else 0, key="l4l_r")
        if left_y == right_y: st.error("Years must be different.")
        else:
            df_map = {year_old2: (df_old2, cols_old2), year_prev: (df_prev, cols_prev), year_curr: (df_curr, cols_curr)}
            df_l, cols_l = df_map[left_y]
            df_r, cols_r = df_map[right_y]
            f_list, meta = apply_shared_filters([df_l, df_r], cols_l, "l4l", default_months=hierarchy_months)
            render_two_year_dashboard(f_list[1], f_list[0], cols_r, cols_l, "l4l", "l4l", meta["category"], GLOBAL_COLOR_MAP)

# ================= TAB: FULL YEAR =================
with tab_full:
    st.header("Full Year Analysis")
    year_ops = [y for d, y in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr]) if d is not None]
    if not year_ops: st.info("No data.")
    else:
        sel_y = st.selectbox("Select year", year_ops, key="fy_y")
        df_map = {year_old2: (df_old2, cols_old2), year_prev: (df_prev, cols_prev), year_curr: (df_curr, cols_curr)}
        df_sel, cols_sel = df_map[sel_y]
        f_sel, meta = create_single_filters(df_sel, cols_sel, "full")
        render_single_year_dashboard(f_sel, cols_sel, sel_y, "full_dash", meta["category"], GLOBAL_COLOR_MAP)

# ================= HELPER FOR MONTHLY TABLES =================
def get_filtered_cr_dfs(m_dict):
    v_dfs = []
    for d_f, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
        if d_f is not None:
            tmp = d_f.copy()
            if m_dict.get("country") and m_dict["country"] != "All Countries": tmp = tmp[tmp[c["Country"]] == m_dict["country"]]
            if m_dict.get("customer") and m_dict["customer"] != "All Customers": tmp = tmp[tmp[c["Customer"]] == m_dict["customer"]]
            if m_dict.get("category") and m_dict["category"] != "All Categories": tmp = tmp[tmp[c["Cat"]] == m_dict["category"]]
            if m_dict.get("brand") and m_dict["brand"] != "All Brands": tmp = tmp[tmp[c["Brand"]] == m_dict["brand"]]
            if m_dict.get("months"): tmp = tmp[tmp[c["Month"]].isin(m_dict["months"])]
            if not tmp.empty: v_dfs.append((tmp, str(y), c))
    return sorted(v_dfs, key=lambda x: x[1])

def render_monthly_comparison(v_dfs, m_dict, mode="Net"):
    st.markdown(f"### {mode} Value Monthly Comparison")
    div = len(m_dict.get("months", [])) or 12
    avg_div = st.slider(f"Select months for calculation:", 1, 12, div, key=f"sl_{mode}_{m_dict.get('prefix','x')}")
    if not v_dfs: return
    
    col_key = "Net" if mode=="Net" else "Qty"
    sum_k, avg_k = f"∑ ({avg_div} m)", "Avg Month"
    rows = []
    
    for d_f, y_str, c in v_dfs:
        m_vals = {m: sum_decimal(d_f[d_f[c["Month"]] == m][c[col_key]]) for m in MONTHS_ORDER}
        partial = sum(m_vals[m] for m in MONTHS_ORDER[:avg_div])
        m_vals[sum_k] = partial
        m_vals[avg_k] = partial / Decimal(str(avg_div))
        
        row = {"Year": y_str}
        for m in MONTHS_ORDER + [sum_k, avg_k]: row[SHORT_MONTHS.get(m, m)] = to_display_num(m_vals[m])
        rows.append(row)
        
    if len(rows) >= 2:
        y_new, y_old = rows[-1]["Year"], rows[-2]["Year"]
        row_yoy = {"Year": f"∆ {y_new} vs {y_old}"}
        for m in MONTHS_ORDER + [sum_k, avg_k]:
            k = SHORT_MONTHS.get(m, m)
            row_yoy[k] = yoy_label(yoy_calc(rows[-1][k], rows[-2][k])) if m in m_dict.get("months", MONTHS_ORDER) + [sum_k, avg_k] else "n/a"
        rows.append(row_yoy)
        
    st.dataframe(style_monthly_table(pd.DataFrame(rows)), use_container_width=True, hide_index=True)

# ================= TAB: CUSTOMER REVIEW =================
with tab_customer:
    st.header("👥 Customer Review")
    if not [d for d in [df_curr, df_prev, df_old2] if d is not None]: st.warning("Upload data.")
    else:
        df_all_cr = pd.concat([d for d in [df_curr, df_prev, df_old2] if d is not None], ignore_index=True)
        c1, c2, c3, c4 = st.columns(4)
        m_cr = {"prefix":"cr"}
        m_cr["country"] = c1.selectbox("🌎 Country", ["All Countries"] + sorted(df_all_cr[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist()), key="cr_co")
        m_cr["customer"] = c2.selectbox("🏢 Customer", ["All Customers"] + sorted(df_all_cr[df_all_cr[hierarchy_cols["Country"]]==m_cr["country"] if m_cr["country"]!="All Countries" else df_all_cr][hierarchy_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist()), key="cr_cu")
        m_cr["category"] = c3.selectbox("📦 Category", ["All Categories"] + sorted(df_all_cr[hierarchy_cols["Cat"]].dropna().unique().tolist()), key="cr_ca")
        m_cr["months"] = c4.multiselect("📅 Months", MONTHS_ORDER, default=hierarchy_months or MONTHS_ORDER, key="cr_mo")

        if m_cr["customer"] == "All Customers": st.info("⚠️ Select a specific customer.")
        else:
            v_dfs = get_filtered_cr_dfs(m_cr)
            st.markdown("### KPI (Current vs Previous)")
            if len(v_dfs) >= 2:
                d_n, y_n, c_n = v_dfs[-1]
                d_o, y_o, c_o = v_dfs[-2]
                k1, k2, k3, k4 = st.columns(4)
                k1.metric(f"Net {y_o}", format_number_plain(sum_decimal(d_o[c_o["Net"]])))
                k2.metric(f"Net {y_n}", format_number_plain(sum_decimal(d_n[c_n["Net"]])), yoy_label(yoy_calc(sum_decimal(d_n[c_n["Net"]]), sum_decimal(d_o[c_o["Net"]]))))
                k3.metric(f"Qty {y_o}", format_number_plain(sum_decimal(d_o[c_o["Qty"]])))
                k4.metric(f"Qty {y_n}", format_number_plain(sum_decimal(d_n[c_n["Qty"]])), yoy_label(yoy_calc(sum_decimal(d_n[c_n["Qty"]]), sum_decimal(d_o[c_o["Qty"]]))))
            else: st.info("Not enough data.")
            
            st.divider(); render_monthly_comparison(v_dfs, m_cr, "Net")
            st.divider(); render_monthly_comparison(v_dfs, m_cr, "Qty")

            if v_dfs:
                st.divider(); st.markdown("### Net Value Comparison")
                st.plotly_chart(px.bar(pd.DataFrame([{"Year": y, "Net": float(sum_decimal(d[c["Net"]]))} for d, y, c in v_dfs]), x="Year", y="Net", color="Year", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

            def render_cr_sub(group_col_key, section_title, display_name):
                st.divider(); st.markdown(f"### {section_title}")
                g_dfs = [(d.groupby(c[group_col_key]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"}), y, c[group_col_key]) for d,y,c in v_dfs]
                if g_dfs:
                    g_col_name = g_dfs[0][2]
                    master = g_dfs[0][0]
                    for g, y, _ in g_dfs[1:]: master = pd.merge(master, g, on=g_col_name, how="outer")
                    master = master.fillna(Decimal('0'))
                    y_newest = g_dfs[-1][1]
                    if len(g_dfs) >= 2: master[f"YoY {y_newest} vs {g_dfs[-2][1]}"] = master.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {g_dfs[-2][1]}", 0)), axis=1) if not master.empty else []
                    master = sort_by_col_desc(master, f"Net {y_newest}")

                    pie_cols = st.columns(len(g_dfs))
                    for i, (g, y, _) in enumerate(g_dfs):
                        plot_df = master.copy()
                        plot_df[f"Net {y}"] = plot_df.get(f"Net {y}", pd.Series(dtype=float)).apply(lambda v: max(0, float(clean_number(v))))
                        tot = plot_df[f"Net {y}"].sum()
                        if tot > 0:
                            plot_df['Share'] = plot_df[f"Net {y}"] / tot
                            plot_df.loc[plot_df['Share'] < 0.005, g_col_name] = 'Other'
                            plot_df = plot_df.groupby(g_col_name, as_index=False)[[f"Net {y}"]].sum()
                        with pie_cols[i]: st.plotly_chart(px.pie(plot_df, names=g_col_name, values=f"Net {y}", title=f"{display_name} Pie {y}", color=g_col_name, color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                    display_df = master.copy()
                    for _, y, _ in g_dfs: display_df[f"Net {y}"] = display_df.get(f"Net {y}").apply(to_display_num)
                    if len(g_dfs) >= 2:
                        y1 = g_dfs[-2][1]
                        display_df[f"YoY {y_newest} vs {y1} (%)"] = display_df.get(f"YoY {y_newest} vs {y1}").apply(yoy_label)
                    
                    display_df = display_df.rename(columns={g_col_name: display_name})
                    cols_order = [display_name] + [f"Net {y}" for _,y,_ in g_dfs] + ([f"YoY {y_newest} vs {g_dfs[-2][1]} (%)"] if len(g_dfs)>=2 else [])
                    st.dataframe(add_index(display_df[cols_order]), use_container_width=True)

            if m_cr["category"] == "All Categories": render_cr_sub("Cat", "Category Comparison", "Category")
            render_cr_sub("Brand", "Brand Comparison", "Brand")

            st.divider(); st.markdown("### L4L Table (SKU Level)")
            if v_dfs:
                c_code, c_desc = v_dfs[0][2]["Code"], hierarchy_cols["Desc"]
                l4l_dfs = [(d.groupby(c["Code"]).agg({c["Desc"]: "first", c["Net"]: sum_decimal, c["Qty"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}", c["Qty"]: f"Qty {y}"}), y) for d,y,c in v_dfs]
                master_l4l = l4l_dfs[0][0]
                for g, y in l4l_dfs[1:]:
                    master_l4l = pd.merge(master_l4l, g, on=c_code, how="outer", suffixes=("", "_y"))
                    master_l4l[c_desc] = master_l4l[c_desc].fillna(master_l4l[c_desc + "_y"])
                    master_l4l = master_l4l.drop(columns=[c_desc + "_y"])
                for col in master_l4l.columns:
                    if "Net" in col or "Qty" in col: master_l4l[col] = master_l4l[col].fillna(Decimal('0'))
                
                y_newest = l4l_dfs[-1][1]
                cr_years = [y for _, y in l4l_dfs]
                display_cols = [c_code, c_desc]
                for y in cr_years: display_cols.extend([f"Net {y}", f"Qty {y}"])
                if len(cr_years) >= 2:
                    y1 = cr_years[-2]
                    master_l4l[f"YoY {y_newest} vs {y1} (%)"] = master_l4l.apply(lambda x: yoy_label(yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0))), axis=1) if not master_l4l.empty else []
                    display_cols.append(f"YoY {y_newest} vs {y1} (%)")

                master_l4l = sort_by_col_desc(master_l4l, f"Net {y_newest}")
                for y in cr_years:
                    master_l4l[f"Net {y}"] = master_l4l.get(f"Net {y}").apply(to_display_num)
                    master_l4l[f"Qty {y}"] = master_l4l.get(f"Qty {y}").apply(to_display_num)
                
                master_l4l = master_l4l.rename(columns={c_code: "Code", c_desc: "Description"})
                display_cols[0], display_cols[1] = "Code", "Description"
                st.dataframe(add_index(master_l4l[display_cols]), use_container_width=True)

            st.divider(); st.markdown("### Auto Insights (Category Focus)" if m_cr["category"] == "All Categories" else f"### Auto Insights (SKU Focus - {m_cr['category']})")
            if len(v_dfs) >= 2:
                is_cat_all = (m_cr["category"] == "All Categories")
                ins_dfs = [(d.groupby(c["Cat"] if is_cat_all else c["Code"]).agg({c["Net"]: sum_decimal} if is_cat_all else {c["Desc"]: "first", c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"}), y, c["Cat"] if is_cat_all else c["Code"]) for d,y,c in v_dfs]
                
                c_master_key = ins_dfs[0][2]
                master_ins = ins_dfs[0][0]
                if is_cat_all:
                    for g, y, _ in ins_dfs[1:]: master_ins = pd.merge(master_ins, g, on=c_master_key, how="outer")
                else:
                    c_desc = hierarchy_cols["Desc"]
                    for g, y, _ in ins_dfs[1:]:
                        master_ins = pd.merge(master_ins, g, on=c_master_key, how="outer", suffixes=("", "_y"))
                        master_ins[c_desc] = master_ins[c_desc].fillna(master_ins[c_desc + "_y"])
                        master_ins = master_ins.drop(columns=[c_desc + "_y"])
                
                master_ins = master_ins.fillna(Decimal('0'))
                if not is_cat_all: master_ins = master_ins.rename(columns={c_master_key: "Code", c_desc: "Description"})
                
                disp_prefix = [c_master_key] if is_cat_all else ["Code", "Description"]
                cr_years = [y for _,y,_ in ins_dfs]
                y_newest, y1 = cr_years[-1], cr_years[-2]
                
                master_ins["Change_1_Raw"] = master_ins.apply(lambda x: clean_number(x.get(f"Net {y_newest}", Decimal('0'))) - clean_number(x.get(f"Net {y1}", Decimal('0'))), axis=1)
                master_ins[f"Change {y_newest} vs {y1}"] = master_ins["Change_1_Raw"].apply(to_display_num)
                master_ins[f"YoY {y_newest} vs {y1} (%)"] = master_ins.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0)), axis=1).apply(yoy_label)
                
                display_cols = disp_prefix + [f"Net {y}" for y in cr_years] + [f"Change {y_newest} vs {y1}", f"YoY {y_newest} vs {y1} (%)"]

                c1, c2 = st.columns(2)
                with c1:
                    st.write("#### Top 5 Growth" + (" Categories" if is_cat_all else " SKUs"))
                    growth = master_ins[master_ins["Change_1_Raw"] > 0].sort_values("Change_1_Raw", ascending=False).head(5)
                    if not growth.empty:
                        disp = growth.copy()
                        for y in cr_years: disp[f"Net {y}"] = disp.get(f"Net {y}").apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols]))
                    else: st.info("No growth found.")
                with c2:
                    st.write("#### Top 5 Decline" + (" Categories" if is_cat_all else " SKUs"))
                    decline = master_ins[master_ins["Change_1_Raw"] < 0].sort_values("Change_1_Raw", ascending=True).head(5)
                    if not decline.empty:
                        disp = decline.copy()
                        for y in cr_years: disp[f"Net {y}"] = disp.get(f"Net {y}").apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols]))
                    else: st.success("No decline found.")

# ================= TAB: COUNTRY REVIEW =================
with tab_country:
    st.header("🌍 Country Review")
    if not [d for d in [df_curr, df_prev, df_old2] if d is not None]: st.warning("Upload data.")
    else:
        df_all_co = pd.concat([d for d in [df_curr, df_prev, df_old2] if d is not None], ignore_index=True)
        c1, c2, c3 = st.columns(3)
        m_co = {"prefix": "co", "customer": "All Customers", "country": "All Countries"} # Virtual for get_filtered
        m_co["category"] = c1.selectbox("📦 Category", ["All Categories"] + sorted(df_all_co[hierarchy_cols["Cat"]].dropna().unique().tolist()), key="co_ca")
        m_co["brand"] = c2.selectbox("🏷️ Brand", ["All Brands"] + sorted(df_all_co[hierarchy_cols["Brand"]].dropna().unique().tolist()), key="co_br")
        m_co["months"] = c3.multiselect("📅 Months", MONTHS_ORDER, default=hierarchy_months or MONTHS_ORDER, key="co_mo")

        v_dfs_raw = get_filtered_cr_dfs(m_co)
        v_dfs = []
        for d, y, c in v_dfs_raw:
            d = d[~d[c["Country"]].astype(str).str.lower().str.strip().isin(["romania", "spain", "united kingdom"])]
            if not d.empty: v_dfs.append((d, y, c))

        if not v_dfs: st.warning("No data.")
        else:
            st.divider(); st.markdown("### Net Value Comparison")
            rows = [{"Year": y, "Country": r[c["Country"]], "Net": float(r[c["Net"]])} for d, y, c in v_dfs for _, r in d.groupby(c["Country"]).agg({c["Net"]: sum_decimal}).reset_index().iterrows() if float(r[c["Net"]]) != 0]
            if rows: 
                chart_df = pd.DataFrame(rows)
                # Ensure sort order by latest year
                d_latest, y_latest, c_latest = v_dfs[-1]
                g_latest = d_latest.groupby(c_latest["Country"]).agg({c_latest["Net"]: sum_decimal}).reset_index()
                country_order = sort_by_col_desc(g_latest, c_latest["Net"])[c_latest["Country"]].tolist()
                
                fig = px.bar(chart_df, x="Country", y="Net", color="Year", barmode="group", category_orders={"Country": country_order}, text_auto='.2s', color_discrete_map=GLOBAL_COLOR_MAP)
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            
            master_co = pd.merge(*(d.groupby(c["Country"]).agg({c["Net"]: sum_decimal, c["Qty"]: sum_decimal}).reset_index().rename(columns={c["Country"]: "Country", c["Net"]: f"Net {y}", c["Qty"]: f"Qty {y}"}) for d,y,c in v_dfs), on="Country", how="outer").fillna(Decimal('0'))
            y_n_str = v_dfs[-1][1]
            master_co = sort_by_col_desc(master_co, f"Net {y_n_str}")
            
            st.markdown("### Country Performance (L4L)")
            cols_disp = ["Country"]
            for _, y, _ in v_dfs: cols_disp.extend([f"Net {y}", f"Qty {y}"])
            if len(v_dfs)>=2:
                y_o_str = v_dfs[-2][1]
                master_co[f"YoY {y_n_str} vs {y_o_str} (%)"] = master_co.apply(lambda x: yoy_label(yoy_calc(x.get(f"Net {y_n_str}",0), x.get(f"Net {y_o_str}",0))), axis=1)
                cols_disp.append(f"YoY {y_n_str} vs {y_o_str} (%)")
            
            m_disp = master_co.copy()
            for col in master_co.columns:
                if "Net" in col or "Qty" in col: m_disp[col] = m_disp[col].apply(to_display_num)
            st.dataframe(add_index(m_disp[cols_disp]), use_container_width=True)

            st.divider(); st.markdown("### Country Market Share")
            pies = st.columns(len(v_dfs))
            for i, (_, y, _) in enumerate(v_dfs):
                p_df = master_co.copy()
                p_df[f"Net {y}"] = p_df[f"Net {y}"].apply(lambda v: max(0, float(clean_number(v))))
                if p_df[f"Net {y}"].sum() > 0:
                    p_df.loc[p_df[f"Net {y}"] / p_df[f"Net {y}"].sum() < 0.005, "Country"] = "Other"
                    p_df = p_df.groupby("Country", as_index=False)[[f"Net {y}"]].sum()
                with pies[i]: st.plotly_chart(px.pie(p_df, names="Country", values=f"Net {y}", title=f"Share {y}", color="Country", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

            st.divider(); st.markdown("### Auto Insights (Country Focus)")
            if len(v_dfs) >= 2:
                ins_master_co = master_co.copy()
                y1_str = v_dfs[-2][1]
                ins_master_co["Change_Raw"] = ins_master_co.apply(lambda x: clean_number(x.get(f"Net {y_n_str}", Decimal('0'))) - clean_number(x.get(f"Net {y1_str}", Decimal('0'))), axis=1)
                ins_master_co[f"Change {y_n_str} vs {y1_str}"] = ins_master_co["Change_Raw"].apply(to_display_num)
                
                disp_prefix_co = ["Country"]
                co_years = [y for _,y,_ in v_dfs]
                display_cols_ins = disp_prefix_co + [f"Net {y}" for y in co_years] + [f"Change {y_n_str} vs {y1_str}", f"YoY {y_n_str} vs {y1_str} (%)"]

                c1, c2 = st.columns(2)
                with c1:
                    st.write("#### Top 5 Growth Countries")
                    growth = ins_master_co[ins_master_co["Change_Raw"] > 0].sort_values("Change_Raw", ascending=False).head(5)
                    if not growth.empty:
                        disp = growth.copy()
                        for y in co_years: disp[f"Net {y}"] = disp.get(f"Net {y}").apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols_ins]))
                    else: st.info("No growth found.")
                with c2:
                    st.write("#### Top 5 Decline Countries")
                    decline = ins_master_co[ins_master_co["Change_Raw"] < 0].sort_values("Change_Raw", ascending=True).head(5)
                    if not decline.empty:
                        disp = decline.copy()
                        for y in co_years: disp[f"Net {y}"] = disp.get(f"Net {y}").apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols_ins]))
                    else: st.success("No decline found.")

# ================= TAB: BRAND REVIEW =================
with tab_brand:
    st.header("🏷️ Brand / License Review")
    if not [d for d in [df_curr, df_prev, df_old2] if d is not None]: st.warning("Upload data.")
    else:
        df_all_br = pd.concat([d for d in [df_curr, df_prev, df_old2] if d is not None], ignore_index=True)
        c1, c2, c3, c4 = st.columns(4)
        m_br = {"prefix": "br"}
        m_br["country"] = c1.selectbox("🌎 Country", ["All Countries"] + sorted(df_all_br[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist()), key="br_co")
        m_br["customer"] = c2.selectbox("🏢 Customer", ["All Customers"] + sorted(df_all_br[df_all_br[hierarchy_cols["Country"]]==m_br["country"] if m_br["country"]!="All Countries" else df_all_br][hierarchy_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist()), key="br_cu")
        m_br["category"] = c3.selectbox("📦 Category", ["All Categories"] + sorted(df_all_br[hierarchy_cols["Cat"]].dropna().unique().tolist()), key="br_ca")
        m_br["brand"] = c4.selectbox("🏷️ Brand", ["All Brands"] + sorted(df_all_br[hierarchy_cols["Brand"]].dropna().unique().tolist()), key="br_br")
        m_br["months"] = st.multiselect("📅 Months", MONTHS_ORDER, default=hierarchy_months or MONTHS_ORDER, key="br_mo")

        if m_br["brand"] == "All Brands": st.info("⚠️ Select a specific Brand.")
        else:
            v_dfs = get_filtered_cr_dfs(m_br)
            st.markdown(f"### KPI (Current vs Previous) - {m_br['brand']}")
            if len(v_dfs) >= 2:
                d_n, y_n, c_n = v_dfs[-1]
                d_o, y_o, c_o = v_dfs[-2]
                k1, k2, k3, k4 = st.columns(4)
                k1.metric(f"Net {y_o}", format_number_plain(sum_decimal(d_o[c_o["Net"]])))
                k2.metric(f"Net {y_n}", format_number_plain(sum_decimal(d_n[c_n["Net"]])), yoy_label(yoy_calc(sum_decimal(d_n[c_n["Net"]]), sum_decimal(d_o[c_o["Net"]]))))
                k3.metric(f"Qty {y_o}", format_number_plain(sum_decimal(d_o[c_o["Qty"]])))
                k4.metric(f"Qty {y_n}", format_number_plain(sum_decimal(d_n[c_n["Qty"]])), yoy_label(yoy_calc(sum_decimal(d_n[c_n["Qty"]]), sum_decimal(d_o[c_o["Qty"]]))))
            else: st.info("Not enough data.")
            
            st.divider(); render_monthly_comparison(v_dfs, m_br, "Net")
            st.divider(); render_monthly_comparison(v_dfs, m_br, "Qty")
            
            if v_dfs:
                st.divider(); st.markdown("### Net Value Comparison")
                st.plotly_chart(px.bar(pd.DataFrame([{"Year": y, "Net": float(sum_decimal(d[c["Net"]]))} for d, y, c in v_dfs]), x="Year", y="Net", color="Year", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                st.divider(); st.markdown("### Market Penetration (Countries & Customers)")
                d_latest, y_latest, c_latest = v_dfs[-1]
                
                g_country = d_latest.groupby(c_latest["Country"]).agg({c_latest["Net"]: sum_decimal}).reset_index()
                g_country[f"Net {y_latest}"] = g_country[c_latest["Net"]].apply(lambda x: float(clean_number(x)))
                if g_country[f"Net {y_latest}"].sum() > 0:
                    g_country['Share'] = g_country[f"Net {y_latest}"] / g_country[f"Net {y_latest}"].sum()
                    g_country.loc[g_country['Share'] < 0.01, c_latest["Country"]] = 'Other'
                    g_country = g_country.groupby(c_latest["Country"], as_index=False)[[f"Net {y_latest}"]].sum()
                
                g_cust = d_latest.groupby(c_latest["Customer"]).agg({c_latest["Net"]: sum_decimal}).reset_index()
                g_cust[f"Net {y_latest}"] = g_cust[c_latest["Net"]].apply(lambda x: float(clean_number(x)))
                if g_cust[f"Net {y_latest}"].sum() > 0:
                    g_cust['Share'] = g_cust[f"Net {y_latest}"] / g_cust[f"Net {y_latest}"].sum()
                    g_cust.loc[g_cust['Share'] < 0.01, c_latest["Customer"]] = 'Other'
                    g_cust = g_cust.groupby(c_latest["Customer"], as_index=False)[[f"Net {y_latest}"]].sum()
                
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    st.write(f"#### Top Countries ({y_latest})")
                    st.plotly_chart(px.pie(g_country, names=c_latest["Country"], values=f"Net {y_latest}", color=c_latest["Country"], color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)
                with c_p2:
                    st.write(f"#### Top Customers ({y_latest})")
                    st.plotly_chart(px.pie(g_cust, names=c_latest["Customer"], values=f"Net {y_latest}", color=c_latest["Customer"], color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                st.divider(); st.markdown(f"### Top 10 SKUs for {m_br['brand']}")
                sku_df = sort_by_col_desc(d_latest.groupby(c_latest["Code"]).agg({c_latest["Desc"]: "first", c_latest["Net"]: sum_decimal, c_latest["Qty"]: sum_decimal}).reset_index(), c_latest["Net"]).head(10)
                sku_disp = sku_df.copy()
                sku_disp[c_latest["Net"]] = sku_disp.get(c_latest["Net"]).apply(to_display_num)
                sku_disp[c_latest["Qty"]] = sku_disp.get(c_latest["Qty"]).apply(to_display_num)
                sku_disp = sku_disp.rename(columns={c_latest["Code"]: "Code", c_latest["Desc"]: "Description", c_latest["Net"]: f"Net {y_latest}", c_latest["Qty"]: f"Qty {y_latest}"})
                st.dataframe(add_index(sku_disp[["Code", "Description", f"Net {y_latest}", f"Qty {y_latest}"]]), use_container_width=True)

# ================= TAB: CUSTOMER CHURN & ACQUISITION =================
with tab_churn:
    st.header("⚠️ Customer Churn & Acquisition")
    if len([d for d in [df_curr, df_prev, df_old2] if d is not None]) < 2: st.warning("Need 2 years data.")
    else:
        st.info("ℹ️ Compares the **Newest Year** vs the **Previous Year** based on selected months. \n* **New Customer:** Sales > 0 in New Year, and 0 in Previous Year.\n* **Lost Customer:** Sales > 0 in Previous Year, and <= 0 in New Year.")
        df_all_ch = pd.concat([d for d in [df_curr, df_prev, df_old2] if d is not None], ignore_index=True)
        c1, c2, c3, c4 = st.columns(4)
        m_ch = {"prefix": "ch", "customer": "All Customers"}
        m_ch["country"] = c1.selectbox("🌎 Country", ["All Countries"] + sorted(df_all_ch[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist()), key="ch_co")
        m_ch["category"] = c2.selectbox("📦 Category", ["All Categories"] + sorted(df_all_ch[hierarchy_cols["Cat"]].dropna().unique().tolist()), key="ch_ca")
        m_ch["brand"] = c3.selectbox("🏷️ Brand", ["All Brands"] + sorted(df_all_ch[hierarchy_cols["Brand"]].dropna().unique().tolist()), key="ch_br")
        m_ch["months"] = c4.multiselect("📅 Months", MONTHS_ORDER, default=hierarchy_months or MONTHS_ORDER, key="ch_mo")

        v_dfs = get_filtered_cr_dfs(m_ch)
        if len(v_dfs) >= 2:
            d_n, y_n, c_n = v_dfs[-1]
            d_o, y_o, c_o = v_dfs[-2]
            
            g_n = d_n.groupby(c_n["Customer"]).agg({c_n["Net"]: sum_decimal}).reset_index().rename(columns={c_n["Customer"]: "Customer", c_n["Net"]: "Net_New"})
            g_o = d_o.groupby(c_o["Customer"]).agg({c_o["Net"]: sum_decimal}).reset_index().rename(columns={c_o["Customer"]: "Customer", c_o["Net"]: "Net_Old"})
            
            m_ch_df = pd.merge(g_n, g_o, on="Customer", how="outer").fillna(Decimal('0'))
            m_ch_df['Status'] = 'Retained'
            m_ch_df.loc[(m_ch_df['Net_Old'] <= Decimal('0')) & (m_ch_df['Net_New'] > Decimal('0')), 'Status'] = 'New'
            m_ch_df.loc[(m_ch_df['Net_Old'] > Decimal('0')) & (m_ch_df['Net_New'] <= Decimal('0')), 'Status'] = 'Lost'
            
            df_new_c = m_ch_df[m_ch_df['Status'] == 'New'].copy()
            df_lost_c = m_ch_df[m_ch_df['Status'] == 'Lost'].copy()
            
            v_acq = df_new_c['Net_New'].sum()
            v_los = df_lost_c['Net_Old'].sum()
            
            st.divider(); st.markdown(f"### KPIs ({y_o} ➔ {y_n})")
            k1, k2, k3 = st.columns(3)
            k1.metric("Acquired Value", f"{format_number_plain(v_acq)} EUR", f"{len(df_new_c)} Customers")
            k2.metric("Lost Value", f"{format_number_plain(v_los)} EUR", f"-{len(df_lost_c)} Customers", delta_color="normal")
            k3.metric("Net Flow", f"{format_number_plain(v_acq - v_los)} EUR", delta_color="normal" if v_acq - v_los >= 0 else "inverse")
            
            st.divider()
            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown(f"#### 🟢 Top 10 New Customers ({y_n})")
                disp = df_new_c.sort_values("Net_New", ascending=False).head(10)[["Customer", "Net_New"]].copy()
                disp["Net_New"] = disp["Net_New"].apply(to_display_num)
                st.dataframe(add_index(disp.rename(columns={"Net_New": f"Net {y_n} (EUR)"})), use_container_width=True) if not disp.empty else st.info("None.")
            with col_r:
                st.markdown(f"#### 🔴 Top 10 Lost Customers (0 in {y_n})")
                disp = df_lost_c.sort_values("Net_Old", ascending=False).head(10)[["Customer", "Net_Old"]].copy()
                disp["Net_Old"] = disp["Net_Old"].apply(to_display_num)
                st.dataframe(add_index(disp.rename(columns={"Net_Old": f"Lost Net {y_o} (EUR)"})), use_container_width=True) if not disp.empty else st.success("None!")
        else: st.info("Need 2 valid years for the selected filters.")
