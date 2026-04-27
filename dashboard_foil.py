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
    """Format YoY percentage directly as a string with arrows and colors for tables."""
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
    """Format standard percentage directly as a string with % sign."""
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

# ================= HELPERS & CORE UTILS =================
def add_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

def format_number_plain(d, decimals: int = DISPLAY_DECIMALS) -> str:
    """Format into string - strictly used for Metrics/KPIs (not DataFrames!)"""
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
    """Convert Decimal into int/float so Streamlit sorts it numerically in DataFrames."""
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
    if "article" in x: return "Articles"
    if "horn" in x: return "Horns"
    return "Other"

# Added 'Horns' and 'Other' to prevent ANY row from being excluded
ALLOWED_CATEGORIES = [
    "Napkins", "Hats", "Banner", "Straws", "Bags", "Plates", "Paper Cups",
    "Tablecover", "Reusable", "Foil", "Wooden", "Candles", "Latex",
    "Invitations", "Articles", "Masks", "Pinata", "Plastic Cups", "Horns", "Other"
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
        if str(c).strip().lower() == "month":
            month_col = c
            break
    if month_col is None: month_col = df.columns[0]

    customer_col = None
    for c in df.columns:
        if "customer" in str(c).lower():
            customer_col = c
            break
    if customer_col is None: customer_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    country_col = None
    for c in df.columns:
        if "country" in str(c).lower():
            country_col = c
            break
    if country_col is None: country_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]

    code_col = None
    for c in df.columns:
        if "art" in str(c).lower() and "nr" in str(c).lower():
            code_col = c
            break
    if code_col is None: code_col = df.columns[4] if len(df.columns) > 4 else df.columns[0]

    desc_col = None
    for c in df.columns:
        if "description" in str(c).lower():
            desc_col = c
            break
    if desc_col is None: desc_col = df.columns[5] if len(df.columns) > 5 else df.columns[0]

    brand_col = None
    for c in df.columns:
        if "brand" in str(c).lower():
            brand_col = c
            break
    if brand_col is None: brand_col = df.columns[6] if len(df.columns) > 6 else df.columns[0]

    cat_col = None
    for c in df.columns:
        if "category" in str(c).lower():
            cat_col = c
            break
    if cat_col is None: cat_col = df.columns[7] if len(df.columns) > 7 else df.columns[0]

    net_col = None
    qty_col = None
    for c in df.columns:
        cl = str(c).lower()
        if net_col is None and ("net" in cl or "value" in cl or "sales" in cl):
            net_col = c
        elif qty_col is None and ("qty" in cl or "quantity" in cl or "pcs" in cl):
            qty_col = c
    if net_col is None: net_col = df.columns[-2] if len(df.columns) >= 2 else df.columns[-1]
    if qty_col is None: qty_col = df.columns[-1]

    df[net_col] = df[net_col].apply(clean_number)
    df[qty_col] = df[qty_col].apply(clean_number)

    # STANDARDIZACJA KOLUMN - Zabezpiecza przed błędem KeyError niezależnie od nagłówków w plikach
    df["Month_Clean"] = df[month_col].astype(str).fillna("").replace("nan", "")
    df["Customer_Clean"] = df[customer_col].astype(str).fillna("").replace("nan", "")
    df["Country_Clean"] = df[country_col].astype(str).fillna("").replace("nan", "")
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


def apply_shared_filters(dfs, cols, unique_prefix: str):
    if not dfs:
        return [], None

    df_all = pd.concat(dfs, ignore_index=True)

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

    filtered_dfs = []
    for df in dfs:
        d = df.copy()
        if selected_country != "All Countries":
            d = d[d[cols["Country"]] == selected_country]
        if selected_customer != "All Customers":
            d = d[d[cols["Customer"]] == selected_customer]
        if selected_category != "All Categories":
            d = d[d[cols["Cat"]] == selected_category]
        filtered_dfs.append(d)

    meta = {
        "country": selected_country,
        "customer": selected_customer,
        "category": selected_category,
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
):
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
        # Zabezpieczenie przed ujemnymi wartościami w Pie Chart
        plot_cat.loc[plot_cat[f"Net {year_new}"] < 0, f"Net {year_new}"] = 0
        plot_cat.loc[plot_cat[f"Net {year_old}"] < 0, f"Net {year_old}"] = 0

        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown(f"#### Category Pie {year_old}")
            st.plotly_chart(
                px.pie(plot_cat, names=cat_col, values=f"Net {year_old}"),
                use_container_width=True,
            )
        with pc2:
            st.markdown(f"#### Category Pie {year_new}")
            st.plotly_chart(
                px.pie(plot_cat, names=cat_col, values=f"Net {year_new}"),
                use_container_width=True,
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
            px.pie(bplot, names=brand_col, values=f"Net {year_old}"),
            use_container_width=True,
        )
    with bc2:
        st.markdown(f"#### Brand Pie {year_new}")
        st.plotly_chart(
            px.pie(bplot, names=brand_col, values=f"Net {year_new}"),
            use_container_width=True,
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
        .agg({net_old: sum_decimal, qty_old: sum_decimal})
        .reset_index()
    )
    yoy = pd.merge(yoy_df_new, yoy_df_old, on=code_col, how="outer").fillna(
        Decimal('0')
    )
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

    # AUTO INSIGHTS (TOP 5, GROWTH, RISK)
    st.markdown("### Auto Insights")

    cat_new_ins = (
        df_new.groupby(cat_col)
        .agg({net_new: sum_decimal})
        .reset_index()
        .rename(columns={net_new: f"Net {year_new}"})
    )
    cat_old_ins = (
        df_old.groupby(cat_col)
        .agg({net_old: sum_decimal})
        .reset_index()
        .rename(columns={net_old: f"Net {year_old}"})
    )
    cat_ins = pd.merge(cat_new_ins, cat_old_ins, on=cat_col, how="outer").fillna(
        Decimal('0')
    )
    cat_ins["YoY"] = cat_ins.apply(
        lambda x: yoy_calc(x.get(f"Net {year_new}", Decimal('0')), x.get(f"Net {year_old}", Decimal('0'))), axis=1
    ) if not cat_ins.empty else []
    
    cat_ins = sort_by_col_desc(cat_ins, f"Net {year_new}")

    st.write("#### Top 5 Categories")
    ic1, ic2 = st.columns(2)
    with ic1:
        top_old_cat = cat_ins.sort_values(f"Net {year_old}", ascending=False).head(5)
        disp_old_cat = top_old_cat.copy()
        disp_old_cat[f"Net {year_old}"] = disp_old_cat.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        st.dataframe(
            add_index(disp_old_cat[[cat_col, f"Net {year_old}"]])
        )
    with ic2:
        top_new_cat = cat_ins.sort_values(f"Net {year_new}", ascending=False).head(5)
        disp_new_cat = top_new_cat.copy()
        disp_new_cat[f"Net {year_new}"] = disp_new_cat.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        disp_new_cat["YoY (%)"] = disp_new_cat.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(
            add_index(
                disp_new_cat[[cat_col, f"Net {year_new}", "YoY (%)"]]
            )
        )

    st.write("#### Top 5 Growth (L4L)")
    growth = cat_ins[cat_ins["YoY"] > 0].sort_values("YoY", ascending=False).head(5)
    if growth.empty:
        st.info("There is no growth in categories.")
    else:
        g_disp = growth.copy()
        g_disp[f"Net {year_old}"] = g_disp.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        g_disp[f"Net {year_new}"] = g_disp.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        g_disp["YoY (%)"] = g_disp.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(
            add_index(
                g_disp[
                    [
                        cat_col,
                        f"Net {year_old}",
                        f"Net {year_new}",
                        "YoY (%)",
                    ]
                ]
            )
        )

    st.write("#### Top 5 Risk")
    risk = cat_ins[cat_ins["YoY"] < 0].sort_values("YoY").head(5)
    if risk.empty:
        st.success("There is no risk in categories.")
    else:
        r_disp = risk.copy()
        r_disp[f"Net {year_old}"] = r_disp.get(f"Net {year_old}", pd.Series(dtype=int)).apply(to_display_num)
        r_disp[f"Net {year_new}"] = r_disp.get(f"Net {year_new}", pd.Series(dtype=int)).apply(to_display_num)
        r_disp["YoY (%)"] = r_disp.get("YoY", pd.Series(dtype=str)).apply(yoy_label)
        st.dataframe(
            add_index(
                r_disp[
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
    df: pd.DataFrame, cols: dict, year_name: str, unique_prefix: str, category_filter: str
):
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
            px.pie(plot_cat, names=cat_col, values=f"Net {year_name}"),
            use_container_width=True,
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
        px.pie(bplot, names=brand_col, values=f"Net {year_name}"),
        use_container_width=True,
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


# ================= MAIN APP =================
st.set_page_config(layout="wide", page_title="Sales Intelligence Dashboard")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha")

st.markdown("### Excel Upload (3 separate years)")
c_up1, c_up2, c_up3 = st.columns(3)
with c_up1:
    file_two_years_ago = st.file_uploader("Older Year (2 years ago)", type=["xlsx"])
with c_up2:
    file_prev_year = st.file_uploader("Previous Year", type=["xlsx"])
with c_up3:
    file_current_year = st.file_uploader("Current Year (YTD)", type=["xlsx"])

if not file_prev_year and not file_current_year and not file_two_years_ago:
    st.info("Upload at least one Excel file.")
    st.stop()

df_old2, cols_old2, year_old2 = load_single_year_file(
    file_two_years_ago, "older"
) if file_two_years_ago is not None else (None, None, None)

df_prev, cols_prev, year_prev = load_single_year_file(
    file_prev_year, "prev"
) if file_prev_year is not None else (None, None, None)

df_curr, cols_curr, year_curr = load_single_year_file(
    file_current_year, "curr"
) if file_current_year is not None else (None, None, None)

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
    st.header("Overview — 3-year Comparison")

    all_dfs = [df_curr, df_prev, df_old2]
    loaded_dfs = [d for d in all_dfs if d is not None]

    if len(loaded_dfs) < 1:
        st.warning("Please upload data.")
    else:
        # Detekcja wspólnych miesięcy
        common_months = MONTHS_ORDER.copy()
        for d, c in zip([df_curr, df_prev, df_old2], [cols_curr, cols_prev, cols_old2]):
            if d is not None:
                common_months = [m for m in common_months if m in d[c["Month"]].unique().tolist()]

        st.info(f"Detected common months: {', '.join(common_months)}" if common_months else "No common months detected.")
        selected_months = st.multiselect("Select months for Overview YTD", MONTHS_ORDER, default=common_months, key="ov_months")

        if selected_months:
            # Aplikacja filtra miesięcy
            df_curr_ytd = df_curr[df_curr[cols_curr["Month"]].isin(selected_months)] if df_curr is not None else None
            df_prev_ytd = df_prev[df_prev[cols_prev["Month"]].isin(selected_months)] if df_prev is not None else None
            df_old2_ytd = df_old2[df_old2[cols_old2["Month"]].isin(selected_months)] if df_old2 is not None else None

            st.markdown("### 🛠️ Global Filters")
            
            # Ekstrakcja zunifikowanych kolumn bazowych dla filtrów
            ytd_valid_dfs = [d for d in [df_old2_ytd, df_prev_ytd, df_curr_ytd] if d is not None]
            base_cols = cols_curr if cols_curr else (cols_prev if cols_prev else cols_old2)
            df_concat = pd.concat(ytd_valid_dfs, ignore_index=True)

            c1, c2, c3 = st.columns(3)
            all_countries = ["All Countries"] + sorted(df_concat[base_cols["Country"]].replace("", pd.NA).dropna().unique().tolist())
            selected_country = c1.selectbox("🌎 Country", all_countries, key="ov_country")

            df_for_cust = df_concat[df_concat[base_cols["Country"]] == selected_country] if selected_country != "All Countries" else df_concat.copy()
            all_customers = ["All Customers"] + sorted(df_for_cust[base_cols["Customer"]].replace("", pd.NA).dropna().unique().tolist())
            selected_customer = c2.selectbox("🏢 Customer", all_customers, key="ov_customer")

            all_categories = ["All Categories"] + sorted(df_for_cust[base_cols["Cat"]].dropna().unique().tolist())
            selected_category = c3.selectbox("📦 Category", all_categories, key="ov_category")

            def filter_custom(df, c, country, customer, category):
                if df is None: return None
                d = df.copy()
                if country != "All Countries": d = d[d[c["Country"]] == country]
                if customer != "All Customers": d = d[d[c["Customer"]] == customer]
                if category != "All Categories": d = d[d[c["Cat"]] == category]
                return d

            # ========= SEKCJ 1: Wykres główny NET =========
            st.divider()
            st.markdown("### 1. Net Value Comparison (Global Filters Applied)")
            
            vals = []
            years = []
            if df_old2_ytd is not None: 
                d = filter_custom(df_old2_ytd, cols_old2, selected_country, selected_customer, selected_category)
                vals.append(float(sum_decimal(d[cols_old2["Net"]])))
                years.append(year_old2)
            if df_prev_ytd is not None: 
                d = filter_custom(df_prev_ytd, cols_prev, selected_country, selected_customer, selected_category)
                vals.append(float(sum_decimal(d[cols_prev["Net"]])))
                years.append(year_prev)
            if df_curr_ytd is not None: 
                d = filter_custom(df_curr_ytd, cols_curr, selected_country, selected_customer, selected_category)
                vals.append(float(sum_decimal(d[cols_curr["Net"]])))
                years.append(year_curr)

            if vals:
                st.plotly_chart(px.bar(pd.DataFrame({"Year": years, "Net (EUR)": vals}), x="Year", y="Net (EUR)", text="Net (EUR)", title="Net Value YTD", color="Year"), use_container_width=True)

            # Reusable 3-Year Analysis Tool
            def render_three_year_analysis(group_col, section_title, dfs, year_list, cols_list, display_name):
                st.divider()
                st.markdown(f"### {section_title}")
                
                group_dfs = []
                for df, y, c in zip(dfs, year_list, cols_list):
                    if df is not None:
                        net_col = c["Net"]
                        g = df.groupby(group_col).agg({net_col: sum_decimal}).reset_index().rename(columns={net_col: f"Net {y}"})
                        group_dfs.append((g, y))

                if group_dfs:
                    master = group_dfs[0][0]
                    for g, y in group_dfs[1:]:
                        master = pd.merge(master, g, on=group_col, how="outer")
                    master = master.fillna(Decimal('0'))

                    if len(group_dfs) >= 2:
                        y1, y2 = group_dfs[-2][1], group_dfs[-1][1]
                        master[f"YoY {y2} vs {y1}"] = master.apply(lambda x: yoy_calc(x.get(f"Net {y2}", 0), x.get(f"Net {y1}", 0)), axis=1) if not master.empty else []
                    if len(group_dfs) == 3:
                        y0, y1 = group_dfs[0][1], group_dfs[1][1]
                        master[f"YoY {y1} vs {y0}"] = master.apply(lambda x: yoy_calc(x.get(f"Net {y1}", 0), x.get(f"Net {y0}", 0)), axis=1) if not master.empty else []

                    last_year = group_dfs[-1][1]
                    master = sort_by_col_desc(master, f"Net {last_year}")

                    # WYKRESY KOŁOWE
                    pie_cols = st.columns(len(group_dfs))
                    for i, (g, y) in enumerate(group_dfs):
                        plot_df = master.copy()
                        plot_df[f"Net {y}"] = plot_df.get(f"Net {y}", pd.Series(dtype=float)).apply(lambda v: float(clean_number(v)))
                        plot_df.loc[plot_df[f"Net {y}"] < 0, f"Net {y}"] = 0 # Safety for Pie charts
                        with pie_cols[i]:
                            st.plotly_chart(px.pie(plot_df, names=group_col, values=f"Net {y}", title=f"{display_name} Pie {y}"), use_container_width=True)

                    # TABELA WYNIKOWA
                    display_df = master.copy()
                    for g, y in group_dfs:
                        display_df[f"Net {y}"] = display_df.get(f"Net {y}", pd.Series(dtype=int)).apply(to_display_num)
                    
                    if len(group_dfs) >= 2:
                        display_df[f"YoY {y2} vs {y1} (%)"] = display_df.get(f"YoY {y2} vs {y1}", pd.Series(dtype=str)).apply(yoy_label)
                        display_df = display_df.drop(columns=[f"YoY {y2} vs {y1}"])
                    if len(group_dfs) == 3:
                        display_df[f"YoY {y1} vs {y0} (%)"] = display_df.get(f"YoY {y1} vs {y0}", pd.Series(dtype=str)).apply(yoy_label)
                        display_df = display_df.drop(columns=[f"YoY {y1} vs {y0}"])
                        
                    display_df = display_df.rename(columns={group_col: display_name})
                    st.dataframe(add_index(display_df), use_container_width=True)

            base_dfs = [df_old2_ytd, df_prev_ytd, df_curr_ytd]
            base_years = [year_old2, year_prev, year_curr]
            base_col_maps = [cols_old2, cols_prev, cols_curr]

            # ========= SEKCJA 2: Category =========
            dfs_cat = [filter_custom(d, c, selected_country, selected_customer, "All Categories") if d is not None else None for d, c in zip(base_dfs, base_col_maps)]
            render_three_year_analysis(base_cols["Cat"], "2. Category Comparison (Filtered by Country & Customer)", dfs_cat, base_years, base_col_maps, "Category")

            # ========= SEKCJA 3: Brand =========
            dfs_brand = [filter_custom(d, c, selected_country, selected_customer, selected_category) if d is not None else None for d, c in zip(base_dfs, base_col_maps)]
            render_three_year_analysis(base_cols["Brand"], "3. Brand Comparison (Filtered by Country, Customer & Category)", dfs_brand, base_years, base_col_maps, "Brand")

            # ========= SEKCJA 4: Customer Impact =========
            dfs_cust = [filter_custom(d, c, selected_country, "All Customers", selected_category) if d is not None else None for d, c in zip(base_dfs, base_col_maps)]
            render_three_year_analysis(base_cols["Customer"], "4. Customer Comparison (Filtered by Country & Category)", dfs_cust, base_years, base_col_maps, "Customer")


# ================= DETAILED L4L =================
with tab_l4l:
    st.header("Detailed Like-for-Like")

    year_options = []
    year_to_df = {}
    year_to_cols = {}

    if df_old2 is not None:
        year_options.append(year_old2)
        year_to_df[year_old2] = df_old2
        year_to_cols[year_old2] = cols_old2
    if df_prev is not None:
        year_options.append(year_prev)
        year_to_df[year_prev] = df_prev
        year_to_cols[year_prev] = cols_prev
    if df_curr is not None:
        year_options.append(year_curr)
        year_to_df[year_curr] = df_curr
        year_to_cols[year_curr] = cols_curr

    if len(year_options) < 2:
        st.warning("Detailed L4L requires at least two year files.")
    else:
        st.markdown("#### Select years (older on the left, newer on the right)")
        left_year_option = st.selectbox(
            "Older year",
            year_options,
            index=0,
            key="l4l_left_year",
        )
        right_year_option = st.selectbox(
            "Newer year",
            year_options,
            index=1 if len(year_options) > 1 else 0,
            key="l4l_right_year",
        )

        if left_year_option == right_year_option:
            st.error("Older year and newer year must be different.")
        else:
            df_left = year_to_df[left_year_option]
            cols_left = year_to_cols[left_year_option]
            df_right = year_to_df[right_year_option]
            cols_right = year_to_cols[right_year_option]

            months_left = sorted(
                df_left[cols_left["Month"]].dropna().unique().tolist(),
                key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99,
            )
            months_right = sorted(
                df_right[cols_right["Month"]].dropna().unique().tolist(),
                key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99,
            )
            common_months = [m for m in months_left if m in months_right]

            st.info(
                f"Detected common months: {', '.join(common_months)}"
                if common_months
                else "No common months detected."
            )

            selected_months_l4l = st.multiselect(
                "Select months for L4L",
                MONTHS_ORDER,
                default=common_months,
                key="detailed_l4l_months",
            )

            if not selected_months_l4l:
                st.info("Select at least one month.")
            else:
                missing_left = [
                    m
                    for m in selected_months_l4l
                    if m not in df_left[cols_left["Month"]].unique().tolist()
                ]
                missing_right = [
                    m
                    for m in selected_months_l4l
                    if m not in df_right[cols_right["Month"]].unique().tolist()
                ]
                if missing_left:
                    st.error(
                        f"Selected months exceed data for older year: {', '.join(missing_left)}"
                    )
                elif missing_right:
                    st.error(
                        f"Selected months exceed data for newer year: {', '.join(missing_right)}"
                    )
                else:
                    df_left_l4l = df_left[
                        df_left[cols_left["Month"]].isin(selected_months_l4l)
                    ]
                    df_right_l4l = df_right[
                        df_right[cols_right["Month"]].isin(selected_months_l4l)
                    ]

                    st.markdown("### Filters for Detailed L4L")
                    filtered_list, meta = apply_shared_filters(
                        [df_left_l4l, df_right_l4l],
                        cols_left,
                        unique_prefix="l4l",
                    )
                    left_filtered, right_filtered = filtered_list

                    render_two_year_dashboard(
                        df_new=right_filtered,
                        df_old=left_filtered,
                        cols_new=cols_right,
                        cols_old=cols_left,
                        context_name="detailed_l4l",
                        unique_prefix="detailed_l4l",
                        category_filter=meta["category"],
                    )

# ================= FULL YEAR ANALYSIS =================
with tab_full:
    st.header("Full Year Analysis")

    available_years = []
    year_map_df = {}
    year_map_cols = {}

    if df_old2 is not None:
        available_years.append(year_old2)
        year_map_df[year_old2] = df_old2
        year_map_cols[year_old2] = cols_old2
    if df_prev is not None:
        available_years.append(year_prev)
        year_map_df[year_prev] = df_prev
        year_map_cols[year_prev] = cols_prev
    if df_curr is not None:
        available_years.append(year_curr)
        year_map_df[year_curr] = df_curr
        year_map_cols[year_curr] = cols_curr

    if not available_years:
        st.info("No years available for full year analysis.")
    else:
        selected_full = st.selectbox(
            "Select year for full year analysis", available_years, key="full_year_sel"
        )
        df_selected = year_map_df[selected_full]
        cols_selected = year_map_cols[selected_full]

        st.markdown("### Filters for Full Year")
        filtered_selected, meta = create_single_filters(
            df_selected, cols_selected, unique_prefix="full"
        )

        render_single_year_dashboard(
            filtered_selected,
            cols_selected,
            selected_full,
            unique_prefix="full_dash",
            category_filter=meta["category"],
        )
