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
    if isinstance(x, (int, float)):
        try:
            return Decimal(str(x))
        except (InvalidOperation, Exception):
            return Decimal('0')
    s = str(x).strip()
    if not s or s.lower() in ["nan", "none", "null", ""]:
        return Decimal('0')
    
    # Czyszczenie spacji, twardych spacji oraz minusem w unicode
    s = s.replace("\xa0", "").replace("\u202f", "").replace(" ", "")
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    
    # Obsługa notacji nawiasowej (293,04) -> -293,04
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    # Obsługa minusa na końcu liczby 293,04- -> -293,04
    elif s.endswith("-") and not s.startswith("-"):
        s = "-" + s[:-1]
        
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
SPANISH_PALETTE = [
    "#40407a", "#706fd3", "#34ace0", "#33d9b2", "#2c2c54",
    "#474787", "#aaa69d", "#227093", "#218c74", "#ff5252",
    "#ff793f", "#d1ccc0", "#ffb142", "#ffda79", "#b33939",
    "#cd6133", "#84817a", "#cc8e35", "#ccae62"
]

def normalize_month(x) -> str:
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


def apply_shared_filters(dfs, cols, unique_prefix: str, default_months=None, show_months=True, hm_sig=""):
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
        default_m = [m for m in (default_months or []) if m in options_m]
        if not default_m:
            default_m = options_m
            
        key_months = f"{unique_prefix}_months_{hm_sig}"
        label_m = f"📅 Months ({len(default_m)} active)"
        
        selected_months = c4.multiselect(label_m, options=options_m, default=default_m, key=key_months)
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

    # L4L TABLE
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

    # AUTO INSIGHTS
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

    # CUSTOMER IMPACT SECTION
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


# ================= MAIN APP INITIALIZATION =================
st.set_page_config(layout="wide", page_title="Sales Intelligence Dashboard")
st.title("📊 Sales Intelligence Dashboard")

if 'file_uploader_key' not in st.session_state:
    st.session_state['file_uploader_key'] = 0

def update_cached_file(file_obj, state_key, label):
    if file_obj is None:
        st.session_state[state_key] = (None, None, None)
        st.session_state[f"{state_key}_id"] = None
    elif st.session_state.get(f"{state_key}_id") != file_obj.file_id:
        file_obj.seek(0)
        st.session_state[state_key] = load_single_year_file(file_obj, label)
        st.session_state[f"{state_key}_id"] = file_obj.file_id
        
        # Clear filter keys to avoid "State Stickiness"
        keys_to_del = [k for k in st.session_state.keys() if "_months_" in k]
        for k in keys_to_del:
            del st.session_state[k]

if 'data_older' not in st.session_state: st.session_state['data_older'] = (None, None, None)
if 'data_prev' not in st.session_state: st.session_state['data_prev'] = (None, None, None)
if 'data_curr' not in st.session_state: st.session_state['data_curr'] = (None, None, None)

col_title, col_reset = st.columns([8, 2])
with col_title:
    st.markdown("### Excel Upload (3 separate years)")
with col_reset:
    st.write("") # spacer
    if st.button("🗑️ Reset All Data", use_container_width=True):
        for key in ['data_older', 'data_prev', 'data_curr']:
            st.session_state[key] = (None, None, None)
            st.session_state[f"{key}_id"] = None
        
        keys_to_del = [k for k in st.session_state.keys() if "_months" in k or "last_hm_str" in k]
        for k in keys_to_del: 
            del st.session_state[k]
            
        st.session_state['file_uploader_key'] += 1
        st.rerun()

c_up1, c_up2, c_up3 = st.columns(3)
with c_up1:
    f1 = st.file_uploader("Older Year (2 years ago)", type=["xlsx"], key=f"up1_{st.session_state['file_uploader_key']}")
    update_cached_file(f1, 'data_older', "older")
with c_up2:
    f2 = st.file_uploader("Previous Year", type=["xlsx"], key=f"up2_{st.session_state['file_uploader_key']}")
    update_cached_file(f2, 'data_prev', "prev")
with c_up3:
    f3 = st.file_uploader("Current Year (YTD)", type=["xlsx"], key=f"up3_{st.session_state['file_uploader_key']}")
    update_cached_file(f3, 'data_curr', "curr")

df_old2, cols_old2, year_old2 = st.session_state['data_older']
df_prev, cols_prev, year_prev = st.session_state['data_prev']
df_curr, cols_curr, year_curr = st.session_state['data_curr']

if df_prev is None and df_curr is None and df_old2 is None:
    st.info("Upload at least one Excel file.")
    st.stop()

# MAP YEARS GLOBALLY
year_options = []
year_map_df = {}
year_map_cols = {}

if df_old2 is not None:
    year_options.append(year_old2)
    year_map_df[year_old2] = df_old2
    year_map_cols[year_old2] = cols_old2
if df_prev is not None:
    year_options.append(year_prev)
    year_map_df[year_prev] = df_prev
    year_map_cols[year_prev] = cols_prev
if df_curr is not None:
    year_options.append(year_curr)
    year_map_df[year_curr] = df_curr
    year_map_cols[year_curr] = cols_curr

year_options = sorted(list(set(year_options)))

# GLOBAL COLOR MAP GENERATION
GLOBAL_COLOR_MAP = {"Other": "#808080"}
all_loaded_dfs_for_colors = [d for d in [df_curr, df_prev, df_old2] if d is not None]

if len(all_loaded_dfs_for_colors) > 0:
    all_categories = set()
    all_brands = set()
    all_countries = set()
    all_customers = set()
    all_years = []
    
    for d, c, y in zip([df_old2, df_prev, df_curr], [cols_old2, cols_prev, cols_curr], [year_old2, year_prev, year_curr]):
        if d is not None:
            all_categories.update(d[c["Cat"]].dropna().unique())
            all_brands.update(d[c["Brand"]].dropna().unique())
            all_countries.update(d[c["Country"]].dropna().unique())
            all_customers.update(d[c["Customer"]].dropna().unique())
            if str(y) not in all_years:
                all_years.append(str(y))
                
    all_categories = sorted(list(all_categories))
    all_brands = sorted(list(all_brands))
    all_countries = sorted(list(all_countries))
    all_customers = sorted(list(all_customers))
    
    year_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, y in enumerate(all_years):
        GLOBAL_COLOR_MAP[y] = year_colors[i % len(year_colors)]
        
    palette = SPANISH_PALETTE
    
    c_idx = 0
    for item in all_categories + all_brands + all_countries + all_customers:
        if item not in GLOBAL_COLOR_MAP:
            GLOBAL_COLOR_MAP[item] = palette[c_idx % len(palette)]
            c_idx += 1

st.divider()

# TABS DECLARATION IN REORDERED STRUCTURE
tab_cust_sales, tab_customer, tab_overview, tab_country, tab_category, tab_brand, tab_l4l = st.tabs([
    "💰 Customers Sales", "👥 Customer Review", "📈 Overview — 3-year Comparison", "🌍 Country Review", "📁 Category Review", "🏷️ Brand Review", "📅 Detailed L4L"
])

hierarchy_df, hierarchy_cols = None, None
if df_curr is not None and not df_curr.empty: 
    hierarchy_df, hierarchy_cols = df_curr, cols_curr
elif df_prev is not None and not df_prev.empty: 
    hierarchy_df, hierarchy_cols = df_prev, cols_prev
elif df_old2 is not None and not df_old2.empty: 
    hierarchy_df, hierarchy_cols = df_old2, cols_old2

hierarchy_months = []
if hierarchy_df is not None:
    hm_raw = hierarchy_df[hierarchy_cols["Month"]].dropna().unique().tolist()
    hierarchy_months = sorted([m for m in hm_raw if m in MONTHS_ORDER], key=lambda x: MONTHS_ORDER.index(x))

hm_sig = "".join([m[:3] for m in hierarchy_months]) if hierarchy_months else "default"

if st.session_state.get('last_hm_str') != hm_sig:
    keys_to_reset = [k for k in st.session_state.keys() if "_months_" in k]
    for k in keys_to_reset:
        del st.session_state[k]
    st.session_state['last_hm_str'] = hm_sig

st.sidebar.info(f"ℹ️ Default months detected: {', '.join(hierarchy_months) if hierarchy_months else 'None'}")

def style_monthly_table(df):
    def color_cells(s):
        if "∆" in str(s.get('Year', '')):
            row_colors = []
            for col in df.columns:
                val = s[col]
                if col == "Year":
                    row_colors.append("")
                else:
                    if isinstance(val, str) and "🟢" in val:
                        row_colors.append("background-color: rgba(144, 238, 144, 0.4); color: black;")
                    elif isinstance(val, str) and "🔴" in val:
                        row_colors.append("background-color: rgba(255, 182, 193, 0.4); color: black;")
                    else:
                        row_colors.append("")
            return row_colors
        else:
            return [""] * len(s)
    return df.style.apply(color_cells, axis=1)


# ================= TAB 1: CUSTOMERS SALES =================
with tab_cust_sales:
    st.header("💰 Customers Sales")
    year_options_cs = []
    year_to_df = {}
    year_to_cols = {}

    if df_old2 is not None:
        year_options_cs.append(year_old2)
        year_to_df[year_old2] = df_old2
        year_to_cols[year_old2] = cols_old2
    if df_prev is not None:
        year_options_cs.append(year_prev)
        year_to_df[year_prev] = df_prev
        year_to_cols[year_prev] = cols_prev
    if df_curr is not None:
        year_options_cs.append(year_curr)
        year_to_df[year_curr] = df_curr
        year_to_cols[year_curr] = cols_curr

    if not year_options_cs:
        st.warning("Please upload data.")
    else:
        # --- FILTRY KRAJU I MIESIĘCY ---
        df_all_cs = pd.concat([year_to_df[y] for y in year_options_cs], ignore_index=True)
        cs_c1, cs_c2 = st.columns(2)
        
        countries_cs = ["All Countries"] + sorted(df_all_cs[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_cs = cs_c1.selectbox("🌎 Country", countries_cs, key="cs_country")

        options_cs_m = MONTHS_ORDER
        default_cs_m = [m for m in hierarchy_months if m in options_cs_m]
        if not default_cs_m:
            default_cs_m = options_cs_m
        
        key_cs_mo = f"cs_months_{hm_sig}"
        label_cs_m = f"📅 Months ({len(default_cs_m)} active)"
        selected_months_cs = cs_c2.multiselect(label_cs_m, options=options_cs_m, default=default_cs_m, key=key_cs_mo)
        
        def filter_df_cs(d_f, c):
            if d_f is None: return None
            res = d_f.copy()
            if selected_country_cs != "All Countries":
                res = res[res[c["Country"]] == selected_country_cs]
            if selected_months_cs:
                res = res[res[c["Month"]].isin(selected_months_cs)]
            return res

        sorted_years_cs = sorted(list(set(year_options_cs)))
        selected_year = st.selectbox("Select Year", list(reversed(sorted_years_cs)), index=0, key="cust_sales_year")
        
        df_sel = filter_df_cs(year_to_df[selected_year], year_to_cols[selected_year])
        cols_sel = year_to_cols[selected_year]
        
        st.markdown(f"### Customers Sales in {selected_year}")
        
        cust_col = cols_sel["Customer"]
        net_col = cols_sel["Net"]
        
        cust_sales = df_sel.groupby(cust_col).agg({net_col: sum_decimal}).reset_index()
        
        idx = sorted_years_cs.index(selected_year)
        has_prev = idx > 0
        
        if has_prev:
            prev_y = sorted_years_cs[idx - 1]
            df_prev_yr = filter_df_cs(year_to_df[prev_y], year_to_cols[prev_y])
            c_prev = year_to_cols[prev_y]
            
            cust_sales_prev = df_prev_yr.groupby(c_prev["Customer"]).agg({
                c_prev["Net"]: sum_decimal
            }).reset_index().rename(columns={c_prev["Customer"]: cust_col, c_prev["Net"]: "Net_Old"})
            
            cust_sales = pd.merge(cust_sales, cust_sales_prev, on=cust_col, how="left").fillna(Decimal('0'))
            cust_sales["Change Value Raw"] = cust_sales[net_col] - cust_sales["Net_Old"]
            cust_sales["YoY (%)"] = cust_sales.apply(lambda x: yoy_label(yoy_calc(x[net_col], x["Net_Old"])), axis=1)
        
        cust_sales = sort_by_col_desc(cust_sales, net_col)
        disp_cust = cust_sales.copy()
        
        net_curr_label = f"Net {selected_year}"
        disp_cust[net_curr_label] = disp_cust[net_col].apply(to_display_num)
        
        if has_prev:
            net_prev_label = f"Net {prev_y}"
            disp_cust[net_prev_label] = disp_cust["Net_Old"].apply(to_display_num)
            disp_cust["Change Value"] = cust_sales["Change Value Raw"].apply(to_display_num)
            display_cols = [cust_col, net_prev_label, net_curr_label, "Change Value", "YoY (%)"]
        else:
            display_cols = [cust_col, net_curr_label]
            
        st.dataframe(add_index(disp_cust[display_cols]), use_container_width=True)
        
        st.markdown(f"### Customer Sales Distribution ({selected_year})")
        plot_df = cust_sales.copy()
        plot_df[net_col] = plot_df[net_col].apply(lambda x: max(0, float(clean_number(x))))
        
        tot = plot_df[net_col].sum()
        if tot > 0:
            plot_df.loc[plot_df[net_col] / tot < 0.01, cust_col] = 'Other'
            plot_df = plot_df.groupby(cust_col, as_index=False)[[net_col]].sum()
            
        st.plotly_chart(px.pie(plot_df, names=cust_col, values=net_col, color=cust_col, color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)
        
        st.divider()
        st.markdown("### Customer Impact (Growth vs Decline)")
        if len(sorted_years_cs) >= 2:
            if idx > 0:
                prev_year = sorted_years_cs[idx - 1]
                st.write(f"Comparing {selected_year} vs {prev_year}")
                
                df_new = filter_df_cs(year_to_df[selected_year], year_to_cols[selected_year])
                df_old = filter_df_cs(year_to_df[prev_year], year_to_cols[prev_year])
                cols_new = year_to_cols[selected_year]
                cols_old = year_to_cols[prev_year]
                
                c_col_new, net_new = cols_new["Customer"], cols_new["Net"]
                c_col_old, net_old = cols_old["Customer"], cols_old["Net"]
                
                cust_new_df = df_new.groupby(c_col_new).agg({net_new: sum_decimal}).reset_index().rename(columns={net_new: f"Net {selected_year}", c_col_new: "Customer"})
                cust_old_df = df_old.groupby(c_col_old).agg({net_old: sum_decimal}).reset_index().rename(columns={net_old: f"Net {prev_year}", c_col_old: "Customer"})
                
                impact = pd.merge(cust_new_df, cust_old_df, on="Customer", how="outer").fillna(Decimal('0'))
                
                impact["Change Value Raw"] = impact.get(f"Net {selected_year}", Decimal('0')) - impact.get(f"Net {prev_year}", Decimal('0'))
                impact["Special Case"] = (impact.get(f"Net {prev_year}", Decimal('0')) < 0) & (impact.get(f"Net {selected_year}", Decimal('0')) == 0)
                impact["YoY"] = impact.apply(lambda x: yoy_calc(x.get(f"Net {selected_year}", 0), x.get(f"Net {prev_year}", 0)), axis=1) if not impact.empty else []
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write("#### Top Growth Drivers")
                    growth_imp = impact[(impact["Change Value Raw"] > 0) & (~impact["Special Case"])].sort_values("Change Value Raw", ascending=False).head(10)
                    growth_special = impact[impact["Special Case"]].head(10)
                    growth_imp = pd.concat([growth_imp, growth_special])
                    if growth_imp.empty:
                        st.info("No growth generated by customers.")
                    else:
                        g_disp = growth_imp.copy()
                        g_disp[f"Net {prev_year}"] = g_disp[f"Net {prev_year}"].apply(to_display_num)
                        g_disp[f"Net {selected_year}"] = g_disp[f"Net {selected_year}"].apply(to_display_num)
                        g_disp["Change Value"] = g_disp["Change Value Raw"].apply(to_display_num)
                        g_disp["YoY (%)"] = g_disp["YoY"].apply(yoy_label)
                        st.dataframe(add_index(g_disp[["Customer", f"Net {prev_year}", f"Net {selected_year}", "Change Value", "YoY (%)"]]))
                
                with c2:
                    st.write("#### Top Decline Drivers")
                    decline_imp = impact[impact["Change Value Raw"] < 0].sort_values("Change Value Raw").head(10)
                    if decline_imp.empty:
                        st.success("No decline across customers.")
                    else:
                        d_disp = decline_imp.copy()
                        d_disp[f"Net {prev_year}"] = d_disp[f"Net {prev_year}"].apply(to_display_num)
                        d_disp[f"Net {selected_year}"] = d_disp[f"Net {selected_year}"].apply(to_display_num)
                        d_disp["Change Value"] = d_disp["Change Value Raw"].apply(to_display_num)
                        d_disp["YoY (%)"] = d_disp["YoY"].apply(yoy_label)
                        st.dataframe(add_index(d_disp[["Customer", f"Net {prev_year}", f"Net {selected_year}", "Change Value", "YoY (%)"]]))
            else:
                st.info(f"No previous year data available to compare with {selected_year}.")


# ================= TAB: CUSTOMER REVIEW =================
with tab_customer:
    st.header("👥 Customer Review")
    
    dfs_cr = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_cr) < 1:
        st.warning("Please upload data.")
    else:
        df_all_cr = pd.concat(dfs_cr, ignore_index=True)
        
        c1, c2, c3, c4 = st.columns(4)
        
        countries_cr = ["All Countries"] + sorted(df_all_cr[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_cr = c1.selectbox("🌎 Country", countries_cr, key="cr_country")

        df_for_customers_cr = df_all_cr.copy()
        if selected_country_cr != "All Countries":
            df_for_customers_cr = df_for_customers_cr[df_for_customers_cr[hierarchy_cols["Country"]] == selected_country_cr]

        customers_cr = ["All Customers"] + sorted(df_for_customers_cr[hierarchy_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
        selected_customer_cr = c2.selectbox("🏢 Customer", customers_cr, key="cr_customer")

        categories_cr = ["All Categories"] + sorted(df_for_customers_cr[hierarchy_cols["Cat"]].dropna().unique().tolist())
        selected_category_cr = c3.selectbox("📦 Category", categories_cr, key="cr_category")

        options_cr_m = MONTHS_ORDER 
        default_cr_m = [m for m in hierarchy_months if m in options_cr_m]
        if not default_cr_m:
            default_cr_m = options_cr_m
            
        key_cr_mo = f"cr_months_{hm_sig}"
        label_cr_m = f"📅 Months ({len(default_cr_m)} active)"
        selected_months_cr = c4.multiselect(label_cr_m, options=options_cr_m, default=default_cr_m, key=key_cr_mo)

        meta_cr = {
            "country": selected_country_cr,
            "customer": selected_customer_cr,
            "category": selected_category_cr,
            "months": selected_months_cr
        }
        
        if meta_cr["customer"] == "All Customers":
            st.info("⚠️ Please select a specific customer from the filter above to view the dedicated analysis in this tab.")
        else:
            st.markdown("### KPI (Current vs Previous)")
            cr_valid_dfs = []
            for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                if orig_d is not None:
                    d_f = orig_d.copy()
                    if meta_cr["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cr["country"]]
                    if meta_cr["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cr["customer"]]
                    if meta_cr["category"] != "All Categories": d_f = d_f[d_f[c["Cat"]] == meta_cr["category"]]
                    if meta_cr["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_cr["months"])] 
                    
                    if not d_f.empty:
                        cr_valid_dfs.append((d_f, y, c))
            
            cr_valid_dfs_chrono = sorted(cr_valid_dfs, key=lambda x: x[1])

            if len(cr_valid_dfs_chrono) >= 2:
                d_new, y_new, c_new = cr_valid_dfs_chrono[-1]
                d_old, y_old, c_old = cr_valid_dfs_chrono[-2]

                st.markdown(f"**Comparing Performance:** Year {y_old} vs Year {y_new}")
                s_new_net = sum_decimal(d_new[c_new["Net"]])
                s_old_net = sum_decimal(d_old[c_old["Net"]])
                s_new_qty = sum_decimal(d_new[c_new["Qty"]])
                s_old_qty = sum_decimal(d_old[c_old["Qty"]])

                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric(f"Net {y_old} (EUR)", format_number_plain(s_old_net))
                kc2.metric(f"Net {y_new} (EUR)", format_number_plain(s_new_net), yoy_label(yoy_calc(s_new_net, s_old_net)))
                kc3.metric(f"Qty {y_old} (PCS)", format_number_plain(s_old_qty))
                kc4.metric(f"Qty {y_new} (PCS)", format_number_plain(s_new_qty), yoy_label(yoy_calc(s_new_qty, s_old_qty)))
            else:
                st.info("Not enough data to calculate comparison KPIs (need at least 2 years).")
                
            st.divider()
            
            default_divisor = len(meta_cr["months"]) if meta_cr["months"] else 12
            st.info(f"ℹ️ Averages and Sums are calculated using {default_divisor} months based on your selected month filters above.")
            avg_divisor = st.slider("Select number of months for ∑ and AVG calculation (e.g. 3 = Jan, Feb, Mar):", min_value=1, max_value=12, value=default_divisor, step=1, key="cr_slider")

            def render_monthly_table(mode="Net"):
                st.markdown(f"### {mode} Value Monthly Comparison")
                
                col_key = "Net" if mode == "Net" else "Qty"
                sum_col_key = f"∑ (for {avg_divisor} months)"
                avg_col_key = "Avg Month"

                year_data = {}
                for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                    if orig_d is not None:
                        d_f = orig_d.copy()
                        if meta_cr["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cr["country"]]
                        if meta_cr["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cr["customer"]]
                        if meta_cr["category"] != "All Categories": d_f = d_f[d_f[c["Cat"]] == meta_cr["category"]]

                        m_vals = {}
                        for m in MONTHS_ORDER:
                            val = sum_decimal(d_f[d_f[c["Month"]] == m][c[col_key]])
                            m_vals[m] = val
                        
                        selected_months_for_avg = MONTHS_ORDER[:avg_divisor]
                        partial_sum = Decimal('0')
                        for m in selected_months_for_avg: partial_sum += m_vals[m]
                            
                        m_vals[sum_col_key] = partial_sum
                        m_vals[avg_col_key] = partial_sum / Decimal(str(avg_divisor))
                        year_data[y] = m_vals

                if not year_data: return

                available_years = sorted(list(year_data.keys()))
                display_rows = []
                col_keys = MONTHS_ORDER + [sum_col_key, avg_col_key]

                for y in available_years:
                    row = {"Year": str(y)}
                    for m in col_keys:
                        disp_name = SHORT_MONTHS.get(m, m)
                        row[disp_name] = to_display_num(year_data[y][m])
                    display_rows.append(row)

                if len(available_years) >= 2:
                    y_newest = available_years[-1]
                    y1 = available_years[-2]
                    row_yoy = {"Year": f"∆ {y_newest} vs {y1}"}
                    for m in col_keys:
                        disp_name = SHORT_MONTHS.get(m, m)
                        if m in meta_cr["months"] or m in [sum_col_key, avg_col_key]:
                            row_yoy[disp_name] = yoy_label(yoy_calc(year_data[y_newest][m], year_data[y1][m]))
                        else:
                            row_yoy[disp_name] = "n/a"
                    display_rows.append(row_yoy)

                df_disp = pd.DataFrame(display_rows)
                styled_df = style_monthly_table(df_disp)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

            render_monthly_table("Net")
            st.divider()
            render_monthly_table("Qty")

            st.divider()
            st.markdown("### Net Value Comparison")
            chart_vals = []
            for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                if orig_d is not None:
                    d_f = orig_d.copy()
                    if meta_cr["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cr["country"]]
                    if meta_cr["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cr["customer"]]
                    if meta_cr["category"] != "All Categories": d_f = d_f[d_f[c["Cat"]] == meta_cr["category"]]
                    if meta_cr["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_cr["months"])]
                    
                    if not d_f.empty:
                        chart_vals.append({"Year": str(y), "Net": float(sum_decimal(d_f[c["Net"]]))})
            
            if chart_vals:
                st.plotly_chart(px.bar(pd.DataFrame(chart_vals).sort_values("Year"), x="Year", y="Net", text="Net", color="Year", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

            def render_cr_sub_analysis(group_col_key, section_title, display_name):
                st.divider()
                st.markdown(f"### {section_title}")
                
                group_dfs = []
                for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                    if orig_d is not None:
                        d_f = orig_d.copy()
                        if meta_cr["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cr["country"]]
                        if meta_cr["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cr["customer"]]
                        if group_col_key != "Cat" and meta_cr["category"] != "All Categories": d_f = d_f[d_f[c["Cat"]] == meta_cr["category"]]
                        if meta_cr["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_cr["months"])]

                        if not d_f.empty:
                            g = d_f.groupby(c[group_col_key]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"})
                            group_dfs.append((g, y, c[group_col_key]))

                if group_dfs:
                    g_col_name = group_dfs[0][2]
                    master = group_dfs[0][0]
                    for g, y, _ in group_dfs[1:]:
                        master = pd.merge(master, g, on=g_col_name, how="outer")
                    master = master.fillna(Decimal('0'))

                    group_dfs_chrono = sorted(group_dfs, key=lambda x: x[1])
                    y_newest = group_dfs_chrono[-1][1]
                    
                    if len(group_dfs_chrono) >= 2:
                        y1 = group_dfs_chrono[-2][1]
                        master[f"YoY {y_newest} vs {y1}"] = master.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0)), axis=1) if not master.empty else []

                    master = sort_by_col_desc(master, f"Net {y_newest}")

                    pie_cols = st.columns(len(group_dfs_chrono))
                    for i, (g, y, _) in enumerate(group_dfs_chrono):
                        plot_df = master.copy()
                        plot_df[f"Net {y}"] = plot_df.get(f"Net {y}", pd.Series(dtype=float)).apply(lambda v: max(0, float(clean_number(v))))
                        
                        total_net = plot_df[f"Net {y}"].sum()
                        if total_net > 0:
                            plot_df['Share'] = plot_df[f"Net {y}"] / total_net
                            plot_df.loc[plot_df['Share'] < 0.005, g_col_name] = 'Other'
                            plot_df = plot_df.groupby(g_col_name, as_index=False)[[f"Net {y}"]].sum()

                        with pie_cols[i]:
                            st.plotly_chart(px.pie(plot_df, names=g_col_name, values=f"Net {y}", title=f"{display_name} Pie {y}", color=g_col_name, color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                    display_df = master.copy()
                    for _, y, _ in group_dfs_chrono:
                        display_df[f"Net {y}"] = display_df.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                    
                    if len(group_dfs_chrono) >= 2:
                        y1 = group_dfs_chrono[-2][1]
                        display_df[f"YoY {y_newest} vs {y1} (%)"] = display_df.get(f"YoY {y_newest} vs {y1}", pd.Series(dtype=str)).apply(yoy_label)
                        display_df = display_df.drop(columns=[f"YoY {y_newest} vs {y1}"], errors='ignore')
                        
                    display_df = display_df.rename(columns={g_col_name: display_name})
                    
                    cols_order = [display_name]
                    for _, y, _ in group_dfs_chrono:
                        cols_order.append(f"Net {y}")
                    if len(group_dfs_chrono) >= 2:
                        cols_order.append(f"YoY {y_newest} vs {group_dfs_chrono[-2][1]} (%)")
                        
                    st.dataframe(add_index(display_df[cols_order]), use_container_width=True)

            if meta_cr["category"] == "All Categories":
                render_cr_sub_analysis("Cat", "Category Comparison", "Category")
            render_cr_sub_analysis("Brand", "Brand Comparison", "Brand")

            st.divider()
            st.markdown("### L4L Table (SKU Level)")
            
            l4l_dfs = []
            for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                if orig_d is not None:
                    d_f = orig_d.copy()
                    if meta_cr["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cr["country"]]
                    if meta_cr["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cr["customer"]]
                    if meta_cr["category"] != "All Categories": d_f = d_f[d_f[c["Cat"]] == meta_cr["category"]]
                    if meta_cr["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_cr["months"])]
                    
                    if not d_f.empty:
                        g = d_f.groupby(c["Code"]).agg({c["Desc"]: "first", c["Net"]: sum_decimal, c["Qty"]: sum_decimal}).reset_index()
                        g = g.rename(columns={c["Net"]: f"Net {y}", c["Qty"]: f"Qty {y}"})
                        l4l_dfs.append((g, y, c))
                    
            if l4l_dfs:
                c_code = l4l_dfs[0][2]["Code"]
                c_desc = hierarchy_cols["Desc"]
                master_l4l = l4l_dfs[0][0]
                for g, y, _ in l4l_dfs[1:]:
                    master_l4l = pd.merge(master_l4l, g, on=c_code, how="outer", suffixes=("", "_y"))
                    master_l4l[c_desc] = master_l4l[c_desc].fillna(master_l4l[c_desc + "_y"])
                    master_l4l = master_l4l.drop(columns=[c_desc + "_y"])
                
                for col in master_l4l.columns:
                    if "Net" in col or "Qty" in col:
                        master_l4l[col] = master_l4l[col].fillna(Decimal('0'))
                
                l4l_chrono = sorted(l4l_dfs, key=lambda x: x[1])
                y_newest = l4l_chrono[-1][1]
                cr_years = [y for _, y, _ in l4l_chrono]
                
                display_cols = [c_code, c_desc]
                for y in cr_years:
                    display_cols.extend([f"Net {y}", f"Qty {y}"])

                if len(cr_years) >= 2:
                    y1 = cr_years[-2]
                    master_l4l[f"YoY {y_newest} vs {y1} (%)"] = master_l4l.apply(lambda x: yoy_label(yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0))), axis=1) if not master_l4l.empty else []
                    display_cols.append(f"YoY {y_newest} vs {y1} (%)")

                master_l4l = sort_by_col_desc(master_l4l, f"Net {y_newest}")
                
                for y in cr_years:
                    master_l4l[f"Net {y}"] = master_l4l.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                    master_l4l[f"Qty {y}"] = master_l4l.get(f"Qty {y}", pd.Series(dtype=int)).apply(to_display_num)
                    
                master_l4l = master_l4l.rename(columns={c_code: "Code", c_desc: "Description"})
                display_cols[0] = "Code"
                display_cols[1] = "Description"
                
                st.dataframe(add_index(master_l4l[display_cols]), use_container_width=True)

            st.divider()
            is_cat_all = (meta_cr["category"] == "All Categories")
            st.markdown("### Auto Insights (Category Focus)" if is_cat_all else f"### Auto Insights (SKU Focus - {meta_cr['category']})")
            
            ins_dfs = []
            for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                if orig_d is not None:
                    d_f = orig_d.copy()
                    if meta_cr["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cr["country"]]
                    if meta_cr["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cr["customer"]]
                    if not is_cat_all: d_f = d_f[d_f[c["Cat"]] == meta_cr["category"]]
                    if meta_cr["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_cr["months"])]
                    
                    if not d_f.empty:
                        if is_cat_all: 
                            g = d_f.groupby(c["Cat"]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"})
                            ins_dfs.append((g, y, c["Cat"]))
                        else: 
                            g = d_f.groupby(c["Code"]).agg({c["Desc"]: "first", c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"})
                            ins_dfs.append((g, y, c["Code"]))
                            
            if len(ins_dfs) >= 2:
                if is_cat_all:
                    c_master_key = ins_dfs[0][2]
                    master_ins = ins_dfs[0][0]
                    for g, y, _ in ins_dfs[1:]: 
                        master_ins = pd.merge(master_ins, g, on=c_master_key, how="outer")
                    master_ins = master_ins.fillna(Decimal('0'))
                    disp_prefix = [c_master_key]
                else:
                    c_code = ins_dfs[0][2]
                    c_desc = hierarchy_cols["Desc"]
                    master_ins = ins_dfs[0][0]
                    for g, y, _ in ins_dfs[1:]:
                        master_ins = pd.merge(master_ins, g, on=c_code, how="outer", suffixes=("", "_y"))
                        master_ins[c_desc] = master_ins[c_desc].fillna(master_ins[c_desc + "_y"])
                        master_ins = master_ins.drop(columns=[c_desc + "_y"])
                    for col in master_ins.columns:
                        if "Net" in col: 
                            master_ins[col] = master_ins[col].fillna(Decimal('0'))
                    master_ins = master_ins.rename(columns={c_code: "Code", c_desc: "Description"})
                    disp_prefix = ["Code", "Description"]
                
                ins_chrono = sorted(ins_dfs, key=lambda x: x[1])
                cr_years_ins = [item[1] for item in ins_chrono]
                y_newest = cr_years_ins[-1]
                y1 = cr_years_ins[-2]
                
                master_ins["Change_1_Raw"] = master_ins.apply(lambda x: clean_number(x.get(f"Net {y_newest}", Decimal('0'))) - clean_number(x.get(f"Net {y1}", Decimal('0'))), axis=1)
                master_ins["YoY_1"] = master_ins.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0)), axis=1)
                
                master_ins[f"Change {y_newest} vs {y1}"] = master_ins["Change_1_Raw"].apply(to_display_num)
                master_ins[f"YoY {y_newest} vs {y1} (%)"] = master_ins["YoY_1"].apply(yoy_label)
                display_cols = disp_prefix + [f"Net {y}" for y in cr_years_ins] + [f"Change {y_newest} vs {y1}", f"YoY {y_newest} vs {y1} (%)"]

                cc1, cc2 = st.columns(2)
                with cc1:
                    st.write("#### Top 5 Growth" + (" Categories" if is_cat_all else " SKUs"))
                    growth = master_ins[master_ins["Change_1_Raw"] > 0].sort_values("Change_1_Raw", ascending=False).head(5)
                    if not growth.empty:
                        disp = growth.copy()
                        for y in cr_years_ins: 
                            disp[f"Net {y}"] = disp.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols]))
                    else: 
                        st.info("No growth found.")
                        
                with cc2:
                    st.write("#### Top 5 Decline" + (" Categories" if is_cat_all else " SKUs"))
                    decline = master_ins[master_ins["Change_1_Raw"] < 0].sort_values("Change_1_Raw", ascending=True).head(5)
                    if not decline.empty:
                        disp = decline.copy()
                        for y in cr_years_ins: 
                            disp[f"Net {y}"] = disp.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols]))
                    else: 
                        st.success("No decline found.")


# ================= TAB: OVERVIEW =================
with tab_overview:
    st.header("Overview — 3-year Comparison")
    loaded_dfs = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if not loaded_dfs: 
        st.warning("Please upload data.")
    else:
        filtered_dfs, meta = apply_shared_filters(loaded_dfs, hierarchy_cols, "ov", default_months=hierarchy_months, hm_sig=hm_sig)
        df_curr_f = filtered_dfs[0] if df_curr is not None else None
        df_prev_f = filtered_dfs[1 if df_curr is not None else 0] if df_prev is not None else None
        df_old2_f = filtered_dfs[-1] if df_old2 is not None else None

        st.divider()
        st.markdown("### Net Value Comparison (Global Filters Applied)")
        vals, years = [], []
        for df_f, y, c in zip([df_old2_f, df_prev_f, df_curr_f], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if df_f is not None: 
                vals.append(float(sum_decimal(df_f[c["Net"]])))
                years.append(y)
        if vals: 
            chart_df = pd.DataFrame({"Year": years, "Net (EUR)": vals}).sort_values("Year")
            st.plotly_chart(px.bar(chart_df, x="Year", y="Net (EUR)", text="Net (EUR)", title="Net Value YTD", color="Year", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

        def render_3y_analysis(group_col, title, dfs, year_list, cols_list, display_name):
            st.divider()
            st.markdown(f"### {title}")
            g_dfs = []
            for df, y, c in zip(dfs, year_list, cols_list):
                if df is not None:
                    g = df.groupby(group_col).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"})
                    g_dfs.append((g, y))
            
            if g_dfs:
                master = g_dfs[0][0]
                for g, y in g_dfs[1:]: 
                    master = pd.merge(master, g, on=group_col, how="outer")
                master = master.fillna(Decimal('0'))
                g_dfs_c = sorted(g_dfs, key=lambda x: x[1])
                y_newest = g_dfs_c[-1][1]
                if len(g_dfs_c) >= 2: 
                    master[f"YoY {y_newest} vs {g_dfs_c[-2][1]}"] = master.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {g_dfs_c[-2][1]}", 0)), axis=1) if not master.empty else []
                master = sort_by_col_desc(master, f"Net {y_newest}")

                pie_cols = st.columns(len(g_dfs_c))
                for i, (g, y) in enumerate(g_dfs_c):
                    plot_df = master.copy()
                    plot_df[f"Net {y}"] = plot_df.get(f"Net {y}").apply(lambda v: max(0, float(clean_number(v))))
                    tot = plot_df[f"Net {y}"].sum()
                    if tot > 0:
                        plot_df.loc[plot_df[f"Net {y}"] / tot < 0.005, group_col] = 'Other'
                        plot_df = plot_df.groupby(group_col, as_index=False)[[f"Net {y}"]].sum()
                    with pie_cols[i]: 
                        st.plotly_chart(px.pie(plot_df, names=group_col, values=f"Net {y}", title=f"{display_name} {y}", color=group_col, color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)
                
                disp = master.copy()
                for _, y in g_dfs_c: 
                    disp[f"Net {y}"] = disp.get(f"Net {y}").apply(to_display_num)
                if len(g_dfs_c) >= 2: 
                    disp[f"YoY {y_newest} vs {g_dfs_c[-2][1]} (%)"] = disp.get(f"YoY {y_newest} vs {g_dfs_c[-2][1]}").apply(yoy_label)
                
                disp = disp.rename(columns={group_col: display_name})
                cols_order = [display_name] + [f"Net {y}" for _,y in g_dfs_c] + ([f"YoY {y_newest} vs {g_dfs_c[-2][1]} (%)"] if len(g_dfs_c)>=2 else [])
                st.dataframe(add_index(disp[cols_order]), use_container_width=True)

        dfs_cat = []
        for df_f, c_map, orig_d in zip([df_curr_f, df_prev_f, df_old2_f], [cols_curr, cols_prev, cols_old2], [df_curr, df_prev, df_old2]):
            if df_f is not None and orig_d is not None:
                d = orig_d.copy()
                if meta["country"] != "All Countries": d = d[d[c_map["Country"]] == meta["country"]]
                if meta["customer"] != "All Customers": d = d[d[c_map["Customer"]] == meta["customer"]]
                if meta["months"]: d = d[d[c_map["Month"]].isin(meta["months"])]
                dfs_cat.append(d)
            else:
                dfs_cat.append(None)

        if meta["category"] == "All Categories":
            render_3y_analysis(hierarchy_cols["Cat"], "Category Comparison", dfs_cat, [year_curr, year_prev, year_old2], [cols_curr, cols_prev, cols_old2], "Category")
        
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
                    if is_cat_all: 
                        g = d_f.groupby(c["Cat"]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"})
                        ins_dfs_ov.append((g, y, c["Cat"]))
                    else: 
                        g = d_f.groupby(c["Code"]).agg({c["Desc"]: "first", c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}"})
                        ins_dfs_ov.append((g, y, c["Code"]))
                
        if len(ins_dfs_ov) >= 2:
            if is_cat_all:
                c_master_key = ins_dfs_ov[0][2]
                master_ins_ov = ins_dfs_ov[0][0]
                for g, y, _ in ins_dfs_ov[1:]: 
                    master_ins_ov = pd.merge(master_ins_ov, g, on=c_master_key, how="outer")
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
                    if "Net" in col: 
                        master_ins_ov[col] = master_ins_ov[col].fillna(Decimal('0'))
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
                    for y in ov_years: 
                        disp[f"Net {y}"] = disp.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                    st.dataframe(add_index(disp[display_cols]))
                else: 
                    st.info("No growth found.")
                    
            with c2:
                st.write("#### Top 5 Decline" + (" Categories" if is_cat_all else " SKUs"))
                decline = master_ins_ov[master_ins_ov["Change_1_Raw"] < 0].sort_values("Change_1_Raw", ascending=True).head(5)
                if not decline.empty:
                    disp = decline.copy()
                    for y in ov_years: 
                        disp[f"Net {y}"] = disp.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                    st.dataframe(add_index(disp[display_cols]))
                else: 
                    st.success("No decline found.")


# ================= TAB: COUNTRY REVIEW =================
with tab_country:
    st.header("🌍 Country Review")
    
    dfs_cou_rev = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_cou_rev) < 1:
        st.warning("Please upload data.")
    else:
        df_all_cou_rev = pd.concat(dfs_cou_rev, ignore_index=True)
        
        cou_c1, cou_c2, cou_c3, cou_c4 = st.columns(4)
        
        countries_cou_rev = ["All Countries"] + sorted(df_all_cou_rev[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_cou_rev = cou_c1.selectbox("🌎 Country", countries_cou_rev, key="cou_rev_country")

        df_for_cou_rev = df_all_cou_rev.copy()
        if selected_country_cou_rev != "All Countries":
            df_for_cou_rev = df_for_cou_rev[df_for_cou_rev[hierarchy_cols["Country"]] == selected_country_cou_rev]

        customers_cou_rev = ["All Customers"] + sorted(df_for_cou_rev[hierarchy_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
        selected_customer_cou_rev = cou_c2.selectbox("🏢 Customer", customers_cou_rev, key="cou_rev_customer")

        categories_cou_rev = ["All Categories"] + sorted(df_for_cou_rev[hierarchy_cols["Cat"]].dropna().unique().tolist())
        selected_category_cou_rev = cou_c3.selectbox("📦 Category", categories_cou_rev, key="cou_rev_category")

        options_cou_m = MONTHS_ORDER 
        default_cou_m = [m for m in hierarchy_months if m in options_cou_m]
        if not default_cou_m:
            default_cou_m = options_cou_m
            
        key_cou_mo = f"cou_months_{hm_sig}"
        label_cou_m = f"📅 Months ({len(default_cou_m)} active)"
        selected_months_cou = cou_c4.multiselect(label_cou_m, options=options_cou_m, default=default_cou_m, key=key_cou_mo)

        meta_cou = {
            "country": selected_country_cou_rev,
            "customer": selected_customer_cou_rev,
            "category": selected_category_cou_rev,
            "months": selected_months_cou
        }

        cou_valid_dfs = []
        for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if orig_d is not None:
                d_f = orig_d.copy()
                if meta_cou["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cou["country"]]
                if meta_cou["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cou["customer"]]
                if meta_cou["category"] != "All Categories": d_f = d_f[d_f[c["Cat"]] == meta_cou["category"]]
                if meta_cou["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_cou["months"])]
                if not d_f.empty:
                    cou_valid_dfs.append((d_f, y, c))

        if cou_valid_dfs:
            st.markdown("### Country Sales Breakdown")
            cou_dfs_list = []
            for d_f, y, c in cou_valid_dfs:
                g = d_f.groupby(c["Country"]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}", c["Country"]: "Country"})
                cou_dfs_list.append((g, y))

            if cou_dfs_list:
                master_cou = cou_dfs_list[0][0]
                for g, y in cou_dfs_list[1:]:
                    master_cou = pd.merge(master_cou, g, on="Country", how="outer")
                master_cou = master_cou.fillna(Decimal('0'))

                cou_dfs_chrono = sorted(cou_dfs_list, key=lambda x: x[1])
                y_newest = cou_dfs_chrono[-1][1]
                if len(cou_dfs_chrono) >= 2:
                    y1 = cou_dfs_chrono[-2][1]
                    master_cou[f"YoY {y_newest} vs {y1}"] = master_cou.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0)), axis=1) if not master_cou.empty else []

                master_cou = sort_by_col_desc(master_cou, f"Net {y_newest}")

                pie_cols = st.columns(len(cou_dfs_chrono))
                for i, (g, y) in enumerate(cou_dfs_chrono):
                    plot_df = master_cou.copy()
                    plot_df[f"Net {y}"] = plot_df.get(f"Net {y}", pd.Series(dtype=float)).apply(lambda v: max(0, float(clean_number(v))))
                    tot = plot_df[f"Net {y}"].sum()
                    if tot > 0:
                        plot_df.loc[plot_df[f"Net {y}"] / tot < 0.01, "Country"] = 'Other'
                        plot_df = plot_df.groupby("Country", as_index=False)[[f"Net {y}"]].sum()
                    with pie_cols[i]:
                        st.plotly_chart(px.pie(plot_df, names="Country", values=f"Net {y}", title=f"Country Pie {y}", color="Country", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                disp_cou = master_cou.copy()
                for _, y in cou_dfs_chrono:
                    disp_cou[f"Net {y}"] = disp_cou.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                if len(cou_dfs_chrono) >= 2:
                    y1 = cou_dfs_chrono[-2][1]
                    disp_cou[f"YoY {y_newest} vs {y1} (%)"] = disp_cou.get(f"YoY {y_newest} vs {y1}", pd.Series(dtype=str)).apply(yoy_label)
                    disp_cou = disp_cou.drop(columns=[f"YoY {y_newest} vs {y1}"], errors='ignore')

                cols_order = ["Country"] + [f"Net {y}" for _, y in cou_dfs_chrono] + ([f"YoY {y_newest} vs {cou_dfs_chrono[-2][1]} (%)"] if len(cou_dfs_chrono) >= 2 else [])
                st.dataframe(add_index(disp_cou[cols_order]), use_container_width=True)


# ================= TAB: CATEGORY REVIEW =================
with tab_category:
    st.header("📁 Category Review")
    
    dfs_cat_rev = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_cat_rev) < 1:
        st.warning("Please upload data.")
    else:
        df_all_cat_rev = pd.concat(dfs_cat_rev, ignore_index=True)
        
        cat_c1, cat_c2, cat_c3, cat_c4 = st.columns(4)
        
        countries_cat_rev = ["All Countries"] + sorted(df_all_cat_rev[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_cat_rev = cat_c1.selectbox("🌎 Country", countries_cat_rev, key="cat_rev_country")

        df_for_cat_rev = df_all_cat_rev.copy()
        if selected_country_cat_rev != "All Countries":
            df_for_cat_rev = df_for_cat_rev[df_for_cat_rev[hierarchy_cols["Country"]] == selected_country_cat_rev]

        customers_cat_rev = ["All Customers"] + sorted(df_for_cat_rev[hierarchy_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
        selected_customer_cat_rev = cat_c2.selectbox("🏢 Customer", customers_cat_rev, key="cat_rev_customer")

        brands_cat_rev = ["All Brands"] + sorted(df_for_cat_rev[hierarchy_cols["Brand"]].dropna().unique().tolist())
        selected_brand_cat_rev = cat_c3.selectbox("🏷️ Brand (Licence)", brands_cat_rev, key="cat_rev_brand")

        options_cat_m = MONTHS_ORDER 
        default_cat_m = [m for m in hierarchy_months if m in options_cat_m]
        if not default_cat_m:
            default_cat_m = options_cat_m
            
        key_cat_mo = f"cat_months_{hm_sig}"
        label_cat_m = f"📅 Months ({len(default_cat_m)} active)"
        selected_months_cat = cat_c4.multiselect(label_cat_m, options=options_cat_m, default=default_cat_m, key=key_cat_mo)

        meta_cat = {
            "country": selected_country_cat_rev,
            "customer": selected_customer_cat_rev,
            "brand": selected_brand_cat_rev,
            "months": selected_months_cat
        }

        cat_valid_dfs = []
        for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if orig_d is not None:
                d_f = orig_d.copy()
                if meta_cat["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_cat["country"]]
                if meta_cat["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_cat["customer"]]
                if meta_cat["brand"] != "All Brands": d_f = d_f[d_f[c["Brand"]] == meta_cat["brand"]]
                if meta_cat["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_cat["months"])]
                if not d_f.empty:
                    cat_valid_dfs.append((d_f, y, c))

        if cat_valid_dfs:
            st.markdown("### Category Sales Breakdown")
            cat_dfs_list = []
            for d_f, y, c in cat_valid_dfs:
                g = d_f.groupby(c["Cat"]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}", c["Cat"]: "Category"})
                cat_dfs_list.append((g, y))

            if cat_dfs_list:
                master_cat = cat_dfs_list[0][0]
                for g, y in cat_dfs_list[1:]:
                    master_cat = pd.merge(master_cat, g, on="Category", how="outer")
                master_cat = master_cat.fillna(Decimal('0'))

                cat_dfs_chrono = sorted(cat_dfs_list, key=lambda x: x[1])
                y_newest = cat_dfs_chrono[-1][1]
                if len(cat_dfs_chrono) >= 2:
                    y1 = cat_dfs_chrono[-2][1]
                    master_cat[f"YoY {y_newest} vs {y1}"] = master_cat.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0)), axis=1) if not master_cat.empty else []

                master_cat = sort_by_col_desc(master_cat, f"Net {y_newest}")

                pie_cols = st.columns(len(cat_dfs_chrono))
                for i, (g, y) in enumerate(cat_dfs_chrono):
                    plot_df = master_cat.copy()
                    plot_df[f"Net {y}"] = plot_df.get(f"Net {y}", pd.Series(dtype=float)).apply(lambda v: max(0, float(clean_number(v))))
                    tot = plot_df[f"Net {y}"].sum()
                    if tot > 0:
                        plot_df.loc[plot_df[f"Net {y}"] / tot < 0.01, "Category"] = 'Other'
                        plot_df = plot_df.groupby("Category", as_index=False)[[f"Net {y}"]].sum()
                    with pie_cols[i]:
                        st.plotly_chart(px.pie(plot_df, names="Category", values=f"Net {y}", title=f"Category Pie {y}", color="Category", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                disp_cat = master_cat.copy()
                for _, y in cat_dfs_chrono:
                    disp_cat[f"Net {y}"] = disp_cat.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                if len(cat_dfs_chrono) >= 2:
                    y1 = cat_dfs_chrono[-2][1]
                    disp_cat[f"YoY {y_newest} vs {y1} (%)"] = disp_cat.get(f"YoY {y_newest} vs {y1}", pd.Series(dtype=str)).apply(yoy_label)
                    disp_cat = disp_cat.drop(columns=[f"YoY {y_newest} vs {y1}"], errors='ignore')

                cols_order = ["Category"] + [f"Net {y}" for _, y in cat_dfs_chrono] + ([f"YoY {y_newest} vs {cat_dfs_chrono[-2][1]} (%)"] if len(cat_dfs_chrono) >= 2 else [])
                st.dataframe(add_index(disp_cat[cols_order]), use_container_width=True)


# ================= TAB: BRAND REVIEW =================
with tab_brand:
    st.header("🏷️ Brand Review")
    
    dfs_bra_rev = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_bra_rev) < 1:
        st.warning("Please upload data.")
    else:
        df_all_bra_rev = pd.concat(dfs_bra_rev, ignore_index=True)
        
        bra_c1, bra_c2, bra_c3, bra_c4 = st.columns(4)
        
        countries_bra_rev = ["All Countries"] + sorted(df_all_bra_rev[hierarchy_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_bra_rev = bra_c1.selectbox("🌎 Country", countries_bra_rev, key="bra_rev_country")

        df_for_bra_rev = df_all_bra_rev.copy()
        if selected_country_bra_rev != "All Countries":
            df_for_bra_rev = df_for_bra_rev[df_for_bra_rev[hierarchy_cols["Country"]] == selected_country_bra_rev]

        customers_bra_rev = ["All Customers"] + sorted(df_for_bra_rev[hierarchy_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
        selected_customer_bra_rev = bra_c2.selectbox("🏢 Customer", customers_bra_rev, key="bra_rev_customer")

        categories_bra_rev = ["All Categories"] + sorted(df_for_bra_rev[hierarchy_cols["Cat"]].dropna().unique().tolist())
        selected_category_bra_rev = bra_c3.selectbox("📦 Category", categories_bra_rev, key="bra_rev_category")

        options_bra_m = MONTHS_ORDER 
        default_bra_m = [m for m in hierarchy_months if m in options_bra_m]
        if not default_bra_m:
            default_bra_m = options_bra_m
            
        key_bra_mo = f"bra_months_{hm_sig}"
        label_bra_m = f"📅 Months ({len(default_bra_m)} active)"
        selected_months_bra = bra_c4.multiselect(label_bra_m, options=options_bra_m, default=default_bra_m, key=key_bra_mo)

        meta_bra = {
            "country": selected_country_bra_rev,
            "customer": selected_customer_bra_rev,
            "category": selected_category_bra_rev,
            "months": selected_months_bra
        }

        bra_valid_dfs = []
        for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if orig_d is not None:
                d_f = orig_d.copy()
                if meta_bra["country"] != "All Countries": d_f = d_f[d_f[c["Country"]] == meta_bra["country"]]
                if meta_bra["customer"] != "All Customers": d_f = d_f[d_f[c["Customer"]] == meta_bra["customer"]]
                if meta_bra["category"] != "All Categories": d_f = d_f[d_f[c["Cat"]] == meta_bra["category"]]
                if meta_bra["months"]: d_f = d_f[d_f[c["Month"]].isin(meta_bra["months"])]
                if not d_f.empty:
                    bra_valid_dfs.append((d_f, y, c))

        if bra_valid_dfs:
            st.markdown("### Brand Sales Breakdown")
            bra_dfs_list = []
            for d_f, y, c in bra_valid_dfs:
                g = d_f.groupby(c["Brand"]).agg({c["Net"]: sum_decimal}).reset_index().rename(columns={c["Net"]: f"Net {y}", c["Brand"]: "Brand"})
                bra_dfs_list.append((g, y))

            if bra_dfs_list:
                master_bra = bra_dfs_list[0][0]
                for g, y in bra_dfs_list[1:]:
                    master_bra = pd.merge(master_bra, g, on="Brand", how="outer")
                master_bra = master_bra.fillna(Decimal('0'))

                bra_dfs_chrono = sorted(bra_dfs_list, key=lambda x: x[1])
                y_newest = bra_dfs_chrono[-1][1]
                if len(bra_dfs_chrono) >= 2:
                    y1 = bra_dfs_chrono[-2][1]
                    master_bra[f"YoY {y_newest} vs {y1}"] = master_bra.apply(lambda x: yoy_calc(x.get(f"Net {y_newest}", 0), x.get(f"Net {y1}", 0)), axis=1) if not master_bra.empty else []

                master_bra = sort_by_col_desc(master_bra, f"Net {y_newest}")

                pie_cols = st.columns(len(bra_dfs_chrono))
                for i, (g, y) in enumerate(bra_dfs_chrono):
                    plot_df = master_bra.copy()
                    plot_df[f"Net {y}"] = plot_df.get(f"Net {y}", pd.Series(dtype=float)).apply(lambda v: max(0, float(clean_number(v))))
                    tot = plot_df[f"Net {y}"].sum()
                    if tot > 0:
                        plot_df.loc[plot_df[f"Net {y}"] / tot < 0.01, "Brand"] = 'Other'
                        plot_df = plot_df.groupby("Brand", as_index=False)[[f"Net {y}"]].sum()
                    with pie_cols[i]:
                        st.plotly_chart(px.pie(plot_df, names="Brand", values=f"Net {y}", title=f"Brand Pie {y}", color="Brand", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                disp_bra = master_bra.copy()
                for _, y in bra_dfs_chrono:
                    disp_bra[f"Net {y}"] = disp_bra.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                if len(bra_dfs_chrono) >= 2:
                    y1 = bra_dfs_chrono[-2][1]
                    disp_bra[f"YoY {y_newest} vs {y1} (%)"] = disp_bra.get(f"YoY {y_newest} vs {y1}", pd.Series(dtype=str)).apply(yoy_label)
                    disp_bra = disp_bra.drop(columns=[f"YoY {y_newest} vs {y1}"], errors='ignore')

                cols_order = ["Brand"] + [f"Net {y}" for _, y in bra_dfs_chrono] + ([f"YoY {y_newest} vs {bra_dfs_chrono[-2][1]} (%)"] if len(bra_dfs_chrono) >= 2 else [])
                st.dataframe(add_index(disp_bra[cols_order]), use_container_width=True)


# ================= TAB: DETAILED L4L =================
with tab_l4l:
    st.header("📅 Detailed L4L Analysis")
    loaded_dfs_l4l = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(loaded_dfs_l4l) < 2:
        st.warning("Please upload at least two Excel files to perform L4L comparison.")
    else:
        filtered_dfs_l4l, meta_l4l = apply_shared_filters(loaded_dfs_l4l, hierarchy_cols, "l4l", default_months=hierarchy_months, hm_sig=hm_sig)
        
        available_pairs = []
        if df_curr is not None and df_prev is not None:
            available_pairs.append((year_prev, year_curr, filtered_dfs_l4l[1 if df_curr is not None else 0], filtered_dfs_l4l[0], cols_prev, cols_curr))
        if df_prev is not None and df_old2 is not None:
            idx_prev = 1 if df_curr is not None else 0
            idx_old = 2 if df_curr is not None else 1
            available_pairs.append((year_old2, year_prev, filtered_dfs_l4l[idx_old], filtered_dfs_l4l[idx_prev], cols_old2, cols_prev))
            
        if available_pairs:
            pair_labels = [f"{y_old} vs {y_new}" for y_old, y_new, _, _, _, _ in available_pairs]
            sel_pair_idx = st.selectbox("Select Year Comparison Pair", range(len(pair_labels)), format_func=lambda i: pair_labels[i], key="l4l_pair_sel")
            
            y_old_sel, y_new_sel, df_old_sel, df_new_sel, cols_old_sel, cols_new_sel = available_pairs[sel_pair_idx]
            
            render_two_year_dashboard(
                df_new=df_new_sel,
                df_old=df_old_sel,
                cols_new=cols_new_sel,
                cols_old=cols_old_sel,
                context_name="Detailed L4L",
                unique_prefix=f"l4l_{y_old_sel}_{y_new_sel}",
                category_filter=meta_l4l["category"],
                color_map=GLOBAL_COLOR_MAP
            )
