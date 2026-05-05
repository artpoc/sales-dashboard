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
        
        if key_months not in st.session_state:
            st.session_state[key_months] = default_m
            
        selected_months = c4.multiselect("📅 Months", options=options_m, key=key_months)
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

    # CUSTOMER IMPACT (RESTORED SECTION)
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


# ================= CUSTOMER REVIEW =================
with tab_customer:
    st.header("👥 Customer Review")
    
    dfs_cr = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_cr) < 1:
        st.warning("Please upload data.")
    else:
        base_cols = hierarchy_cols
        
        df_all_cr = pd.concat(dfs_cr, ignore_index=True)
        
        c1_cr, c2_cr, c3_cr, c4_cr = st.columns(4)
        
        countries_cr = ["All Countries"] + sorted(df_all_cr[base_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_cr = c1_cr.selectbox("🌎 Country", countries_cr, key="cr_country")

        df_for_customers_cr = df_all_cr.copy()
        if selected_country_cr != "All Countries":
            df_for_customers_cr = df_for_customers_cr[df_for_customers_cr[base_cols["Country"]] == selected_country_cr]

        customers_cr = ["All Customers"] + sorted(df_for_customers_cr[base_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
        selected_customer_cr = c2_cr.selectbox("🏢 Customer", customers_cr, key="cr_customer")

        categories_cr = ["All Categories"] + sorted(df_for_customers_cr[base_cols["Cat"]].dropna().unique().tolist())
        selected_category_cr = c3_cr.selectbox("📦 Category", categories_cr, key="cr_category")

        options_cr_m = MONTHS_ORDER 
        default_cr_m = [m for m in hierarchy_months if m in options_cr_m]
        if not default_cr_m: default_cr_m = options_cr_m
        
        if "cr_months" not in st.session_state:
            st.session_state["cr_months"] = default_cr_m
            
        selected_months_cr = c4_cr.multiselect("📅 Months", options=options_cr_m, key="cr_months")

        meta_cr = {
            "country": selected_country_cr,
            "customer": selected_customer_cr,
            "category": selected_category_cr,
            "months": selected_months_cr,
            "df_all": df_all_cr
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
            st.info(f"ℹ️ Averages and Sums are calculated using {default_divisor} months based on your selected month filters above. You can adjust this divisor manually below.")
            avg_divisor = st.slider("Select number of months for ∑ and AVG calculation (e.g. 3 = Jan, Feb, Mar):", min_value=1, max_value=12, value=default_divisor, step=1, key="cr_slider")

            def render_monthly_table(mode="Net"):
                if mode == "Net": st.markdown("### Net Value Monthly Comparison")
                else: st.markdown("### Quantity Monthly Comparison")
                
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
                st.plotly_chart(px.bar(pd.DataFrame(chart_vals).sort_values("Year"), x="Year", y="Net", text="Net", color="Year", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True, key="cr_net_bar")

            def render_cr_sub_analysis(group_col_key, section_title, display_name, color_map=None):
                color_map = color_map or {}
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
                        plot_df[f"Net {y}"] = plot_df.get(f"Net {y}", pd.Series(dtype=float)).apply(lambda v: float(clean_number(v)))
                        plot_df.loc[plot_df[f"Net {y}"] < 0, f"Net {y}"] = 0
                        
                        total_net = plot_df[f"Net {y}"].sum()
                        if total_net > 0:
                            plot_df['Share'] = plot_df[f"Net {y}"] / total_net
                            plot_df.loc[plot_df['Share'] < 0.005, g_col_name] = 'Other'
                            plot_df = plot_df.groupby(g_col_name, as_index=False)[[f"Net {y}"]].sum()

                        with pie_cols[i]:
                            st.plotly_chart(px.pie(plot_df, names=g_col_name, values=f"Net {y}", title=f"{display_name} Pie {y}", color=g_col_name, color_discrete_map=color_map), use_container_width=True, key=f"cr_pie_{group_col_key}_{y}")

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

            render_cr_sub_analysis("Cat", "Category Comparison", "Category", color_map=GLOBAL_COLOR_MAP)
            render_cr_sub_analysis("Brand", "Brand Comparison", "Brand", color_map=GLOBAL_COLOR_MAP)

            def render_cr_l4l_table():
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
                    c_desc = base_cols["Desc"]
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
                    cr_years = [item[1] for item in l4l_chrono]
                    
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

            render_cr_l4l_table()

# ================= COUNTRY REVIEW =================
with tab_country:
    st.header("🌍 Country Review")
    
    dfs_co = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_co) < 1:
        st.warning("Please upload data.")
    else:
        base_cols = hierarchy_cols
        df_all_co = pd.concat(dfs_co, ignore_index=True)
        
        cc1, cc2, cc3 = st.columns(3)
        
        categories_co = ["All Categories"] + sorted(df_all_co[base_cols["Cat"]].dropna().unique().tolist())
        selected_category_co = cc1.selectbox("📦 Category", categories_co, key="co_category")

        brands_co = ["All Brands"] + sorted(df_all_co[base_cols["Brand"]].dropna().unique().tolist())
        selected_brand_co = cc2.selectbox("🏷️ Brand (Licence)", brands_co, key="co_brand")

        options_co_m = MONTHS_ORDER 
        default_co_m = [m for m in hierarchy_months if m in options_co_m]
        if not default_co_m: default_co_m = options_co_m
        
        if "co_months" not in st.session_state:
            st.session_state["co_months"] = default_co_m
            
        selected_months_co = cc3.multiselect("📅 Months", options=options_co_m, key="co_months")

        co_valid_dfs = []
        excluded_countries = ["romania", "spain", "united kingdom"]
        
        for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if orig_d is not None:
                d_f = orig_d.copy()
                
                d_f = d_f[~d_f[c["Country"]].astype(str).str.lower().str.strip().isin(excluded_countries)]
                
                if selected_category_co != "All Categories": d_f = d_f[d_f[c["Cat"]] == selected_category_co]
                if selected_brand_co != "All Brands": d_f = d_f[d_f[c["Brand"]] == selected_brand_co]
                if selected_months_co: d_f = d_f[d_f[c["Month"]].isin(selected_months_co)] 
                
                if not d_f.empty:
                    co_valid_dfs.append((d_f, y, c))
        
        co_valid_dfs_chrono = sorted(co_valid_dfs, key=lambda x: x[1])

        if not co_valid_dfs_chrono:
            st.warning("No data matches selected criteria.")
        else:
            co_dfs_grouped = []
            for d_f, y, c in co_valid_dfs_chrono:
                g = d_f.groupby(c["Country"]).agg({c["Net"]: sum_decimal, c["Qty"]: sum_decimal}).reset_index()
                g = g.rename(columns={c["Country"]: "Country", c["Net"]: f"Net {y}", c["Qty"]: f"Qty {y}"})
                co_dfs_grouped.append((g, str(y)))

            master_co = co_dfs_grouped[0][0]
            for g, y_str in co_dfs_grouped[1:]:
                master_co = pd.merge(master_co, g, on="Country", how="outer")
            master_co = master_co.fillna(Decimal('0'))

            y_newest_str = str(co_valid_dfs_chrono[-1][1])
            master_co = sort_by_col_desc(master_co, f"Net {y_newest_str}")

            st.divider()
            st.markdown("### Net Value Comparison")
            
            chart_data_rows = []
            for y_str in [item[1] for item in co_dfs_grouped]:
                for _, r in master_co.iterrows():
                    val = float(clean_number(r.get(f"Net {y_str}", Decimal('0'))))
                    if val != 0:
                        chart_data_rows.append({
                            "Year": y_str, 
                            "Country": r["Country"], 
                            "Net": val
                        })
            
            if chart_data_rows:
                chart_df = pd.DataFrame(chart_data_rows)
                country_order = master_co["Country"].tolist()
                
                fig = px.bar(
                    chart_df, 
                    x="Country", 
                    y="Net", 
                    color="Year", 
                    barmode="group",
                    title="Net Value by Country",
                    category_orders={"Country": country_order},
                    text_auto='.2s',
                    color_discrete_map=GLOBAL_COLOR_MAP
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True, key="co_net_bar")
            else:
                st.info("No net values to display for selected filters.")

            st.markdown("### Country Performance (L4L)")
            co_years_str = [item[1] for item in co_dfs_grouped]
            display_cols_co = ["Country"]
            
            for y_str in co_years_str:
                display_cols_co.extend([f"Net {y_str}", f"Qty {y_str}"])

            if len(co_years_str) >= 2:
                y1_str = co_years_str[-2]
                master_co[f"YoY {y_newest_str} vs {y1_str} (%)"] = master_co.apply(lambda x: yoy_label(yoy_calc(x.get(f"Net {y_newest_str}", 0), x.get(f"Net {y1_str}", 0))), axis=1) if not master_co.empty else []
                display_cols_co.append(f"YoY {y_newest_str} vs {y1_str} (%)")

            master_co_disp = master_co.copy()
            for y_str in co_years_str:
                master_co_disp[f"Net {y_str}"] = master_co_disp.get(f"Net {y_str}", pd.Series(dtype=int)).apply(to_display_num)
                master_co_disp[f"Qty {y_str}"] = master_co_disp.get(f"Qty {y_str}", pd.Series(dtype=int)).apply(to_display_num)
                
            st.dataframe(add_index(master_co_disp[display_cols_co]), use_container_width=True)

            st.divider()
            st.markdown("### Country Market Share")
            pie_cols_co = st.columns(len(co_dfs_grouped))
            for i, (g, y_str) in enumerate(co_dfs_grouped):
                plot_df = master_co.copy()
                plot_df[f"Net {y_str}"] = plot_df.get(f"Net {y_str}", pd.Series(dtype=float)).apply(lambda v: float(clean_number(v)))
                plot_df.loc[plot_df[f"Net {y_str}"] < 0, f"Net {y_str}"] = 0
                
                total_net = plot_df[f"Net {y_str}"].sum()
                if total_net > 0:
                    plot_df['Share'] = plot_df[f"Net {y_str}"] / total_net
                    plot_df.loc[plot_df['Share'] < 0.005, "Country"] = 'Other'
                    plot_df = plot_df.groupby("Country", as_index=False)[[f"Net {y_str}"]].sum()

                with pie_cols_co[i]:
                    st.plotly_chart(px.pie(plot_df, names="Country", values=f"Net {y_str}", title=f"Country Share {y_str}", color="Country", color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True, key=f"co_pie_{y_str}")

            st.divider()
            st.markdown("### Auto Insights (Country Focus)")
            
            if len(co_years_str) >= 2:
                ins_master_co = master_co.copy()
                y1_str = co_years_str[-2]
                
                ins_master_co["Change_Raw"] = ins_master_co.apply(lambda x: clean_number(x.get(f"Net {y_newest_str}", Decimal('0'))) - clean_number(x.get(f"Net {y1_str}", Decimal('0'))), axis=1)
                ins_master_co[f"Change {y_newest_str} vs {y1_str}"] = ins_master_co["Change_Raw"].apply(to_display_num)
                
                disp_prefix_co = ["Country"]
                display_cols_ins = disp_prefix_co + [f"Net {y}" for y in co_years_str] + [f"Change {y_newest_str} vs {y1_str}", f"YoY {y_newest_str} vs {y1_str} (%)"]

                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"#### Top 5 Growth Countries")
                    growth = ins_master_co[ins_master_co["Change_Raw"] > 0].sort_values("Change_Raw", ascending=False).head(5)
                    if not growth.empty:
                        disp = growth.copy()
                        for y_str in co_years_str:
                            disp[f"Net {y_str}"] = disp.get(f"Net {y_str}", pd.Series(dtype=int)).apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols_ins]))
                    else:
                        st.info("No growth found.")
                        
                with c2:
                    st.write("#### Top 5 Decline Countries")
                    decline = ins_master_co[ins_master_co["Change_Raw"] < 0].sort_values("Change_Raw", ascending=True).head(5)
                    if not decline.empty:
                        disp = decline.copy()
                        for y_str in co_years_str:
                            disp[f"Net {y_str}"] = disp.get(f"Net {y_str}", pd.Series(dtype=int)).apply(to_display_num)
                        st.dataframe(add_index(disp[display_cols_ins]))
                    else:
                        st.success("No decline found.")

# ================= BRAND REVIEW =================
with tab_brand:
    st.header("🏷️ Brand / License Review")
    
    dfs_br = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_br) < 1:
        st.warning("Please upload data.")
    else:
        base_cols = hierarchy_cols
        df_all_br = pd.concat(dfs_br, ignore_index=True)
        
        bc1, bc2, bc3, bc4 = st.columns(4)
        
        countries_br = ["All Countries"] + sorted(df_all_br[base_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_br = bc1.selectbox("🌎 Country", countries_br, key="br_country")

        df_for_brands = df_all_br.copy()
        if selected_country_br != "All Countries":
            df_for_brands = df_for_brands[df_for_brands[base_cols["Country"]] == selected_country_br]

        customers_br = ["All Customers"] + sorted(df_for_brands[base_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
        selected_customer_br = bc2.selectbox("🏢 Customer", customers_br, key="br_customer")

        categories_br = ["All Categories"] + sorted(df_for_brands[base_cols["Cat"]].dropna().unique().tolist())
        selected_category_br = bc3.selectbox("📦 Category", categories_br, key="br_category")

        brands_br = ["All Brands"] + sorted(df_for_brands[base_cols["Brand"]].dropna().unique().tolist())
        selected_brand_specific = bc4.selectbox("🏷️ Brand (Licence)", brands_br, key="br_brand_specific")

        options_br_m = MONTHS_ORDER 
        default_br_m = [m for m in hierarchy_months if m in options_br_m]
        if not default_br_m: default_br_m = options_br_m
        
        if "br_months" not in st.session_state:
            st.session_state["br_months"] = default_br_m
            
        selected_months_br = st.multiselect("📅 Months", options=options_br_m, key="br_months")

        if selected_brand_specific == "All Brands":
            st.info("⚠️ Please select a specific Brand from the filter above to view the dedicated analysis.")
        else:
            st.markdown(f"### KPI (Current vs Previous) - {selected_brand_specific}")
            br_valid_dfs = []
            for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                if orig_d is not None:
                    d_f = orig_d.copy()
                    if selected_country_br != "All Countries": d_f = d_f[d_f[c["Country"]] == selected_country_br]
                    if selected_customer_br != "All Customers": d_f = d_f[d_f[c["Customer"]] == selected_customer_br]
                    if selected_category_br != "All Categories": d_f = d_f[d_f[c["Cat"]] == selected_category_br]
                    d_f = d_f[d_f[c["Brand"]] == selected_brand_specific]
                    if selected_months_br: d_f = d_f[d_f[c["Month"]].isin(selected_months_br)] 
                    
                    if not d_f.empty:
                        br_valid_dfs.append((d_f, y, c))
            
            br_valid_dfs_chrono = sorted(br_valid_dfs, key=lambda x: x[1])

            if len(br_valid_dfs_chrono) >= 2:
                d_new, y_new, c_new = br_valid_dfs_chrono[-1]
                d_old, y_old, c_old = br_valid_dfs_chrono[-2]

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
            
            default_divisor_br = len(selected_months_br) if selected_months_br else 12
            avg_divisor_br = st.slider("Select number of months for ∑ and AVG calculation:", min_value=1, max_value=12, value=default_divisor_br, step=1, key="br_slider")

            def render_brand_monthly_table():
                st.markdown("### Net Value Monthly Comparison")
                col_key = "Net"
                sum_col_key = f"∑ (for {avg_divisor_br} months)"
                avg_col_key = "Avg Month"

                year_data = {}
                for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
                    if orig_d is not None:
                        d_f = orig_d.copy()
                        if selected_country_br != "All Countries": d_f = d_f[d_f[c["Country"]] == selected_country_br]
                        if selected_customer_br != "All Customers": d_f = d_f[d_f[c["Customer"]] == selected_customer_br]
                        if selected_category_br != "All Categories": d_f = d_f[d_f[c["Cat"]] == selected_category_br]
                        d_f = d_f[d_f[c["Brand"]] == selected_brand_specific]

                        m_vals = {}
                        for m in MONTHS_ORDER:
                            val = sum_decimal(d_f[d_f[c["Month"]] == m][c[col_key]])
                            m_vals[m] = val
                        
                        selected_months_for_avg = MONTHS_ORDER[:avg_divisor_br]
                        partial_sum = Decimal('0')
                        for m in selected_months_for_avg: partial_sum += m_vals[m]
                            
                        m_vals[sum_col_key] = partial_sum
                        m_vals[avg_col_key] = partial_sum / Decimal(str(avg_divisor_br))
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
                        if m in selected_months_br or m in [sum_col_key, avg_col_key]:
                            row_yoy[disp_name] = yoy_label(yoy_calc(year_data[y_newest][m], year_data[y1][m]))
                        else:
                            row_yoy[disp_name] = "n/a"
                    display_rows.append(row_yoy)

                df_disp = pd.DataFrame(display_rows)
                styled_df = style_monthly_table(df_disp)
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

            render_brand_monthly_table()

            st.divider()
            st.markdown("### Market Penetration (Countries & Customers)")
            
            if br_valid_dfs_chrono:
                d_latest, y_latest, c_latest = br_valid_dfs_chrono[-1]
                
                g_country = d_latest.groupby(c_latest["Country"]).agg({c_latest["Net"]: sum_decimal}).reset_index()
                g_country[f"Net {y_latest}"] = g_country[c_latest["Net"]].apply(lambda x: float(clean_number(x)))
                
                tot = g_country[f"Net {y_latest}"].sum()
                if tot > 0:
                    g_country['Share'] = g_country[f"Net {y_latest}"] / tot
                    g_country.loc[g_country['Share'] < 0.01, c_latest["Country"]] = 'Other'
                    g_country = g_country.groupby(c_latest["Country"], as_index=False)[[f"Net {y_latest}"]].sum()
                
                g_cust = d_latest.groupby(c_latest["Customer"]).agg({c_latest["Net"]: sum_decimal}).reset_index()
                g_cust[f"Net {y_latest}"] = g_cust[c_latest["Net"]].apply(lambda x: float(clean_number(x)))
                
                tot_c = g_cust[f"Net {y_latest}"].sum()
                if tot_c > 0:
                    g_cust['Share'] = g_cust[f"Net {y_latest}"] / tot_c
                    g_cust.loc[g_cust['Share'] < 0.01, c_latest["Customer"]] = 'Other'
                    g_cust = g_cust.groupby(c_latest["Customer"], as_index=False)[[f"Net {y_latest}"]].sum()
                
                c_pie1, c_pie2 = st.columns(2)
                
                with c_pie1:
                    st.write(f"#### Top Countries for {selected_brand_specific} ({y_latest})")
                    st.plotly_chart(px.pie(g_country, names=c_latest["Country"], values=f"Net {y_latest}", color=c_latest["Country"], color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

                with c_pie2:
                    st.write(f"#### Top Customers for {selected_brand_specific} ({y_latest})")
                    st.plotly_chart(px.pie(g_cust, names=c_latest["Customer"], values=f"Net {y_latest}", color=c_latest["Customer"], color_discrete_map=GLOBAL_COLOR_MAP), use_container_width=True)

            st.divider()
            st.markdown(f"### Top 10 SKUs for {selected_brand_specific}")
            if br_valid_dfs_chrono:
                d_latest, y_latest, c_latest = br_valid_dfs_chrono[-1]
                sku_df = d_latest.groupby(c_latest["Code"]).agg({c_latest["Desc"]: "first", c_latest["Net"]: sum_decimal, c_latest["Qty"]: sum_decimal}).reset_index()
                sku_df = sort_by_col_desc(sku_df, c_latest["Net"]).head(10)
                
                sku_disp = sku_df.copy()
                sku_disp[c_latest["Net"]] = sku_disp.get(c_latest["Net"], pd.Series(dtype=int)).apply(to_display_num)
                sku_disp[c_latest["Qty"]] = sku_disp.get(c_latest["Qty"], pd.Series(dtype=int)).apply(to_display_num)
                sku_disp = sku_disp.rename(columns={c_latest["Code"]: "Code", c_latest["Desc"]: "Description", c_latest["Net"]: f"Net {y_latest}", c_latest["Qty"]: f"Qty {y_latest}"})
                
                st.dataframe(add_index(sku_disp[["Code", "Description", f"Net {y_latest}", f"Qty {y_latest}"]]), use_container_width=True)

# ================= CUSTOMER CHURN & ACQUISITION =================
with tab_churn:
    st.header("⚠️ Customer Churn & Acquisition")
    
    dfs_ch = [d for d in [df_curr, df_prev, df_old2] if d is not None]
    if len(dfs_ch) < 2:
        st.warning("Please upload at least 2 years of data to analyze Churn & Acquisition.")
    else:
        st.info("ℹ️ This analysis strictly compares the **Newest Year** vs the **Previous Year** based on your selected months. \n* **New Customer:** Sales > 0 in New Year, and 0 in Previous Year.\n* **Lost Customer:** Sales > 0 in Previous Year, and <= 0 in New Year.")
        
        base_cols = hierarchy_cols
        df_all_ch = pd.concat(dfs_ch, ignore_index=True)
        
        ch1, ch2, ch3, ch4 = st.columns(4)
        
        countries_ch = ["All Countries"] + sorted(df_all_ch[base_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
        selected_country_ch = ch1.selectbox("🌎 Country", countries_ch, key="ch_country")

        categories_ch = ["All Categories"] + sorted(df_all_ch[base_cols["Cat"]].dropna().unique().tolist())
        selected_category_ch = ch2.selectbox("📦 Category", categories_ch, key="ch_category")

        brands_ch = ["All Brands"] + sorted(df_all_ch[base_cols["Brand"]].dropna().unique().tolist())
        selected_brand_ch = ch3.selectbox("🏷️ Brand", brands_ch, key="ch_brand")

        options_ch_m = MONTHS_ORDER 
        default_ch_m = [m for m in hierarchy_months if m in options_ch_m]
        if not default_ch_m: default_ch_m = options_ch_m
        
        if "ch_months" not in st.session_state:
            st.session_state["ch_months"] = default_ch_m
            
        selected_months_ch = ch4.multiselect("📅 Months", options=options_ch_m, key="ch_months")

        ch_valid_dfs = []
        for orig_d, y, c in zip([df_old2, df_prev, df_curr], [year_old2, year_prev, year_curr], [cols_old2, cols_prev, cols_curr]):
            if orig_d is not None:
                d_f = orig_d.copy()
                if selected_country_ch != "All Countries": d_f = d_f[d_f[c["Country"]] == selected_country_ch]
                if selected_category_ch != "All Categories": d_f = d_f[d_f[c["Cat"]] == selected_category_ch]
                if selected_brand_ch != "All Brands": d_f = d_f[d_f[c["Brand"]] == selected_brand_ch]
                if selected_months_ch: d_f = d_f[d_f[c["Month"]].isin(selected_months_ch)] 
                
                if not d_f.empty:
                    ch_valid_dfs.append((d_f, y, c))
                
        ch_valid_dfs_chrono = sorted(ch_valid_dfs, key=lambda x: x[1])
        
        if len(ch_valid_dfs_chrono) >= 2:
            d_new, y_new, c_new = ch_valid_dfs_chrono[-1]
            d_old, y_old, c_old = ch_valid_dfs_chrono[-2]
            
            g_new = d_new.groupby(c_new["Customer"]).agg({c_new["Net"]: sum_decimal}).reset_index().rename(columns={c_new["Customer"]: "Customer", c_new["Net"]: "Net_New"})
            g_old = d_old.groupby(c_old["Customer"]).agg({c_old["Net"]: sum_decimal}).reset_index().rename(columns={c_old["Customer"]: "Customer", c_old["Net"]: "Net_Old"})
            
            merged_ch = pd.merge(g_new, g_old, on="Customer", how="outer").fillna(Decimal('0'))
            
            merged_ch['Status'] = 'Retained'
            merged_ch.loc[(merged_ch['Net_Old'] <= Decimal('0')) & (merged_ch['Net_New'] > Decimal('0')), 'Status'] = 'New'
            merged_ch.loc[(merged_ch['Net_Old'] > Decimal('0')) & (merged_ch['Net_New'] <= Decimal('0')), 'Status'] = 'Lost'
            
            df_new_cust = merged_ch[merged_ch['Status'] == 'New'].copy()
            df_lost_cust = merged_ch[merged_ch['Status'] == 'Lost'].copy()
            
            val_acquired = df_new_cust['Net_New'].sum()
            val_lost = df_lost_cust['Net_Old'].sum()
            net_impact = val_acquired - val_lost
            
            st.divider()
            st.markdown(f"### Acquisition & Churn KPIs ({y_old} ➔ {y_new})")
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Acquired Value (from New Customers)", f"{format_number_plain(val_acquired)} EUR", f"{len(df_new_cust)} Customers")
            
            # Wymuszenie czerwonego koloru dla strat i zielonego dla wzrostów
            kpi2.metric("Lost Value (from Churned Customers)", f"{format_number_plain(val_lost)} EUR", f"-{len(df_lost_cust)} Customers", delta_color="normal")
            
            impact_color = "normal" if net_impact >= 0 else "inverse"
            kpi3.metric("Net Flow (Acquired - Lost)", f"{format_number_plain(net_impact)} EUR", delta_color=impact_color)
            
            st.divider()
            col_new, col_lost = st.columns(2)
            
            with col_new:
                st.markdown(f"#### 🟢 Top 10 New Customers ({y_new})")
                df_new_cust = df_new_cust.sort_values("Net_New", ascending=False).head(10)
                disp_new = df_new_cust[["Customer", "Net_New"]].copy()
                disp_new["Net_New"] = disp_new["Net_New"].apply(to_display_num)
                disp_new = disp_new.rename(columns={"Net_New": f"Net {y_new} (EUR)"})
                if disp_new.empty:
                    st.info("No new customers found for this criteria.")
                else:
                    st.dataframe(add_index(disp_new), use_container_width=True)
                    
            with col_lost:
                st.markdown(f"#### 🔴 Top 10 Lost Customers (Bought in {y_old}, 0 in {y_new})")
                df_lost_cust = df_lost_cust.sort_values("Net_Old", ascending=False).head(10)
                disp_lost = df_lost_cust[["Customer", "Net_Old"]].copy()
                disp_lost["Net_Old"] = disp_lost["Net_Old"].apply(to_display_num)
                disp_lost = disp_lost.rename(columns={"Net_Old": f"Lost Net from {y_old} (EUR)"})
                if disp_lost.empty:
                    st.success("No churned customers found for this criteria!")
                else:
                    st.dataframe(add_index(disp_lost), use_container_width=True)
        else:
            st.info("Not enough data to calculate comparison KPIs (need at least 2 valid years for the selected filters).")
