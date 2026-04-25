import streamlit as st
import pandas as pd
import plotly.express as px
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ========================= CONFIG =========================
DISPLAY_DECIMALS = 0  # 0 or 1
MONTHS_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# ========================= HELPERS =========================
def to_decimal(x):
    if pd.isna(x):
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    try:
        if isinstance(x, int):
            return Decimal(x)
        if isinstance(x, float):
            return Decimal(str(x))
        s = str(x).strip().replace(" ", "").replace(",", ".")
        if s == "" or s.lower() == "nan":
            return Decimal("0")
        return Decimal(s)
    except (InvalidOperation, Exception):
        return Decimal("0")


def decimal_sum(series):
    try:
        return sum((to_decimal(v) for v in series.tolist()), Decimal("0"))
    except Exception:
        return Decimal("0")


def safe_div(a: Decimal, b: Decimal) -> Decimal:
    try:
        if b == 0:
            return Decimal("0")
        return a / b
    except (InvalidOperation, ZeroDivisionError):
        return Decimal("0")


def calc_yoy_clean(new: Decimal, old: Decimal):
    try:
        if old < 0 and new == 0:
            return None
        if old == 0:
            return Decimal("100") if new > 0 else Decimal("0")
        if old > 0 and new == 0:
            return Decimal("-100")
        return (new - old) / abs(old) * Decimal("100")
    except Exception:
        return None


def yoy_label(val, special: bool = False):
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


def format_number_plain(d, decimals: int = DISPLAY_DECIMALS) -> str:
    try:
        if not isinstance(d, Decimal):
            d = to_decimal(d)
        if decimals == 0:
            q = d.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            return str(int(q))
        q = d.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        return f"{q:.1f}"
    except (InvalidOperation, Exception):
        return "0"


def add_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df


def sort_by_col_desc(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col not in df.columns:
        return df
    try:
        return df.sort_values(by=col, ascending=False)
    except Exception:
        tmp = df.copy()
        tmp[col] = tmp[col].apply(lambda x: float(to_decimal(x)))
        return tmp.sort_values(by=col, ascending=False)


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


ALLOWED_CATEGORIES = [
    "Napkins", "Hats", "Banner", "Straws", "Bags", "Plates", "Paper Cups",
    "Tablecover", "Reusable", "Foil", "Wooden", "Candles", "Latex",
    "Invitations", "Articles", "Masks", "Pinata", "Plastic Cups"
]

# ========================= DATA LOADING =========================
def load_and_prep_data(file, label: str):
    if file is None:
        return None, None
    df = pd.read_excel(file, dtype=object, engine="openpyxl")
    df.columns = df.columns.str.strip()

    col_map = {}

    def find_col(possible_names, fallback_idx=None):
        for n in df.columns:
            if str(n).strip().lower() in [p.lower() for p in possible_names]:
                return n
        if fallback_idx is not None and fallback_idx < len(df.columns):
            return df.columns[fallback_idx]
        return None

    col_map["Month"] = find_col(["Month"], 0)
    col_map["Customer"] = find_col(["Customer Name", "Customer"], 1)
    col_map["Country"] = find_col(["Country"], 2)
    col_map["Vat"] = find_col(["Vat ID Nr.", "VAT", "Vat"], 3)
    col_map["Code"] = find_col(["Art. Nr.", "Article Number", "SKU"], 4)
    col_map["Desc"] = find_col(["Article description", "Description"], 5)
    col_map["Brand"] = find_col(["Brand Name", "Brand"], 6)
    col_map["Cat"] = find_col(["Category"], 7)
    col_map["Net"] = find_col(["Net Value", "Net", "NetValue"], 8)
    col_map["Qty"] = find_col(["Quantity", "Qty"], 9)
    col_map["Year"] = find_col(["Year"], None)

    required = ["Month", "Customer", "Country", "Code", "Desc", "Brand", "Cat", "Net", "Qty"]
    missing = [k for k in required if col_map.get(k) is None]
    if missing:
        st.error(f"File '{label}': missing required columns: {missing}")
        return None, None

    df[col_map["Net"]] = df[col_map["Net"]].apply(to_decimal)
    df[col_map["Qty"]] = df[col_map["Qty"]].apply(to_decimal)

    for key in ["Month", "Customer", "Country", "Vat", "Code", "Desc", "Brand", "Cat", "Year"]:
        c = col_map.get(key)
        if c is None:
            continue
        df[c] = df[c].astype(str).fillna("").replace("nan", "")

    df["Category Clean"] = df[col_map["Cat"]].apply(normalize_category)
    df = df[df["Category Clean"].isin(ALLOWED_CATEGORIES)]
    df = df[df[col_map["Desc"]].notna()]
    df = df[df[col_map["Desc"]].str.lower() != "none"]

    return df, col_map


def get_year_label(df, cols, fallback: str) -> str:
    year_col_name = cols.get("Year")
    if year_col_name and year_col_name in df.columns:
        vals = [v for v in df[year_col_name].unique().tolist() if str(v).strip() != ""]
        if len(vals) == 1:
            return str(vals[0])
    return fallback


# ========================= FILTERS =========================
def create_and_apply_filters(df, cols, prefix: str):
    if df is None or cols is None:
        return None, None, None, None

    country_col = cols["Country"]
    customer_col = cols["Customer"]
    cat_col = "Category Clean"

    countries = ["All Countries"] + sorted(df[country_col].replace("", pd.NA).dropna().unique())
    customers = ["All Customers"] + sorted(df[customer_col].replace("", pd.NA).dropna().unique())
    categories = ["All Categories"] + sorted(df[cat_col].dropna().unique())

    sel_country = st.selectbox(
        "Country",
        countries,
        key=f"{prefix}_country"
    )
    sel_customer = st.selectbox(
        "Customer",
        customers,
        key=f"{prefix}_customer"
    )
    sel_category = st.selectbox(
        "Category",
        categories,
        key=f"{prefix}_category"
    )

    d = df.copy()
    if sel_country != "All Countries":
        d = d[d[country_col] == sel_country]
    if sel_customer != "All Customers":
        d = d[d[customer_col] == sel_customer]
    if sel_category != "All Categories":
        d = d[d["Category Clean"] == sel_category]

    return d, sel_country, sel_customer, sel_category


def customer_impact_with_filters(df_old, cols_old, df_new, cols_new, prefix: str, title_prefix: str):
    if df_old is None or cols_old is None or df_new is None or cols_new is None:
        st.info("Customer impact not available.")
        return

    cat_all = sorted(list(set(df_old["Category Clean"].dropna().unique()) |
                          set(df_new["Category Clean"].dropna().unique())))
    brand_all = sorted(list(set(df_old[cols_old["Brand"]].dropna().unique()) |
                            set(df_new[cols_new["Brand"]].dropna().unique())))

    sel_cat = st.selectbox(
        "Impact Category",
        ["All Categories"] + cat_all,
        key=f"{prefix}_impact_cat"
    )
    sel_brand = st.selectbox(
        "Impact Brand (License)",
        ["All Brands"] + brand_all,
        key=f"{prefix}_impact_brand"
    )

    def apply_cb_filters(df, cols):
        if df is None:
            return None
        d = df.copy()
        if sel_cat != "All Categories":
            d = d[d["Category Clean"] == sel_cat]
        if sel_brand != "All Brands":
            d = d[d[cols["Brand"]] == sel_brand]
        return d

    df_old_f = apply_cb_filters(df_old, cols_old)
    df_new_f = apply_cb_filters(df_new, cols_new)

    if df_old_f is None or df_new_f is None or df_old_f.empty and df_new_f.empty:
        st.info("No data for selected impact filters.")
        return

    cust_old_col = cols_old["Customer"]
    cust_new_col = cols_new["Customer"]
    net_old_col = cols_old["Net"]
    net_new_col = cols_new["Net"]

    old_agg = df_old_f.groupby(cust_old_col).agg({net_old_col: decimal_sum}).reset_index()
    new_agg = df_new_f.groupby(cust_new_col).agg({net_new_col: decimal_sum}).reset_index()

    impact = pd.merge(
        old_agg,
        new_agg,
        left_on=cust_old_col,
        right_on=cust_new_col,
        how="outer"
    ).fillna(Decimal("0"))

    impact["Customer"] = impact[cust_old_col].where(
        impact[cust_old_col] != "",
        impact[cust_new_col]
    )

    impact["Net_Old"] = impact[net_old_col].apply(to_decimal)
    impact["Net_New"] = impact[net_new_col].apply(to_decimal)

    impact["Change Value"] = impact["Net_New"] - impact["Net_Old"]
    impact["YoY"] = impact.apply(
        lambda x: calc_yoy_clean(x["Net_New"], x["Net_Old"]),
        axis=1
    )
    impact["YoY %"] = impact["YoY"].apply(yoy_label)

    impact = impact[(impact["Net_Old"] != 0) | (impact["Net_New"] != 0)]

    st.markdown(f"## 👥 Customer Impact – {title_prefix}")
    c1, c2 = st.columns(2)

    with c1:
        st.write("### 🟢 Top Growth Drivers")
        growth = impact[impact["Change Value"] > 0].copy()
        growth = sort_by_col_desc(growth, "Change Value").head(10)
        if growth.empty:
            st.info("No growth generated by customers.")
        else:
            g_disp = growth.copy()
            for col in ["Net_Old", "Net_New", "Change Value"]:
                g_disp[col] = g_disp[col].apply(format_number_plain)
            st.dataframe(add_index(g_disp[["Customer", "Net_Old", "Net_New", "Change Value", "YoY %"]]))

    with c2:
        st.write("### 🔴 Top Decline Drivers")
        decline = impact[impact["Change Value"] < 0].copy()
        decline = decline.sort_values("Change Value").head(10)
        if decline.empty:
            st.success("No decline across customers.")
        else:
            d_disp = decline.copy()
            for col in ["Net_Old", "Net_New", "Change Value"]:
                d_disp[col] = d_disp[col].apply(format_number_plain)
            st.dataframe(add_index(d_disp[["Customer", "Net_Old", "Net_New", "Change Value", "YoY %"]]))

    st.divider()


# ========================= TWO-YEAR DASHBOARD (L4L / DETAILED) =========================
def render_two_year_dashboard(df_old, cols_old, df_new, cols_new, prefix: str, context_name: str, months_filter=None):
    if df_old is None or cols_old is None or df_new is None or cols_new is None:
        st.info("Two-year view not available.")
        return

    net_old_col = cols_old["Net"]
    qty_old_col = cols_old["Qty"]
    net_new_col = cols_new["Net"]
    qty_new_col = cols_new["Qty"]
    code_old_col = cols_old["Code"]
    code_new_col = cols_new["Code"]
    desc_old_col = cols_old["Desc"]
    desc_new_col = cols_new["Desc"]
    brand_old_col = cols_old["Brand"]
    brand_new_col = cols_new["Brand"]

    year_old_label = get_year_label(df_old, cols_old, "Older Year")
    year_new_label = get_year_label(df_new, cols_new, "Newer Year")

    if months_filter is not None:
        df_old = df_old[df_old[cols_old["Month"]].isin(months_filter)].copy()
        df_new = df_new[df_new[cols_new["Month"]].isin(months_filter)].copy()

    st.markdown(f"### Global Filters – {context_name}")
    filtered_old, sel_country, sel_customer, sel_category = create_and_apply_filters(
        df_old, cols_old, prefix=f"{prefix}_old"
    )

    def apply_same_filters(df, cols):
        if df is None:
            return None
        d = df.copy()
        if sel_country != "All Countries":
            d = d[d[cols["Country"]] == sel_country]
        if sel_customer != "All Customers":
            d = d[d[cols["Customer"]] == sel_customer]
        if sel_category != "All Categories":
            d = d[d["Category Clean"] == sel_category]
        return d

    filtered_new = apply_same_filters(df_new, cols_new)

    if filtered_old is None or filtered_new is None or filtered_old.empty and filtered_new.empty:
        st.info("No data after filters.")
        return

    # ---------- KPI (only once) ----------
    st.subheader(f"💰 KPI – {year_old_label} vs {year_new_label}")
    net_old = decimal_sum(filtered_old[net_old_col])
    net_new = decimal_sum(filtered_new[net_new_col])
    qty_old = decimal_sum(filtered_old[qty_old_col])
    qty_new = decimal_sum(filtered_new[qty_new_col])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Net {year_old_label}", format_number_plain(net_old))
    k2.metric(
        f"Net {year_new_label}",
        format_number_plain(net_new),
        yoy_label(calc_yoy_clean(net_new, net_old))
    )
    k3.metric(f"Qty {year_old_label}", format_number_plain(qty_old))
    k4.metric(
        f"Qty {year_new_label}",
        format_number_plain(qty_new),
        yoy_label(calc_yoy_clean(qty_new, qty_old))
    )

    st.divider()

    # ---------- CATEGORY PERFORMANCE ----------
    st.markdown("## 📂 Category Performance (YoY%)")
    cat_old = filtered_old.groupby("Category Clean").agg({net_old_col: decimal_sum}).reset_index()
    cat_new = filtered_new.groupby("Category Clean").agg({net_new_col: decimal_sum}).reset_index()

    cat = pd.merge(cat_old, cat_new, on="Category Clean", how="outer").fillna(Decimal("0"))
    cat = sort_by_col_desc(cat, net_new_col)

    total_old = decimal_sum(cat[net_old_col])
    total_new = decimal_sum(cat[net_new_col])

    cat[f"Share {year_old_label} %"] = cat[net_old_col].apply(
        lambda x: safe_div(x, total_old) * Decimal("100") if total_old != 0 else Decimal("0")
    )
    cat[f"Share {year_new_label} %"] = cat[net_new_col].apply(
        lambda x: safe_div(x, total_new) * Decimal("100") if total_new != 0 else Decimal("0")
    )

    cat["YoY"] = cat.apply(lambda x: calc_yoy_clean(x[net_new_col], x[net_old_col]), axis=1)
    cat["YoY %"] = cat["YoY"].apply(yoy_label)

    plot_old = cat.copy()
    plot_old[net_old_col] = plot_old[net_old_col].apply(lambda x: float(to_decimal(x)))
    plot_new = cat.copy()
    plot_new[net_new_col] = plot_new[net_new_col].apply(lambda x: float(to_decimal(x)))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### Category Pie – {year_old_label}")
        st.plotly_chart(
            px.pie(plot_old, names="Category Clean", values=net_old_col),
            use_container_width=True,
            key=f"{prefix}_cat_pie_old"
        )
    with c2:
        st.markdown(f"### Category Pie – {year_new_label}")
        st.plotly_chart(
            px.pie(plot_new, names="Category Clean", values=net_new_col),
            use_container_width=True,
            key=f"{prefix}_cat_pie_new"
        )

    cat_disp = cat.copy()
    cat_disp[net_old_col] = cat_disp[net_old_col].apply(format_number_plain)
    cat_disp[net_new_col] = cat_disp[net_new_col].apply(format_number_plain)
    cat_disp[f"Share {year_old_label} %"] = cat_disp[f"Share {year_old_label} %"].apply(
        lambda x: f"{format_number_plain(x)}%"
    )
    cat_disp[f"Share {year_new_label} %"] = cat_disp[f"Share {year_new_label} %"].apply(
        lambda x: f"{format_number_plain(x)}%"
    )

    st.dataframe(add_index(cat_disp[[
        "Category Clean",
        net_old_col, f"Share {year_old_label} %",
        net_new_col, f"Share {year_new_label} %",
        "YoY %"
    ]]))

    st.divider()

    # ---------- BRAND PERFORMANCE ----------
    st.markdown("## 🏷️ Brand Performance (YoY%)")
    brand_old = filtered_old.groupby(brand_old_col).agg({net_old_col: decimal_sum}).reset_index()
    brand_new = filtered_new.groupby(brand_new_col).agg({net_new_col: decimal_sum}).reset_index()

    brand = pd.merge(
        brand_old,
        brand_new,
        left_on=brand_old_col,
        right_on=brand_new_col,
        how="outer"
    ).fillna(Decimal("0"))

    brand["Brand"] = brand[brand_old_col].where(
        brand[brand_old_col] != "",
        brand[brand_new_col]
    )

    brand = brand[["Brand", net_old_col, net_new_col]]
    brand = sort_by_col_desc(brand, net_new_col)

    total_old_b = decimal_sum(brand[net_old_col])
    total_new_b = decimal_sum(brand[net_new_col])

    brand[f"Share {year_old_label} %"] = brand[net_old_col].apply(
        lambda x: safe_div(x, total_old_b) * Decimal("100") if total_old_b != 0 else Decimal("0")
    )
    brand[f"Share {year_new_label} %"] = brand[net_new_col].apply(
        lambda x: safe_div(x, total_new_b) * Decimal("100") if total_new_b != 0 else Decimal("0")
    )

    brand["YoY"] = brand.apply(lambda x: calc_yoy_clean(x[net_new_col], x[net_old_col]), axis=1)
    brand["YoY %"] = brand["YoY"].apply(yoy_label)

    b_old_plot = brand.copy()
    b_old_plot[net_old_col] = b_old_plot[net_old_col].apply(lambda x: float(to_decimal(x)))
    b_new_plot = brand.copy()
    b_new_plot[net_new_col] = b_new_plot[net_new_col].apply(lambda x: float(to_decimal(x)))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### Brand Pie – {year_old_label}")
        st.plotly_chart(
            px.pie(b_old_plot, names="Brand", values=net_old_col),
            use_container_width=True,
            key=f"{prefix}_brand_pie_old"
        )
    with c2:
        st.markdown(f"### Brand Pie – {year_new_label}")
        st.plotly_chart(
            px.pie(b_new_plot, names="Brand", values=net_new_col),
            use_container_width=True,
            key=f"{prefix}_brand_pie_new"
        )

    b_disp = brand.copy()
    b_disp[net_old_col] = b_disp[net_old_col].apply(format_number_plain)
    b_disp[net_new_col] = b_disp[net_new_col].apply(format_number_plain)
    b_disp[f"Share {year_old_label} %"] = b_disp[f"Share {year_old_label} %"].apply(
        lambda x: f"{format_number_plain(x)}%"
    )
    b_disp[f"Share {year_new_label} %"] = b_disp[f"Share {year_new_label} %"].apply(
        lambda x: f"{format_number_plain(x)}%"
    )

    st.dataframe(add_index(b_disp[[
        "Brand",
        net_old_col, f"Share {year_old_label} %",
        net_new_col, f"Share {year_new_label} %",
        "YoY %"
    ]]))

    st.divider()

    # ---------- TOP PRODUCTS ----------
    st.markdown("## 🏆 Top Products")
    base_old = filtered_old.copy()
    base_new = filtered_new.copy()

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"### {year_old_label}")
        d_old = base_old.groupby(code_old_col).agg({
            desc_old_col: "first",
            net_old_col: decimal_sum,
            qty_old_col: decimal_sum
        }).reset_index()
        d_old = d_old[d_old[net_old_col] > 0]
        d_old = sort_by_col_desc(d_old, net_old_col)
        if d_old.empty:
            st.info("No sales.")
        else:
            top_old = d_old.head(10)
            total_old_net = decimal_sum(d_old[net_old_col])
            top_old["Share %"] = top_old[net_old_col].apply(
                lambda x: safe_div(x, total_old_net) * Decimal("100") if total_old_net != 0 else Decimal("0")
            )
            disp = top_old.copy()
            disp[net_old_col] = disp[net_old_col].apply(format_number_plain)
            disp[qty_old_col] = disp[qty_old_col].apply(format_number_plain)
            disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
            st.dataframe(add_index(disp[[code_old_col, desc_old_col, net_old_col, qty_old_col, "Share %"]]))
            share_total = safe_div(decimal_sum(top_old[net_old_col]), total_old_net) * Decimal("100") if total_old_net != 0 else Decimal("0")
            st.write(f"Top 10 share: {format_number_plain(share_total)}%")

    with c2:
        st.write(f"### {year_new_label}")
        d_new = base_new.groupby(code_new_col).agg({
            desc_new_col: "first",
            net_new_col: decimal_sum,
            qty_new_col: decimal_sum
        }).reset_index()
        d_new = d_new[d_new[net_new_col] > 0]
        d_new = sort_by_col_desc(d_new, net_new_col)
        if d_new.empty:
            st.info("No sales.")
        else:
            top_new = d_new.head(10)
            total_new_net = decimal_sum(d_new[net_new_col])
            top_new["Share %"] = top_new[net_new_col].apply(
                lambda x: safe_div(x, total_new_net) * Decimal("100") if total_new_net != 0 else Decimal("0")
            )
            disp = top_new.copy()
            disp[net_new_col] = disp[net_new_col].apply(format_number_plain)
            disp[qty_new_col] = disp[qty_new_col].apply(format_number_plain)
            disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
            st.dataframe(add_index(disp[[code_new_col, desc_new_col, net_new_col, qty_new_col, "Share %"]]))
            share_total = safe_div(decimal_sum(top_new[net_new_col]), total_new_net) * Decimal("100") if total_new_net != 0 else Decimal("0")
            st.write(f"Top 10 share: {format_number_plain(share_total)}%")

    st.divider()

    # ---------- PARETO & ABC (TABS PER YEAR) ----------
    st.markdown("## 📊 Pareto Analysis – by Year")
    pareto_tabs = st.tabs([f"{year_old_label}", f"{year_new_label}"])

    for (df_y, cols_y, year_label, tab) in [
        (filtered_old, cols_old, year_old_label, pareto_tabs[0]),
        (filtered_new, cols_new, year_new_label, pareto_tabs[1]),
    ]:
        with tab:
            net_col = cols_y["Net"]
            code_col = cols_y["Code"]
            desc_col = cols_y["Desc"]
            p = df_y.groupby(code_col).agg({
                desc_col: "first",
                "Category Clean": "first",
                net_col: decimal_sum
            }).reset_index()
            p = p[p[net_col] > 0]
            if p.empty:
                st.info("No sales for Pareto.")
            else:
                p = sort_by_col_desc(p, net_col)
                total_val = decimal_sum(p[net_col])
                if total_val == 0:
                    st.info("Total value is zero.")
                else:
                    p["cum_value"] = p[net_col].cumsum()
                    p["cum_share"] = p["cum_value"].apply(lambda x: safe_div(x, total_val))
                    top80 = p[p["cum_share"] <= Decimal("0.8")]

                    total_sku = p[code_col].nunique()
                    pareto_sku = top80[code_col].nunique()
                    sku_share = safe_div(Decimal(pareto_sku), Decimal(total_sku)) * Decimal("100") if total_sku > 0 else Decimal("0")

                    st.write(
                        f"Top SKU for 80%: {pareto_sku} / {total_sku} "
                        f"({format_number_plain(sku_share)}% of SKU)"
                    )

                    p_disp = top80[[code_col, desc_col, "Category Clean", net_col]].copy()
                    p_disp[net_col] = p_disp[net_col].apply(format_number_plain)
                    st.dataframe(add_index(p_disp))

    st.divider()

    st.markdown("## 📊 ABC Analysis – by Year")
    abc_tabs = st.tabs([f"{year_old_label}", f"{year_new_label}"])

    for (df_y, cols_y, year_label, tab) in [
        (filtered_old, cols_old, year_old_label, abc_tabs[0]),
        (filtered_new, cols_new, year_new_label, abc_tabs[1]),
    ]:
        with tab:
            net_col = cols_y["Net"]
            code_col = cols_y["Code"]
            desc_col = cols_y["Desc"]
            a = df_y.groupby(code_col).agg({
                desc_col: "first",
                net_col: decimal_sum
            }).reset_index()
            a = a[a[net_col] > 0]
            if a.empty:
                st.info("No sales for ABC.")
            else:
                a = sort_by_col_desc(a, net_col).reset_index(drop=True)
                total_val = decimal_sum(a[net_col])
                if total_val == 0:
                    st.info("Total value is zero.")
                else:
                    a["cum"] = a[net_col].cumsum().apply(lambda x: safe_div(x, total_val))
                    a["segment"] = "C"
                    a.loc[a["cum"] <= Decimal("0.7"), "segment"] = "A"
                    a.loc[(a["cum"] > Decimal("0.7")) & (a["cum"] <= Decimal("0.9")), "segment"] = "B"

                    seg_counts = a["segment"].value_counts()
                    st.write(
                        f"A: {seg_counts.get('A', 0)} | "
                        f"B: {seg_counts.get('B', 0)} | "
                        f"C: {seg_counts.get('C', 0)}"
                    )

                    a_disp = a[[code_col, desc_col, net_col, "segment"]].copy()
                    a_disp[net_col] = a_disp[net_col].apply(format_number_plain)
                    st.dataframe(add_index(a_disp))

    st.divider()

    # ---------- L4L TABLE ----------
    st.markdown("## 📈 L4L Table (sorted by newer year)")
    old_agg = filtered_old.groupby(code_old_col).agg({
        desc_old_col: "first",
        net_old_col: decimal_sum,
        qty_old_col: decimal_sum
    }).reset_index().rename(columns={
        code_old_col: "Code",
        desc_old_col: "Description",
        net_old_col: "Net_Old",
        qty_old_col: "Qty_Old"
    })

    new_agg = filtered_new.groupby(code_new_col).agg({
        desc_new_col: "first",
        net_new_col: decimal_sum,
        qty_new_col: decimal_sum
    }).reset_index().rename(columns={
        code_new_col: "Code",
        desc_new_col: "Description",
        net_new_col: "Net_New",
        qty_new_col: "Qty_New"
    })

    l4l = pd.merge(old_agg, new_agg, on=["Code", "Description"], how="outer").fillna(Decimal("0"))

    for col in ["Net_Old", "Net_New", "Qty_Old", "Qty_New"]:
        l4l[col] = l4l[col].apply(to_decimal)

    l4l["YoY"] = l4l.apply(lambda x: calc_yoy_clean(x["Net_New"], x["Net_Old"]), axis=1)
    l4l["YoY %"] = l4l["YoY"].apply(yoy_label)

    l4l = sort_by_col_desc(l4l, "Net_New")

    disp = l4l.copy()
    for col in ["Net_Old", "Net_New", "Qty_Old", "Qty_New"]:
        disp[col] = disp[col].apply(format_number_plain)

    st.dataframe(add_index(disp[[
        "Code", "Description",
        "Net_Old", "Net_New",
        "Qty_Old", "Qty_New",
        "YoY %"
    ]]))

    st.divider()

    # ---------- AUTO INSIGHTS (TOP 5) ----------
    st.markdown("## 🧠 Auto Insights – Top 5 Categories / Growth / Risk")

    # allow choosing which year to base Top 5 on
    year_choice = st.selectbox(
        "Select year for Top 5 insights",
        [year_old_label, year_new_label],
        key=f"{prefix}_top5_year"
    )

    if year_choice == year_old_label:
        df_ins = filtered_old
        net_col_ins = net_old_col
        other_df = filtered_new
        other_net = net_new_col
        base_old_label = year_old_label
        base_new_label = year_new_label
    else:
        df_ins = filtered_new
        net_col_ins = net_new_col
        other_df = filtered_old
        other_net = net_old_col
        base_old_label = year_new_label
        base_new_label = year_old_label

    cat_ins_old = filtered_old.groupby("Category Clean").agg({net_old_col: decimal_sum}).reset_index()
    cat_ins_new = filtered_new.groupby("Category Clean").agg({net_new_col: decimal_sum}).reset_index()
    cat_ins = pd.merge(cat_ins_old, cat_ins_new, on="Category Clean", how="outer").fillna(Decimal("0"))
    cat_ins["YoY"] = cat_ins.apply(lambda x: calc_yoy_clean(x[net_new_col], x[net_old_col]), axis=1)
    cat_ins["YoY %"] = cat_ins["YoY"].apply(yoy_label)

    st.write("### Top 5 Categories")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"#### {year_old_label}")
        top_old_cat = sort_by_col_desc(cat_ins, net_old_col).head(5)
        disp = top_old_cat.copy()
        disp[net_old_col] = disp[net_old_col].apply(format_number_plain)
        st.dataframe(add_index(disp[["Category Clean", net_old_col]]))
    with c2:
        st.write(f"#### {year_new_label}")
        top_new_cat = sort_by_col_desc(cat_ins, net_new_col).head(5)
        disp = top_new_cat.copy()
        disp[net_new_col] = disp[net_new_col].apply(format_number_plain)
        st.dataframe(add_index(disp[["Category Clean", net_new_col, "YoY %"]]))

    st.write("### Top 5 Growth (YoY > 0)")
    growth = cat_ins[cat_ins["YoY"] > 0].copy()
    growth = growth.sort_values("YoY", ascending=False).head(5)
    if growth.empty:
        st.info("There is no growth in categories.")
    else:
        disp = growth.copy()
        disp[net_old_col] = disp[net_old_col].apply(format_number_plain)
        disp[net_new_col] = disp[net_new_col].apply(format_number_plain)
        st.dataframe(add_index(disp[["Category Clean", net_old_col, net_new_col, "YoY %"]]))

    st.write("### Top 5 Risk (YoY < 0)")
    risk = cat_ins[cat_ins["YoY"] < 0].copy()
    risk = risk.sort_values("YoY").head(5)
    if risk.empty:
        st.success("There is no risk in categories.")
    else:
        disp = risk.copy()
        disp[net_old_col] = disp[net_old_col].apply(format_number_plain)
        disp[net_new_col] = disp[net_new_col].apply(format_number_plain)
        st.dataframe(add_index(disp[["Category Clean", net_old_col, net_new_col, "YoY %"]]))

    st.divider()

    # ---------- CUSTOMER IMPACT WITH FILTERS ----------
    customer_impact_with_filters(
        filtered_old, cols_old,
        filtered_new, cols_new,
        prefix=f"{prefix}_impact",
        title_prefix=f"{year_old_label} → {year_new_label}"
    )


# ========================= SINGLE YEAR DASHBOARD (FULL YEAR) =========================
def render_single_year_full(df, cols, prefix: str, context_name: str):
    if df is None or cols is None or df.empty:
        st.info("No data for selected year.")
        return

    net_col = cols["Net"]
    qty_col = cols["Qty"]
    code_col = cols["Code"]
    desc_col = cols["Desc"]
    brand_col = cols["Brand"]

    year_label = get_year_label(df, cols, context_name)

    st.markdown(f"### Global Filters – Full Year {year_label}")
    filtered, _, _, _ = create_and_apply_filters(df, cols, prefix=f"{prefix}_full")
    if filtered is None or filtered.empty:
        st.info("No data after filters.")
        return

    # KPI
    st.subheader(f"💰 KPI – {year_label}")
    total_net = decimal_sum(filtered[net_col])
    total_qty = decimal_sum(filtered[qty_col])

    k1, k2 = st.columns(2)
    k1.metric(f"Net {year_label}", format_number_plain(total_net))
    k2.metric(f"Qty {year_label}", format_number_plain(total_qty))

    st.divider()

    # Category Performance (no YoY)
    st.markdown(f"## 📂 Category Performance – {year_label}")
    cat = filtered.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
    cat = sort_by_col_desc(cat, net_col)
    total_cat = decimal_sum(cat[net_col])
    cat["Share %"] = cat[net_col].apply(
        lambda x: safe_div(x, total_cat) * Decimal("100") if total_cat != 0 else Decimal("0")
    )

    plot_cat = cat.copy()
    plot_cat[net_col] = plot_cat[net_col].apply(lambda x: float(to_decimal(x)))

    st.markdown(f"### Category Pie – {year_label}")
    st.plotly_chart(
        px.pie(plot_cat, names="Category Clean", values=net_col),
        use_container_width=True,
        key=f"{prefix}_full_cat_pie"
    )

    disp = cat.copy()
    disp[net_col] = disp[net_col].apply(format_number_plain)
    disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
    st.dataframe(add_index(disp[["Category Clean", net_col, "Share %"]]))

    st.divider()

    # Brand Performance (no YoY)
    st.markdown(f"## 🏷️ Brand Performance – {year_label}")
    brand = filtered.groupby(brand_col).agg({net_col: decimal_sum}).reset_index()
    brand = sort_by_col_desc(brand, net_col)
    total_brand = decimal_sum(brand[net_col])
    brand["Share %"] = brand[net_col].apply(
        lambda x: safe_div(x, total_brand) * Decimal("100") if total_brand != 0 else Decimal("0")
    )

    plot_brand = brand.copy()
    plot_brand[net_col] = plot_brand[net_col].apply(lambda x: float(to_decimal(x)))

    st.markdown(f"### Brand Pie – {year_label}")
    st.plotly_chart(
        px.pie(plot_brand, names=brand_col, values=net_col),
        use_container_width=True,
        key=f"{prefix}_full_brand_pie"
    )

    disp_b = brand.copy()
    disp_b[net_col] = disp_b[net_col].apply(format_number_plain)
    disp_b["Share %"] = disp_b["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
    st.dataframe(add_index(disp_b[[brand_col, net_col, "Share %"]]))

    st.divider()

    # Top Products
    st.markdown(f"## 🏆 Top Products – {year_label}")
    top = filtered.groupby(code_col).agg({
        desc_col: "first",
        net_col: decimal_sum,
        qty_col: decimal_sum
    }).reset_index()
    top = top[top[net_col] > 0]
    top = sort_by_col_desc(top, net_col)
    if top.empty:
        st.info("No product data.")
    else:
        total_net_all = decimal_sum(top[net_col])
        top10 = top.head(10).copy()
        top10["Share %"] = top10[net_col].apply(
            lambda x: safe_div(x, total_net_all) * Decimal("100") if total_net_all != 0 else Decimal("0")
        )
        disp = top10.copy()
        disp[net_col] = disp[net_col].apply(format_number_plain)
        disp[qty_col] = disp[qty_col].apply(format_number_plain)
        disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
        st.dataframe(add_index(disp[[code_col, desc_col, net_col, qty_col, "Share %"]]))
        share_total = safe_div(decimal_sum(top10[net_col]), total_net_all) * Decimal("100") if total_net_all != 0 else Decimal("0")
        st.write(f"Top 10 share: {format_number_plain(share_total)}%")

    st.divider()

    # Pareto & ABC (single year)
    st.markdown(f"## 📊 Pareto Analysis – {year_label}")
    p = filtered.groupby(code_col).agg({
        desc_col: "first",
        "Category Clean": "first",
        net_col: decimal_sum
    }).reset_index()
    p = p[p[net_col] > 0]
    if p.empty:
        st.info("No sales for Pareto.")
    else:
        p = sort_by_col_desc(p, net_col)
        total_val = decimal_sum(p[net_col])
        if total_val == 0:
            st.info("Total value is zero.")
        else:
            p["cum_value"] = p[net_col].cumsum()
            p["cum_share"] = p["cum_value"].apply(lambda x: safe_div(x, total_val))
            top80 = p[p["cum_share"] <= Decimal("0.8")]

            total_sku = p[code_col].nunique()
            pareto_sku = top80[code_col].nunique()
            sku_share = safe_div(Decimal(pareto_sku), Decimal(total_sku)) * Decimal("100") if total_sku > 0 else Decimal("0")

            st.write(
                f"Top SKU for 80%: {pareto_sku} / {total_sku} "
                f"({format_number_plain(sku_share)}% of SKU)"
            )

            p_disp = top80[[code_col, desc_col, "Category Clean", net_col]].copy()
            p_disp[net_col] = p_disp[net_col].apply(format_number_plain)
            st.dataframe(add_index(p_disp))

    st.divider()

    st.markdown(f"## 📊 ABC Analysis – {year_label}")
    a = filtered.groupby(code_col).agg({
        desc_col: "first",
        net_col: decimal_sum
    }).reset_index()
    a = a[a[net_col] > 0]
    if a.empty:
        st.info("No sales for ABC.")
    else:
        a = sort_by_col_desc(a, net_col).reset_index(drop=True)
        total_val = decimal_sum(a[net_col])
        if total_val == 0:
            st.info("Total value is zero.")
        else:
            a["cum"] = a[net_col].cumsum().apply(lambda x: safe_div(x, total_val))
            a["segment"] = "C"
            a.loc[a["cum"] <= Decimal("0.7"), "segment"] = "A"
            a.loc[(a["cum"] > Decimal("0.7")) & (a["cum"] <= Decimal("0.9")), "segment"] = "B"

            seg_counts = a["segment"].value_counts()
            st.write(
                f"A: {seg_counts.get('A', 0)} | "
                f"B: {seg_counts.get('B', 0)} | "
                f"C: {seg_counts.get('C', 0)}"
            )

            a_disp = a[[code_col, desc_col, net_col, "segment"]].copy()
            a_disp[net_col] = a_disp[net_col].apply(format_number_plain)
            st.dataframe(add_index(a_disp))

    st.divider()

    # Top 5 sections (no YoY)
    st.markdown("## 🧠 Auto Insights – Top 5 Categories / Growth / Risk (single year)")
    cat_ins = filtered.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
    cat_ins = sort_by_col_desc(cat_ins, net_col)

    st.write("### Top 5 Categories")
    top5 = cat_ins.head(5).copy()
    top5[net_col] = top5[net_col].apply(format_number_plain)
    st.dataframe(add_index(top5[["Category Clean", net_col]]))

    # For single year, "growth" and "risk" don't have YoY, so we can show highest and lowest
    st.write("### Top 5 Growth (highest net)")
    growth = cat_ins.head(5).copy()
    growth[net_col] = growth[net_col].apply(format_number_plain)
    st.dataframe(add_index(growth[["Category Clean", net_col]]))

    st.write("### Top 5 Risk (lowest net)")
    risk = cat_ins.sort_values(net_col, ascending=True).head(5).copy()
    risk[net_col] = risk[net_col].apply(format_number_plain)
    st.dataframe(add_index(risk[["Category Clean", net_col]]))

    st.divider()

    # Customer impact (single year – ranking by net)
    st.markdown(f"## 👥 Customer Impact – {year_label}")
    cat_all = sorted(filtered["Category Clean"].dropna().unique())
    brand_all = sorted(filtered[brand_col].dropna().unique())

    sel_cat = st.selectbox(
        "Impact Category",
        ["All Categories"] + cat_all,
        key=f"{prefix}_full_impact_cat"
    )
    sel_brand = st.selectbox(
        "Impact Brand (License)",
        ["All Brands"] + brand_all,
        key=f"{prefix}_full_impact_brand"
    )

    df_imp = filtered.copy()
    if sel_cat != "All Categories":
        df_imp = df_imp[df_imp["Category Clean"] == sel_cat]
    if sel_brand != "All Brands":
        df_imp = df_imp[df_imp[brand_col] == sel_brand]

    cust_col = cols["Customer"]
    impact = df_imp.groupby(cust_col).agg({net_col: decimal_sum}).reset_index()
    impact = sort_by_col_desc(impact, net_col)

    if impact.empty:
        st.info("No customer impact data.")
    else:
        disp = impact.copy()
        disp[net_col] = disp[net_col].apply(format_number_plain)
        st.dataframe(add_index(disp[[cust_col, net_col]]))

    st.divider()


# ========================= 3-YEAR OVERVIEW (L4L) =========================
def render_overview_three_years(df_curr, cols_curr, df_prev, cols_prev, df_old, cols_old):
    st.header("Overview – 3-year Like-for-Like")

    if df_curr is None or cols_curr is None or df_prev is None or cols_prev is None:
        st.info("Please upload at least Current Year and Previous Year files.")
        return

    months_curr = set(df_curr[cols_curr["Month"]].dropna().unique())
    months_prev = set(df_prev[cols_prev["Month"]].dropna().unique())
    common_months = months_curr & months_prev

    if df_old is not None and cols_old is not None:
        months_old = set(df_old[cols_old["Month"]].dropna().unique())
        common_months = common_months & months_old

    common_months = sorted(
        list(common_months),
        key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99
    )

    if not common_months:
        st.warning("No common months across years for Like-for-Like.")
        return

    st.info(f"Detected common months for L4L: {', '.join(common_months)}")

    year_curr_label = get_year_label(df_curr, cols_curr, "Current Year")
    year_prev_label = get_year_label(df_prev, cols_prev, "Previous Year")
    year_old_label = get_year_label(df_old, cols_old, "Two Years Ago") if df_old is not None else "Two Years Ago"

    st.markdown("### Global Filters (applied to all 3 years)")
    df_prev_l4l = df_prev[df_prev[cols_prev["Month"]].isin(common_months)].copy()
    filtered_prev, sel_country, sel_customer, sel_category = create_and_apply_filters(
        df_prev_l4l, cols_prev, prefix="overview_prev"
    )

    def apply_same_filters(df, cols):
        if df is None or cols is None:
            return None
        d = df[df[cols["Month"]].isin(common_months)].copy()
        if sel_country != "All Countries":
            d = d[d[cols["Country"]] == sel_country]
        if sel_customer != "All Customers":
            d = d[d[cols["Customer"]] == sel_customer]
        if sel_category != "All Categories":
            d = d[d["Category Clean"] == sel_category]
        return d

    filtered_old = apply_same_filters(df_old, cols_old)
    filtered_curr = apply_same_filters(df_curr, cols_curr)

    st.markdown("### 3-year Net Sales (L4L) – older on the left, newer on the right")
    net_old = decimal_sum(filtered_old[cols_old["Net"]]) if filtered_old is not None else None
    net_prev = decimal_sum(filtered_prev[cols_prev["Net"]])
    net_curr = decimal_sum(filtered_curr[cols_curr["Net"]])

    c1, c2, c3 = st.columns(3)
    if filtered_old is not None:
        c1.metric(f"Net {year_old_label}", format_number_plain(net_old))
    else:
        c1.write(f"{year_old_label}: no file")

    c2.metric(
        f"Net {year_prev_label}",
        format_number_plain(net_prev),
        yoy_label(calc_yoy_clean(net_prev, net_old)) if filtered_old is not None else None
    )
    c3.metric(
        f"Net {year_curr_label}",
        format_number_plain(net_curr),
        yoy_label(calc_yoy_clean(net_curr, net_prev))
    )

    chart_data = {"Year": [], "Net": []}
    if filtered_old is not None:
        chart_data["Year"].append(year_old_label)
        chart_data["Net"].append(float(net_old))
    chart_data["Year"].append(year_prev_label)
    chart_data["Net"].append(float(net_prev))
    chart_data["Year"].append(year_curr_label)
    chart_data["Net"].append(float(net_curr))

    chart_df = pd.DataFrame(chart_data)
    st.plotly_chart(
        px.bar(chart_df, x="Year", y="Net", text="Net", title="3-year Net Sales (L4L)"),
        use_container_width=True,
        key="overview_bar_3year"
    )

    st.divider()

    # Brand Performance 3-year
    st.markdown("## 🏷️ Brand Performance – 3-year L4L")
    bc1, bc2, bc3 = st.columns(3)

    def brand_perf_block(df, cols, year_label, key_prefix):
        if df is None or cols is None or df.empty:
            st.info(f"No data for {year_label}")
            return
        net_col = cols["Net"]
        brand_col = cols["Brand"]
        b = df.groupby(brand_col).agg({net_col: decimal_sum}).reset_index()
        b = sort_by_col_desc(b, net_col)
        total = decimal_sum(b[net_col])
        b["Share %"] = b[net_col].apply(
            lambda x: safe_div(x, total) * Decimal("100") if total != 0 else Decimal("0")
        )
        plot_df = b.copy()
        plot_df[net_col] = plot_df[net_col].apply(lambda x: float(to_decimal(x)))
        st.markdown(f"### Brand Pie – {year_label}")
        st.plotly_chart(
            px.pie(plot_df, names=brand_col, values=net_col),
            use_container_width=True,
            key=f"{key_prefix}_brand_pie"
        )
        disp = b.copy()
        disp[net_col] = disp[net_col].apply(format_number_plain)
        disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
        st.dataframe(add_index(disp[[brand_col, net_col, "Share %"]]))

    with bc1:
        brand_perf_block(filtered_old, cols_old, year_old_label, "overview_old") if filtered_old is not None else st.info(
            f"No data for {year_old_label}"
        )
    with bc2:
        brand_perf_block(filtered_prev, cols_prev, year_prev_label, "overview_prev")
    with bc3:
        brand_perf_block(filtered_curr, cols_curr, year_curr_label, "overview_curr")

    st.divider()

    # Category Performance 3-year
    st.markdown("## 📂 Category Performance – 3-year L4L")
    cc1, cc2, cc3 = st.columns(3)

    def cat_perf_block(df, cols, year_label, key_prefix):
        if df is None or cols is None or df.empty:
            st.info(f"No data for {year_label}")
            return
        net_col = cols["Net"]
        c = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
        c = sort_by_col_desc(c, net_col)
        total = decimal_sum(c[net_col])
        c["Share %"] = c[net_col].apply(
            lambda x: safe_div(x, total) * Decimal("100") if total != 0 else Decimal("0")
        )
        plot_df = c.copy()
        plot_df[net_col] = plot_df[net_col].apply(lambda x: float(to_decimal(x)))
        st.markdown(f"### Category Pie – {year_label}")
        st.plotly_chart(
            px.pie(plot_df, names="Category Clean", values=net_col),
            use_container_width=True,
            key=f"{key_prefix}_cat_pie"
        )
        disp = c.copy()
        disp[net_col] = disp[net_col].apply(format_number_plain)
        disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
        st.dataframe(add_index(disp[["Category Clean", net_col, "Share %"]]))

    with cc1:
        cat_perf_block(filtered_old, cols_old, year_old_label, "overview_old") if filtered_old is not None else st.info(
            f"No data for {year_old_label}"
        )
    with cc2:
        cat_perf_block(filtered_prev, cols_prev, year_prev_label, "overview_prev")
    with cc3:
        cat_perf_block(filtered_curr, cols_curr, year_curr_label, "overview_curr")

    st.divider()

    # L4L table 3-year (sorted by newest)
    st.markdown("## 📈 L4L Table – 3-year (sorted by newest year)")
    net_curr_col = cols_curr["Net"]
    qty_curr_col = cols_curr["Qty"]
    code_curr = cols_curr["Code"]
    desc_curr = cols_curr["Desc"]

    net_prev_col = cols_prev["Net"]
    qty_prev_col = cols_prev["Qty"]
    code_prev = cols_prev["Code"]
    desc_prev = cols_prev["Desc"]

    curr_agg = filtered_curr.groupby(code_curr).agg({
        desc_curr: "first",
        net_curr_col: decimal_sum,
        qty_curr_col: decimal_sum
    }).reset_index().rename(columns={
        code_curr: "Code",
        desc_curr: "Description",
        net_curr_col: "Net_Current",
        qty_curr_col: "Qty_Current"
    })

    prev_agg = filtered_prev.groupby(code_prev).agg({
        desc_prev: "first",
        net_prev_col: decimal_sum,
        qty_prev_col: decimal_sum
    }).reset_index().rename(columns={
        code_prev: "Code",
        desc_prev: "Description",
        net_prev_col: "Net_Previous",
        qty_prev_col: "Qty_Previous"
    })

    if filtered_old is not None and cols_old is not None:
        net_old_col = cols_old["Net"]
        qty_old_col = cols_old["Qty"]
        code_old = cols_old["Code"]
        desc_old = cols_old["Desc"]

        old_agg = filtered_old.groupby(code_old).agg({
            desc_old: "first",
            net_old_col: decimal_sum,
            qty_old_col: decimal_sum
        }).reset_index().rename(columns={
            code_old: "Code",
            desc_old: "Description",
            net_old_col: "Net_Old",
            qty_old_col: "Qty_Old"
        })
    else:
        old_agg = None

    l4l = pd.merge(prev_agg, curr_agg, on=["Code", "Description"], how="outer")
    if old_agg is not None:
        l4l = pd.merge(old_agg, l4l, on=["Code", "Description"], how="outer")

    for col in ["Net_Current", "Net_Previous", "Net_Old", "Qty_Current", "Qty_Previous", "Qty_Old"]:
        if col in l4l.columns:
            l4l[col] = l4l[col].apply(to_decimal).fillna(Decimal("0"))

    l4l["YoY Prev→Curr"] = l4l.apply(
        lambda x: calc_yoy_clean(x.get("Net_Current", Decimal("0")), x.get("Net_Previous", Decimal("0"))),
        axis=1
    )
    l4l["YoY Prev→Curr %"] = l4l["YoY Prev→Curr"].apply(yoy_label)

    if "Net_Old" in l4l.columns:
        l4l["YoY Old→Prev"] = l4l.apply(
            lambda x: calc_yoy_clean(x.get("Net_Previous", Decimal("0")), x.get("Net_Old", Decimal("0"))),
            axis=1
        )
        l4l["YoY Old→Prev %"] = l4l["YoY Old→Prev"].apply(yoy_label)

    l4l = sort_by_col_desc(l4l, "Net_Current")

    disp = l4l.copy()
    for col in ["Net_Current", "Net_Previous", "Net_Old", "Qty_Current", "Qty_Previous", "Qty_Old"]:
        if col in disp.columns:
            disp[col] = disp[col].apply(format_number_plain)

    cols_to_show = ["Code", "Description",
                    "Net_Old", "Net_Previous", "Net_Current",
                    "Qty_Old", "Qty_Previous", "Qty_Current",
                    "YoY Old→Prev %", "YoY Prev→Curr %"]
    cols_to_show = [c for c in cols_to_show if c in disp.columns]

    st.dataframe(add_index(disp[cols_to_show]))

    st.divider()

    # Pareto & ABC tabs per year
    st.markdown("## 📊 Pareto Analysis – by Year")
    year_dfs = []
    if filtered_old is not None:
        year_dfs.append((year_old_label, filtered_old, cols_old))
    year_dfs.append((year_prev_label, filtered_prev, cols_prev))
    year_dfs.append((year_curr_label, filtered_curr, cols_curr))

    pareto_tabs = st.tabs([y for y, _, _ in year_dfs])
    for (year_label, df_y, cols_y), tab in zip(year_dfs, pareto_tabs):
        with tab:
            net_col = cols_y["Net"]
            code_col = cols_y["Code"]
            desc_col = cols_y["Desc"]
            p = df_y.groupby(code_col).agg({
                desc_col: "first",
                "Category Clean": "first",
                net_col: decimal_sum
            }).reset_index()
            p = p[p[net_col] > 0]
            if p.empty:
                st.info("No sales for Pareto.")
            else:
                p = sort_by_col_desc(p, net_col)
                total_val = decimal_sum(p[net_col])
                if total_val == 0:
                    st.info("Total value is zero.")
                else:
                    p["cum_value"] = p[net_col].cumsum()
                    p["cum_share"] = p["cum_value"].apply(lambda x: safe_div(x, total_val))
                    top80 = p[p["cum_share"] <= Decimal("0.8")]

                    total_sku = p[code_col].nunique()
                    pareto_sku = top80[code_col].nunique()
                    sku_share = safe_div(Decimal(pareto_sku), Decimal(total_sku)) * Decimal("100") if total_sku > 0 else Decimal("0")

                    st.write(
                        f"Top SKU for 80%: {pareto_sku} / {total_sku} "
                        f"({format_number_plain(sku_share)}% of SKU)"
                    )

                    p_disp = top80[[code_col, desc_col, "Category Clean", net_col]].copy()
                    p_disp[net_col] = p_disp[net_col].apply(format_number_plain)
                    st.dataframe(add_index(p_disp))

    st.divider()

    st.markdown("## 📊 ABC Analysis – by Year")
    abc_tabs = st.tabs([y for y, _, _ in year_dfs])
    for (year_label, df_y, cols_y), tab in zip(year_dfs, abc_tabs):
        with tab:
            net_col = cols_y["Net"]
            code_col = cols_y["Code"]
            desc_col = cols_y["Desc"]
            a = df_y.groupby(code_col).agg({
                desc_col: "first",
                net_col: decimal_sum
            }).reset_index()
            a = a[a[net_col] > 0]
            if a.empty:
                st.info("No sales for ABC.")
            else:
                a = sort_by_col_desc(a, net_col).reset_index(drop=True)
                total_val = decimal_sum(a[net_col])
                if total_val == 0:
                    st.info("Total value is zero.")
                else:
                    a["cum"] = a[net_col].cumsum().apply(lambda x: safe_div(x, total_val))
                    a["segment"] = "C"
                    a.loc[a["cum"] <= Decimal("0.7"), "segment"] = "A"
                    a.loc[(a["cum"] > Decimal("0.7")) & (a["cum"] <= Decimal("0.9")), "segment"] = "B"

                    seg_counts = a["segment"].value_counts()
                    st.write(
                        f"A: {seg_counts.get('A', 0)} | "
                        f"B: {seg_counts.get('B', 0)} | "
                        f"C: {seg_counts.get('C', 0)}"
                    )

                    a_disp = a[[code_col, desc_col, net_col, "segment"]].copy()
                    a_disp[net_col] = a_disp[net_col].apply(format_number_plain)
                    st.dataframe(add_index(a_disp))

    st.divider()

    # Top 5 sections with year dropdown
    st.markdown("## 🧠 Auto Insights – Top 5 Categories / Growth / Risk (3-year)")
    year_choice = st.selectbox(
        "Select year for Top 5 insights",
        [y for y, _, _ in year_dfs],
        key="overview_top5_year"
    )

    df_choice = None
    cols_choice = None
    if year_choice == year_old_label and filtered_old is not None:
        df_choice, cols_choice = filtered_old, cols_old
    elif year_choice == year_prev_label:
        df_choice, cols_choice = filtered_prev, cols_prev
    else:
        df_choice, cols_choice = filtered_curr, cols_curr

    if df_choice is not None and cols_choice is not None:
        net_col = cols_choice["Net"]
        cat_ins = df_choice.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
        cat_ins = sort_by_col_desc(cat_ins, net_col)

        st.write("### Top 5 Categories")
        top5 = cat_ins.head(5).copy()
        top5[net_col] = top5[net_col].apply(format_number_plain)
        st.dataframe(add_index(top5[["Category Clean", net_col]]))

        st.write("### Top 5 Growth (highest net)")
        growth = cat_ins.head(5).copy()
        growth[net_col] = growth[net_col].apply(format_number_plain)
        st.dataframe(add_index(growth[["Category Clean", net_col]]))

        st.write("### Top 5 Risk (lowest net)")
        risk = cat_ins.sort_values(net_col, ascending=True).head(5).copy()
        risk[net_col] = risk[net_col].apply(format_number_plain)
        st.dataframe(add_index(risk[["Category Clean", net_col]]))

    st.divider()


# ========================= MAIN APP =========================
st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard – 3-year L4L & Full Year")

st.sidebar.header("📂 Data Import")
file_curr = st.sidebar.file_uploader("Upload Current Year (YTD)", type="xlsx", key="file_curr")
file_prev = st.sidebar.file_uploader("Upload Previous Year (Full)", type="xlsx", key="file_prev")
file_old = st.sidebar.file_uploader("Upload Two Years Ago (Full)", type="xlsx", key="file_old")

df_curr, cols_curr = load_and_prep_data(file_curr, "Current Year") if file_curr else (None, None)
df_prev, cols_prev = load_and_prep_data(file_prev, "Previous Year") if file_prev else (None, None)
df_old, cols_old = load_and_prep_data(file_old, "Two Years Ago") if file_old else (None, None)

tab_main_overview, tab_main_l4l, tab_main_full = st.tabs([
    "📈 Overview – 3-year L4L",
    "📅 Detailed Like-for-Like",
    "📊 Full Year Analysis"
])

# ---------- TAB 1: OVERVIEW 3-YEAR ----------
with tab_main_overview:
    render_overview_three_years(df_curr, cols_curr, df_prev, cols_prev, df_old, cols_old)

# ---------- TAB 2: DETAILED L4L ----------
with tab_main_l4l:
    st.header("Detailed Like-for-Like (2-year, flexible months)")
    if df_curr is None or cols_curr is None or df_prev is None or cols_prev is None:
        st.info("Please upload at least Current Year and Previous Year files.")
    else:
        year_options = []
        year_map = {}

        yc = get_year_label(df_curr, cols_curr, "Current Year")
        yp = get_year_label(df_prev, cols_prev, "Previous Year")
        year_options.append(f"{yc} (Current Year)")
        year_map[f"{yc} (Current Year)"] = ("curr", df_curr, cols_curr)
        year_options.append(f"{yp} (Previous Year)")
        year_map[f"{yp} (Previous Year)"] = ("prev", df_prev, cols_prev)
        if df_old is not None and cols_old is not None:
            yo = get_year_label(df_old, cols_old, "Two Years Ago")
            year_options.append(f"{yo} (Two Years Ago)")
            year_map[f"{yo} (Two Years Ago)"] = ("old", df_old, cols_old)

        st.markdown("### Select years (older on the left, newer on the right)")
        col_y1, col_y2 = st.columns(2)
        with col_y1:
            older_choice = st.selectbox("Older Year", year_options, key="l4l_older")
        with col_y2:
            newer_choice = st.selectbox("Newer Year", year_options, index=0 if len(year_options) == 1 else 1, key="l4l_newer")

        if older_choice == newer_choice:
            st.warning("Older and newer year must be different.")
        else:
            _, df_older, cols_older = year_map[older_choice]
            _, df_newer, cols_newer = year_map[newer_choice]

            months_older = set(df_older[cols_older["Month"]].dropna().unique())
            months_newer = set(df_newer[cols_newer["Month"]].dropna().unique())
            common_months = sorted(
                list(months_older & months_newer),
                key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99
            )

            st.markdown("### Select months for L4L")
            selected_months = st.multiselect(
                "Months",
                MONTHS_ORDER,
                default=common_months,
                key="l4l_months"
            )

            if not selected_months:
                st.info("Select at least one month.")
            else:
                # validate that selected months are within newer year months
                newer_months_available = set(df_newer[cols_newer["Month"]].dropna().unique())
                if not set(selected_months).issubset(newer_months_available):
                    st.error(
                        "Selected month range exceeds available months in the newer year "
                        "(Current Year file). Adjust selection."
                    )
                else:
                    render_two_year_dashboard(
                        df_older, cols_older,
                        df_newer, cols_newer,
                        prefix="detailed_l4l",
                        context_name=f"{older_choice} vs {newer_choice}",
                        months_filter=selected_months
                    )

# ---------- TAB 3: FULL YEAR ----------
with tab_main_full:
    st.header("Full Year Analysis (Previous / Two Years Ago / Current if full)")
    year_full_options = []
    year_full_map = {}

    if df_prev is not None and cols_prev is not None:
        yp = get_year_label(df_prev, cols_prev, "Previous Year")
        year_full_options.append(f"{yp} (Previous Year)")
        year_full_map[f"{yp} (Previous Year)"] = (df_prev, cols_prev)

    if df_old is not None and cols_old is not None:
        yo = get_year_label(df_old, cols_old, "Two Years Ago")
        year_full_options.append(f"{yo} (Two Years Ago)")
        year_full_map[f"{yo} (Two Years Ago)"] = (df_old, cols_old)

    if df_curr is not None and cols_curr is not None:
        yc = get_year_label(df_curr, cols_curr, "Current Year")
        year_full_options.append(f"{yc} (Current Year)")
        year_full_map[f"{yc} (Current Year)"] = (df_curr, cols_curr)

    if not year_full_options:
        st.info("Please upload at least one file to run Full Year Analysis.")
    else:
        selected_full = st.selectbox(
            "Select year for Full Year Analysis",
            year_full_options,
            key="full_year_select"
        )
        df_selected, cols_selected = year_full_map[selected_full]
        render_single_year_full(df_selected, cols_selected, prefix="full_year", context_name=selected_full)
