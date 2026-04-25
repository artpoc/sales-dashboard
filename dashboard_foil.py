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


def get_year_label(df, cols, fallback: str) -> str:
    year_col_name = cols.get("Year")
    if year_col_name and year_col_name in df.columns:
        vals = [v for v in df[year_col_name].unique().tolist() if str(v).strip() != ""]
        if len(vals) == 1:
            return str(vals[0])
    return fallback


# ========================= PER-YEAR DASHBOARD =========================
def render_single_year_dashboard(df, cols, context_name: str, unique_prefix: str):
    if df is None or cols is None or df.empty:
        st.info(f"No data for {context_name}")
        return

    net_col = cols["Net"]
    qty_col = cols["Qty"]
    code_col = cols["Code"]
    desc_col = cols["Desc"]
    brand_col = cols["Brand"]

    year_label = get_year_label(df, cols, context_name)

    # ---------- KPI ----------
    st.subheader(f"💰 KPI – {year_label}")
    total_net = decimal_sum(df[net_col])
    total_qty = decimal_sum(df[qty_col])

    k1, k2 = st.columns(2)
    k1.metric(f"Net Sales {year_label}", format_number_plain(total_net))
    k2.metric(f"Quantity {year_label}", format_number_plain(total_qty))

    st.divider()

    # ---------- CATEGORY PERFORMANCE ----------
    st.markdown(f"## 📂 Category Performance – {year_label}")
    cat = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
    cat = sort_by_col_desc(cat, net_col)

    if cat.empty:
        st.info("No category data.")
    else:
        total_cat_net = decimal_sum(cat[net_col])
        cat["Share %"] = cat[net_col].apply(
            lambda x: safe_div(x, total_cat_net) * Decimal("100") if total_cat_net != 0 else Decimal("0")
        )

        plot_df = cat.copy()
        plot_df[net_col] = plot_df[net_col].apply(lambda x: float(to_decimal(x)))

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                px.pie(plot_df, names="Category Clean", values=net_col),
                use_container_width=True,
                key=f"{unique_prefix}_cat_pie"
            )
        with c2:
            disp = cat.copy()
            disp[net_col] = disp[net_col].apply(format_number_plain)
            disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
            st.dataframe(add_index(disp[["Category Clean", net_col, "Share %"]]))

    st.divider()

    # ---------- BRAND PERFORMANCE ----------
    st.markdown(f"## 🏷️ Brand Performance – {year_label}")
    brand = df.groupby(brand_col).agg({net_col: decimal_sum}).reset_index()
    brand = sort_by_col_desc(brand, net_col)

    if brand.empty:
        st.info("No brand data.")
    else:
        total_brand_net = decimal_sum(brand[net_col])
        brand["Share %"] = brand[net_col].apply(
            lambda x: safe_div(x, total_brand_net) * Decimal("100") if total_brand_net != 0 else Decimal("0")
        )

        b_plot = brand.copy()
        b_plot[net_col] = b_plot[net_col].apply(lambda x: float(to_decimal(x)))

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                px.pie(b_plot, names=brand_col, values=net_col),
                use_container_width=True,
                key=f"{unique_prefix}_brand_pie"
            )
        with c2:
            b_disp = brand.copy()
            b_disp[net_col] = b_disp[net_col].apply(format_number_plain)
            b_disp["Share %"] = b_disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
            st.dataframe(add_index(b_disp[[brand_col, net_col, "Share %"]]))

    st.divider()

    # ---------- TOP PRODUCTS ----------
    st.markdown(f"## 🏆 Top Products – {year_label}")
    top = df.groupby(code_col).agg({
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

    # ---------- PARETO ----------
    st.markdown(f"## 📊 Pareto Analysis – {year_label}")
    p = df.groupby(code_col).agg({
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

    # ---------- ABC ----------
    st.markdown(f"## 📊 ABC Analysis – {year_label}")
    a = df.groupby(code_col).agg({
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


# ========================= 3-YEAR L4L OVERVIEW =========================
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
    with st.container():
        filtered_curr, sel_country, sel_customer, sel_category = create_and_apply_filters(
            df_curr[df_curr[cols_curr["Month"]].isin(common_months)],
            cols_curr,
            prefix="overview_curr"
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

        filtered_prev = apply_same_filters(df_prev, cols_prev)
        filtered_old = apply_same_filters(df_old, cols_old) if df_old is not None else None

    st.markdown("### 3-year Net Sales (L4L)")
    net_curr = decimal_sum(filtered_curr[cols_curr["Net"]])
    net_prev = decimal_sum(filtered_prev[cols_prev["Net"]])
    net_old = decimal_sum(filtered_old[cols_old["Net"]]) if filtered_old is not None else None

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Net {year_curr_label}", format_number_plain(net_curr))
    c2.metric(f"Net {year_prev_label}", format_number_plain(net_prev),
              yoy_label(calc_yoy_clean(net_curr, net_prev)))
    if filtered_old is not None:
        c3.metric(f"Net {year_old_label}", format_number_plain(net_old),
                  yoy_label(calc_yoy_clean(net_prev, net_old)))
    else:
        c3.write(f"{year_old_label}: no file")

    chart_data = {
        "Year": [year_curr_label, year_prev_label],
        "Net": [float(net_curr), float(net_prev)]
    }
    if filtered_old is not None:
        chart_data["Year"].append(year_old_label)
        chart_data["Net"].append(float(net_old))

    chart_df = pd.DataFrame(chart_data)
    st.plotly_chart(
        px.bar(chart_df, x="Year", y="Net", text="Net", title="3-year Net Sales (L4L)"),
        use_container_width=True,
        key="overview_bar_3year"
    )

    st.divider()

    st.markdown("## 🏷️ Brand Performance – 3-year L4L")

    def brand_perf_block(df, cols, title, key_prefix):
        if df is None or cols is None or df.empty:
            st.info(f"No data for {title}")
            return None
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
        st.markdown(f"#### {title}")
        st.plotly_chart(
            px.pie(plot_df, names=brand_col, values=net_col),
            use_container_width=True,
            key=f"{key_prefix}_brand_pie"
        )
        disp = b.copy()
        disp[net_col] = disp[net_col].apply(format_number_plain)
        disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
        st.dataframe(add_index(disp[[brand_col, net_col, "Share %"]]))
        return b

    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        brand_perf_block(filtered_curr, cols_curr, year_curr_label, "overview_curr")
    with bc2:
        brand_perf_block(filtered_prev, cols_prev, year_prev_label, "overview_prev")
    with bc3:
        brand_perf_block(filtered_old, cols_old, year_old_label, "overview_old")

    st.divider()

    st.markdown("## 📂 Category Performance – 3-year L4L")

    def cat_perf_block(df, cols, title, key_prefix):
        if df is None or cols is None or df.empty:
            st.info(f"No data for {title}")
            return None
        net_col = cols["Net"]
        c = df.groupby("Category Clean").agg({net_col: decimal_sum}).reset_index()
        c = sort_by_col_desc(c, net_col)
        total = decimal_sum(c[net_col])
        c["Share %"] = c[net_col].apply(
            lambda x: safe_div(x, total) * Decimal("100") if total != 0 else Decimal("0")
        )
        plot_df = c.copy()
        plot_df[net_col] = plot_df[net_col].apply(lambda x: float(to_decimal(x)))
        st.markdown(f"#### {title}")
        st.plotly_chart(
            px.pie(plot_df, names="Category Clean", values=net_col),
            use_container_width=True,
            key=f"{key_prefix}_cat_pie"
        )
        disp = c.copy()
        disp[net_col] = disp[net_col].apply(format_number_plain)
        disp["Share %"] = disp["Share %"].apply(lambda x: f"{format_number_plain(x)}%")
        st.dataframe(add_index(disp[["Category Clean", net_col, "Share %"]]))
        return c

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        cat_perf_block(filtered_curr, cols_curr, year_curr_label, "overview_curr")
    with cc2:
        cat_perf_block(filtered_prev, cols_prev, year_prev_label, "overview_prev")
    with cc3:
        cat_perf_block(filtered_old, cols_old, year_old_label, "overview_old")

    st.divider()

    st.markdown("## 📈 L4L Table – 3-year (SKU level)")

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

    l4l = pd.merge(curr_agg, prev_agg, on=["Code", "Description"], how="outer")
    if old_agg is not None:
        l4l = pd.merge(l4l, old_agg, on=["Code", "Description"], how="outer")

    for col in ["Net_Current", "Net_Previous", "Net_Old", "Qty_Current", "Qty_Previous", "Qty_Old"]:
        if col in l4l.columns:
            l4l[col] = l4l[col].apply(to_decimal).fillna(Decimal("0"))

    l4l["YoY_Current_vs_Previous"] = l4l.apply(
        lambda x: calc_yoy_clean(x.get("Net_Current", Decimal("0")), x.get("Net_Previous", Decimal("0"))),
        axis=1
    )
    if "Net_Old" in l4l.columns:
        l4l["YoY_Previous_vs_Old"] = l4l.apply(
            lambda x: calc_yoy_clean(x.get("Net_Previous", Decimal("0")), x.get("Net_Old", Decimal("0"))),
            axis=1
        )
    else:
        l4l["YoY_Previous_vs_Old"] = None

    l4l["YoY C vs P"] = l4l["YoY_Current_vs_Previous"].apply(yoy_label)
    l4l["YoY P vs O"] = l4l["YoY_Previous_vs_Old"].apply(yoy_label)

    # sort by newer year (current)
    l4l = sort_by_col_desc(l4l, "Net_Current")

    disp = l4l.copy()
    for col in ["Net_Current", "Net_Previous", "Net_Old", "Qty_Current", "Qty_Previous", "Qty_Old"]:
        if col in disp.columns:
            disp[col] = disp[col].apply(format_number_plain)

    cols_to_show = ["Code", "Description",
                    "Net_Current", "Net_Previous", "Net_Old",
                    "Qty_Current", "Qty_Previous", "Qty_Old",
                    "YoY C vs P", "YoY P vs O"]
    cols_to_show = [c for c in cols_to_show if c in disp.columns]

    st.dataframe(add_index(disp[cols_to_show]))


# ========================= MAIN APP =========================
st.set_page_config(page_title="Sales Intelligence Dashboard", layout="wide")
st.title("📊 Sales Intelligence Dashboard – 3-year, L4L & Full Year")

st.sidebar.header("📂 Data Import")
file_curr = st.sidebar.file_uploader("Current Year (YTD)", type=["xlsx"], key="curr")
file_prev = st.sidebar.file_uploader("Previous Year (Full)", type=["xlsx"], key="prev")
file_old = st.sidebar.file_uploader("Two Years Ago (Full)", type=["xlsx"], key="old")

df_curr, cols_curr = load_and_prep_data(file_curr, "Current Year")
df_prev, cols_prev = load_and_prep_data(file_prev, "Previous Year")
df_old, cols_old = load_and_prep_data(file_old, "Two Years Ago")

if df_curr is None and df_prev is None and df_old is None:
    st.info("Upload at least one Excel file to start.")
    st.stop()

tab_overview, tab_l4l, tab_full = st.tabs([
    "📈 Overview – 3-year Like-for-Like",
    "📅 Detailed Like-for-Like",
    "📊 Full Year Analysis"
])

# ---------- TAB 1: OVERVIEW 3-YEAR L4L ----------
with tab_overview:
    render_overview_three_years(df_curr, cols_curr, df_prev, cols_prev, df_old, cols_old)

# ---------- TAB 2: DETAILED L4L (2 YEARS, MONTH RANGE) ----------
with tab_l4l:
    st.header("Detailed Like-for-Like (2-year comparison)")

    year_options = []
    if df_curr is not None: year_options.append("Current Year")
    if df_prev is not None: year_options.append("Previous Year")
    if df_old is not None: year_options.append("Two Years Ago")

    if len(year_options) < 2:
        st.info("Upload at least two files to run detailed L4L.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            left_year = st.selectbox("Left Year (newer)", year_options, key="l4l_left_year")
        with c2:
            right_year = st.selectbox("Right Year (older)", [y for y in year_options if y != left_year], key="l4l_right_year")

        def pick_df_and_cols(label):
            if label == "Current Year":
                return df_curr, cols_curr, get_year_label(df_curr, cols_curr, "Current Year")
            if label == "Previous Year":
                return df_prev, cols_prev, get_year_label(df_prev, cols_prev, "Previous Year")
            if label == "Two Years Ago":
                return df_old, cols_old, get_year_label(df_old, cols_old, "Two Years Ago")
            return None, None, label

        df_left, cols_left, left_name = pick_df_and_cols(left_year)
        df_right, cols_right, right_name = pick_df_and_cols(right_year)

        if df_left is None or df_right is None:
            st.warning("Selected years are not available.")
        else:
            months_left = set(df_left[cols_left["Month"]].dropna().unique())
            months_right = set(df_right[cols_right["Month"]].dropna().unique())
            common_months_lr = months_left & months_right
            common_months_lr = sorted(
                list(common_months_lr),
                key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99
            )

            if not common_months_lr:
                st.warning("No common months between selected years.")
            else:
                st.info(f"Common months for L4L: {', '.join(common_months_lr)}")

                selected_months = st.multiselect(
                    "Select months for L4L",
                    common_months_lr,
                    default=common_months_lr,
                    key="l4l_months"
                )

                if not selected_months:
                    st.info("Select at least one month.")
                else:
                    df_left_m = df_left[df_left[cols_left["Month"]].isin(selected_months)].copy()
                    df_right_m = df_right[df_right[cols_right["Month"]].isin(selected_months)].copy()

                    st.markdown("### Global Filters for this L4L view")
                    filtered_left, sel_country_l, sel_customer_l, sel_category_l = create_and_apply_filters(
                        df_left_m, cols_left, prefix="l4l_left"
                    )

                    def apply_same_filters_lr(df, cols):
                        if df is None or cols is None:
                            return None
                        d = df[df[cols["Month"]].isin(selected_months)].copy()
                        if sel_country_l != "All Countries":
                            d = d[d[cols["Country"]] == sel_country_l]
                        if sel_customer_l != "All Customers":
                            d = d[d[cols["Customer"]] == sel_customer_l]
                        if sel_category_l != "All Categories":
                            d = d[d["Category Clean"] == sel_category_l]
                        return d

                    filtered_right = apply_same_filters_lr(df_right, cols_right)

                    st.markdown("### Side-by-side dashboards")
                    dcol1, dcol2 = st.columns(2)
                    with dcol1:
                        render_single_year_dashboard(filtered_left, cols_left, left_name, unique_prefix="l4l_left_dash")
                    with dcol2:
                        render_single_year_dashboard(filtered_right, cols_right, right_name, unique_prefix="l4l_right_dash")

# ---------- TAB 3: FULL YEAR ANALYSIS ----------
with tab_full:
    st.header("Full Year Analysis")

    year_options_full = []
    if df_prev is not None: year_options_full.append("Previous Year")
    if df_old is not None: year_options_full.append("Two Years Ago")

    if not year_options_full:
        st.info("Upload at least one full-year file (Previous or Two Years Ago).")
    else:
        selected_full = st.selectbox("Select year for full-year analysis", year_options_full, key="full_year_select")

        def pick_df_cols_full(label):
            if label == "Previous Year":
                return df_prev, cols_prev, get_year_label(df_prev, cols_prev, "Previous Year")
            if label == "Two Years Ago":
                return df_old, cols_old, get_year_label(df_old, cols_old, "Two Years Ago")
            return None, None, label

        df_selected, cols_selected, context_name = pick_df_cols_full(selected_full)

        if df_selected is None or cols_selected is None:
            st.warning("Selected year not available.")
        else:
            st.markdown("### Global Filters for Full Year")
            filtered_selected, _, _, _ = create_and_apply_filters(df_selected, cols_selected, prefix="full")
            render_single_year_dashboard(filtered_selected, cols_selected, context_name, unique_prefix="full_dash")
