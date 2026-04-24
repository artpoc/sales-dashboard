import streamlit as st
import pandas as pd
import plotly.express as px
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# ================= CONFIG =================
DISPLAY_DECIMALS = 0  # change to 1 if you want one decimal place (e.g., 232322.4)

MONTHS_ORDER = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
]

# ================= HELPERS & FUNCTIONS =================
def add_index(df):
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    return df

def to_decimal(x):
    if pd.isna(x): return Decimal('0')
    if isinstance(x, Decimal): return x
    try:
        if isinstance(x, int): return Decimal(x)
        if isinstance(x, float): return Decimal(str(x))
        s = str(x).strip().replace(" ", "").replace(",", ".")
        if s == "": return Decimal('0')
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
        if old < 0 and new == 0: return None
        if old == 0: return Decimal('100') if new > 0 else Decimal('0')
        if old > 0 and new == 0: return Decimal('-100')
        return (new - old) / (abs(old)) * Decimal('100')
    except Exception:
        return None

def yoy_label(val, special=False):
    if special: return "Recovery to 0 ⚠️"
    if val is None: return "0%"
    try: v = float(val)
    except: return "0%"
    if v > 0: return f"+{v:.0f}% 🟢"
    elif v < 0: return f"{v:.0f}% 🔴"
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

def format_number_plain(d, decimals=DISPLAY_DECIMALS):
    if not isinstance(d, Decimal):
        try: d = Decimal(str(d))
        except: d = Decimal('0')
    if decimals == 0:
        q = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return f"{int(q)}"
    else:
        q = d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        return f"{q:.1f}"

def sort_by_col_desc(df, col):
    if col in df.columns:
        try: return df.sort_values(by=col, ascending=False)
        except Exception:
            tmp = df.copy()
            tmp[col] = tmp[col].apply(lambda x: float(x) if isinstance(x, Decimal) else float(Decimal(str(x))))
            return tmp.sort_values(by=col, ascending=False)
    return df

# ================= DATA LOADER =================
def load_and_prep_data(file):
    df_raw = pd.read_excel(file, dtype=object, engine='openpyxl')
    df_raw.columns = df_raw.columns.str.strip()
    
    if len(df_raw.columns) < 12:
        st.error("🚨 Brak wymaganych kolumn w pliku. Oczekiwano kolumn od A do L (min. 12 kolumn z uwzględnieniem Month).")
        st.stop()
        
    # Dynamiczne nagłówki przesunięte o 1 kolumnę (indeksy 8, 9, 10, 11)
    cols = {
        "Month": df_raw.columns[0],
        "Customer": "Customer Name",
        "Country": "Country",
        "Vat": "Vat ID Nr.",
        "Code": "Art. Nr.",
        "Desc": "Article description",
        "Brand": "Brand Name",
        "Cat": "Category",
        "Val_Old": df_raw.columns[8],
        "Qty_Old": df_raw.columns[9],
        "Val_New": df_raw.columns[10],
        "Qty_New": df_raw.columns[11]
    }
    
    df = df_raw.copy()
    
    for c in [cols["Val_Old"], cols["Val_New"], cols["Qty_Old"], cols["Qty_New"]]:
        if c in df.columns: df[c] = df[c].apply(to_decimal)
        else: df[c] = Decimal('0')
            
    for c in ["Month", cols["Customer"], cols["Country"], cols["Vat"], cols["Code"], cols["Desc"], cols["Brand"], cols["Cat"]]:
        if c in df.columns: df[c] = df[c].astype(str).fillna("").replace("nan", "")
        else: df[c] = ""
            
    df["Category Clean"] = df[cols["Cat"]].apply(normalize_category)
    ALLOWED_CATEGORIES = [
        "Napkins","Hats","Banner","Straws","Bags","Plates","Paper Cups",
        "Tablecover","Reusable","Foil","Wooden","Candles","Latex",
        "Invitations","Articles","Masks","Pinata","Plastic Cups"
    ]
    df = df[df["Category Clean"].isin(ALLOWED_CATEGORIES)]
    
    # Czyszczenie z pustych Description
    df = df[df[cols["Desc"]].notna()]
    df = df[df[cols["Desc"]].str.lower() != "none"]
    
    return df, cols

# ================= MAIN RENDER ENGINE =================
def render_dashboard(df, df_original_all, cols, selected_category, selected_customer, selected_country, prefix=""):
    """
    Renderuje wszystkie sekcje analityczne. 
    `prefix` jest niezbędny do unikalnych kluczy widgetów Streamlit.
    """
    val_old, val_new = cols["Val_Old"], cols["Val_New"]
    qty_old, qty_new = cols["Qty_Old"], cols["Qty_New"]
    col_code, col_desc = cols["Code"], cols["Desc"]
    col_brand, col_customer = cols["Brand"], cols["Customer"]
    
    df_context = df_original_all.copy() if selected_customer == "All Customers" else df.copy()

    # ================= KPI =================
    st.markdown(f"## 💰 KPI (EUR / PCS)")
    use_df_for_kpi = df if (selected_category != "All Categories" or selected_customer != "All Customers" or selected_country != "All Countries") else df_original_all
    
    s_old, s_new = decimal_sum(use_df_for_kpi[val_old]), decimal_sum(use_df_for_kpi[val_new])
    q_old, q_new = decimal_sum(use_df_for_kpi[qty_old]), decimal_sum(use_df_for_kpi[qty_new])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Sales {val_old}", format_number_plain(s_old))
    c2.metric(f"Sales {val_new}", format_number_plain(s_new), yoy_label(calc_yoy_clean(s_new, s_old)))
    c3.metric(f"Qty {qty_old}", format_number_plain(q_old))
    c4.metric(f"Qty {qty_new}", format_number_plain(q_new), yoy_label(calc_yoy_clean(q_new, q_old)))

    # ================= CATEGORY PERFORMANCE =================
    if selected_category == "All Categories":
        st.markdown("## 📊 Category Performance")
        cat_perf = df_context.groupby("Category Clean").agg({val_old: decimal_sum, val_new: decimal_sum}).reset_index()
        cat_perf = sort_by_col_desc(cat_perf, val_new)
        
        total_old, total_new = decimal_sum(cat_perf[val_old]), decimal_sum(cat_perf[val_new])
        
        if total_old == 0 and total_new == 0:
            st.warning("No data for category performance")
        else:
            cat_perf[f"Share {val_old} %"] = cat_perf[val_old].apply(lambda x: (x / total_old * Decimal('100')) if total_old != 0 else Decimal('0'))
            cat_perf[f"Share {val_new} %"] = cat_perf[val_new].apply(lambda x: (x / total_new * Decimal('100')) if total_new != 0 else Decimal('0'))
            cat_perf["YoY"] = cat_perf.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
            cat_perf["YoY %"] = cat_perf["YoY"].apply(yoy_label)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"### {val_old}")
                plot_old = cat_perf.copy(); plot_old[val_old] = plot_old[val_old].apply(float)
                st.plotly_chart(px.pie(plot_old, names="Category Clean", values=val_old))
            with c2:
                st.markdown(f"### {val_new}")
                plot_new = cat_perf.copy(); plot_new[val_new] = plot_new[val_new].apply(float)
                st.plotly_chart(px.pie(plot_new, names="Category Clean", values=val_new))

            st.markdown("### Category Comparison")
            display_df = cat_perf.sort_values(val_new, ascending=False).copy()
            for c in [val_old, val_new]: display_df[c] = display_df[c].apply(format_number_plain)
            for c in [f"Share {val_old} %", f"Share {val_new} %"]: display_df[c] = display_df[c].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")
            st.dataframe(add_index(display_df[["Category Clean", val_old, f"Share {val_old} %", val_new, f"Share {val_new} %", "YoY %"]]))
        st.divider()

    # ================= BRAND PERFORMANCE =================
    st.markdown("## 🏷️ Brand Performance")
    brand = df.groupby(col_brand).agg({val_old: decimal_sum, val_new: decimal_sum}).reset_index()
    brand = sort_by_col_desc(brand, val_new)
    
    t_old, t_new = decimal_sum(brand[val_old]), decimal_sum(brand[val_new])
    brand[f"Share {val_old} %"] = brand[val_old].apply(lambda x: (x / t_old * Decimal('100')) if t_old != 0 else Decimal('0'))
    brand[f"Share {val_new} %"] = brand[val_new].apply(lambda x: (x / t_new * Decimal('100')) if t_new != 0 else Decimal('0'))
    brand["YoY %"] = brand.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1).apply(yoy_label)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {val_old}")
        b_old = brand.copy(); b_old[val_old] = b_old[val_old].apply(float)
        st.plotly_chart(px.pie(b_old, names=col_brand, values=val_old))
    with c2:
        st.markdown(f"### {val_new}")
        b_new = brand.copy(); b_new[val_new] = b_new[val_new].apply(float)
        st.plotly_chart(px.pie(b_new, names=col_brand, values=val_new))

    brand_disp = brand.copy()
    for c in [val_old, val_new]: brand_disp[c] = brand_disp[c].apply(format_number_plain)
    for c in [f"Share {val_old} %", f"Share {val_new} %"]: brand_disp[c] = brand_disp[c].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")
    st.dataframe(add_index(brand_disp[[col_brand, val_old, f"Share {val_old} %", val_new, f"Share {val_new} %", "YoY %"]]))
    st.divider()

    # ================= TOP PRODUCTS =================
    st.markdown("## 🏆 Top Products")
    if df.empty:
        st.warning("No data available for selected filters")
    else:
        base_df = df.copy()
        col1_top, col2_top = st.columns(2)
        
        with col1_top:
            st.write(f"### {val_old}")
            d_old = base_df.groupby(col_code).agg({col_desc: "first", val_old: decimal_sum, qty_old: decimal_sum}).reset_index()
            d_old = d_old.merge(base_df.groupby(col_code).agg({val_new: decimal_sum}).reset_index(), on=col_code, how="left")
            d_old[val_new] = d_old[val_new].fillna(Decimal('0'))
            
            d_old = sort_by_col_desc(d_old[d_old[val_old] > 0], val_old)
            if d_old.empty: st.info(f"No sales in {val_old}")
            else:
                top_old = d_old.head(10)
                tot_o = decimal_sum(d_old[val_old])
                top_old["Share %"] = top_old[val_old].apply(lambda x: (x / tot_o * Decimal('100')) if tot_o != 0 else Decimal('0'))
                top_disp = top_old.copy()
                for c in [val_old, qty_old]: top_disp[c] = top_disp[c].apply(format_number_plain)
                top_disp["Share %"] = top_disp["Share %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")
                st.dataframe(add_index(top_disp[[col_code, col_desc, val_old, qty_old, "Share %"]]))
                st.write(f"Top 10 share: {int((decimal_sum(top_old[val_old]) / tot_o * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")

        with col2_top:
            st.write(f"### {val_new}")
            d_new = base_df.groupby(col_code).agg({col_desc: "first", val_new: decimal_sum, qty_new: decimal_sum}).reset_index()
            d_new = sort_by_col_desc(d_new[d_new[val_new] > 0], val_new)
            
            if d_new.empty: st.info(f"No sales in {val_new}")
            else:
                top_new = d_new.head(10)
                tot_n = decimal_sum(d_new[val_new])
                top_new["Share %"] = top_new[val_new].apply(lambda x: (x / tot_n * Decimal('100')) if tot_n != 0 else Decimal('0'))
                top_n_disp = top_new.copy()
                for c in [val_new, qty_new]: top_n_disp[c] = top_n_disp[c].apply(format_number_plain)
                top_n_disp["Share %"] = top_n_disp["Share %"].apply(lambda x: f"{int(x.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")
                st.dataframe(add_index(top_n_disp[[col_code, col_desc, val_new, qty_new, "Share %"]]))
                st.write(f"Top 10 share: {int((decimal_sum(top_new[val_new]) / tot_n * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))}%")
    st.divider()

    # ================= PARETO =================
    st.markdown("## 📊 Pareto Analysis")
    ptab1, ptab2 = st.tabs([val_old, val_new])
    for year_tab, val in zip([ptab1, ptab2], [val_old, val_new]):
        with year_tab:
            p = df.groupby(col_code).agg({col_desc: "first", "Category Clean": "first", val: decimal_sum}).reset_index()
            p = p[p[val] > 0]
            if p.empty: st.info("No sales in this period")
            else:
                p = sort_by_col_desc(p, val)
                p["cum_value"] = p[val].cumsum()
                total_value = decimal_sum(p[val])
                p["cum_share"] = p["cum_value"].apply(lambda x: (x / total_value) if isinstance(x, Decimal) else Decimal(str(x)) / total_value)
                
                top80 = p[p["cum_share"] <= Decimal('0.8')]
                total_sku = p[col_code].nunique()
                pareto_sku = top80[col_code].nunique()
                sku_share = (Decimal(pareto_sku) / Decimal(total_sku) * Decimal('100')) if total_sku > 0 else Decimal('0')
                
                st.write(f"Top SKU for 80%: {pareto_sku} / {total_sku} ({int(sku_share.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}% of SKU)")
                p_disp = top80[[col_code, col_desc, "Category Clean", val]].copy()
                p_disp[val] = p_disp[val].apply(format_number_plain)
                st.dataframe(add_index(p_disp))
    st.divider()

    # ================= ABC =================
    st.markdown("## 📊 ABC Analysis")
    atab1, atab2 = st.tabs([val_old, val_new])
    for year_tab, val in zip([atab1, atab2], [val_old, val_new]):
        with year_tab:
            a = df.groupby(col_code).agg({col_desc: "first", val_old: decimal_sum, val_new: decimal_sum}).reset_index()
            a = a[a[val] > 0]
            if a.empty: st.info("No sales in this period")
            else:
                a = sort_by_col_desc(a, val).reset_index(drop=True)
                total_val = decimal_sum(a[val])
                a["cum"] = a[val].cumsum().apply(lambda x: x / total_val)
                a["segment"] = "C"
                a.loc[a["cum"] <= Decimal('0.7'), "segment"] = "A"
                a.loc[(a["cum"] > Decimal('0.7')) & (a["cum"] <= Decimal('0.9')), "segment"] = "B"
                
                seg_counts = a["segment"].value_counts()
                st.write(f"A: {seg_counts.get('A',0)} | B: {seg_counts.get('B',0)} | C: {seg_counts.get('C',0)}")
                a_disp = a[[col_code, col_desc, val, "segment"]].copy()
                a_disp[val] = a_disp[val].apply(format_number_plain)
                st.dataframe(add_index(a_disp))
    st.divider()

    # ================= L4L / YOY =================
    st.markdown("## 📈 L4L Analysis")
    df_yoy = df.groupby(col_code).agg({
        col_desc: "first", val_old: decimal_sum, val_new: decimal_sum,
        qty_old: decimal_sum, qty_new: decimal_sum
    }).reset_index()
    df_yoy = sort_by_col_desc(df_yoy, val_new)
    df_yoy["YoY %"] = df_yoy.apply(lambda x: yoy_label(calc_yoy_clean(x[val_new], x[val_old])), axis=1)

    df_yoy_display = df_yoy.copy()
    for c in [val_old, val_new, qty_old, qty_new]: df_yoy_display[c] = df_yoy_display[c].apply(format_number_plain)
    st.dataframe(add_index(df_yoy_display[[col_code, col_desc, val_old, val_new, qty_old, qty_new, "YoY %"]]))
    st.divider()

    # ================= AUTO INSIGHTS =================
    st.markdown("## 🧠 Auto Insights")
    cat_ins = df_context.groupby("Category Clean").agg({val_old: decimal_sum, val_new: decimal_sum}).reset_index()
    cat_ins = sort_by_col_desc(cat_ins, val_new)
    cat_ins["YoY"] = cat_ins.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
    cat_ins["YoY %"] = cat_ins["YoY"].apply(yoy_label)

    st.write("### Top 5 Categories")
    ic1, ic2 = st.columns(2)
    with ic1:
        st.write(f"#### {val_old}")
        top_old_cat = cat_ins.sort_values(val_old, ascending=False).head(5).copy()
        top_old_cat[val_old] = top_old_cat[val_old].apply(format_number_plain)
        st.dataframe(add_index(top_old_cat[["Category Clean", val_old]]))
    with ic2:
        st.write(f"#### {val_new}")
        top_new_cat = cat_ins.sort_values(val_new, ascending=False).head(5).copy()
        top_new_cat[val_new] = top_new_cat[val_new].apply(format_number_plain)
        st.dataframe(add_index(top_new_cat[["Category Clean", val_new, "YoY %"]]))

    st.write("### Growth (L4L)")
    growth_ins = cat_ins[cat_ins["YoY"] > 0].sort_values("YoY", ascending=False).head(5)
    if growth_ins.empty: st.info("There is no growth in categories")
    else:
        g_disp = growth_ins.copy()
        for c in [val_old, val_new]: g_disp[c] = g_disp[c].apply(format_number_plain)
        st.dataframe(add_index(g_disp[["Category Clean", val_old, val_new, "YoY %"]]))

    st.write("### Risk")
    risk_ins = cat_ins[cat_ins["YoY"] < 0].sort_values("YoY").head(5)
    if risk_ins.empty: st.success("There is no risk in categories")
    else:
        r_disp = risk_ins.copy()
        for c in [val_old, val_new]: r_disp[c] = r_disp[c].apply(format_number_plain)
        st.dataframe(add_index(r_disp[["Category Clean", val_old, val_new, "YoY %"]]))
    st.divider()

    # ================= CUSTOMER IMPACT =================
    st.markdown("## 👥 Customer Impact (Growth vs Decline)")
    
    all_categories = sorted(df_original_all["Category Clean"].dropna().unique()) if "Category Clean" in df_original_all.columns else []
    selected_cat_impact = st.selectbox("Select Category for Impact Analysis", ["All Categories"] + all_categories, key=f"{prefix}_cat_impact")
    all_brands = sorted(df_original_all[col_brand].dropna().unique()) if col_brand in df_original_all.columns else []
    selected_brand_impact = st.selectbox("Select Brand (License)", ["All Brands"] + all_brands, key=f"{prefix}_brand_impact")

    df_impact = df_original_all.copy()
    if selected_cat_impact != "All Categories": df_impact = df_impact[df_impact["Category Clean"] == selected_cat_impact]
    if selected_brand_impact != "All Brands": df_impact = df_impact[df_impact[col_brand] == selected_brand_impact]

    impact = df_impact.groupby(col_customer).agg({val_old: decimal_sum, val_new: decimal_sum}).reset_index()
    impact = impact[(impact[val_old] != 0) | (impact[val_new] != 0)]
    impact["Change Value"] = impact[val_new] - impact[val_old]
    impact["Special Case"] = ((impact[val_old] < 0) & (impact[val_new] == 0))
    impact["YoY"] = impact.apply(lambda x: calc_yoy_clean(x[val_new], x[val_old]), axis=1)
    impact["YoY %"] = impact.apply(lambda x: yoy_label(x["YoY"], x["Special Case"]), axis=1)

    st.write("### 🟢 Top Growth Drivers")
    growth = impact[(impact["Change Value"] > 0) & (~impact["Special Case"])].sort_values("Change Value", ascending=False).head(10)
    growth_special = impact[impact["Special Case"]].head(10)
    growth = pd.concat([growth, growth_special])
    if growth.empty: st.info("No growth generated by customers")
    else:
        g_disp = growth.copy()
        for c in [val_old, val_new, "Change Value"]: g_disp[c] = g_disp[c].apply(format_number_plain)
        st.dataframe(add_index(g_disp[[col_customer, val_old, val_new, "Change Value", "YoY %"]]))

    st.write("### 🔴 Top Decline Drivers")
    decline = impact[(impact["Change Value"] < 0)].sort_values("Change Value").head(10)
    decline_special = impact[impact["Special Case"]].head(10)
    decline = pd.concat([decline, decline_special])
    if decline.empty: st.success("No decline across customers")
    else:
        d_disp = decline.copy()
        for c in [val_old, val_new, "Change Value"]: d_disp[c] = d_disp[c].apply(format_number_plain)
        st.dataframe(add_index(d_disp[[col_customer, val_old, val_new, "Change Value", "YoY %"]]))


# ================= CONFIG & UI INITIALIZATION =================
st.set_page_config(layout="wide")
st.title("📊 Sales Intelligence Dashboard - © Patryk Pociecha")

st.markdown("### 📂 Wgraj pliki z danymi")
col1, col2 = st.columns(2)
with col1:
    file_l4l = st.file_uploader("Upload L4L (np. 2025 vs 2026)", type=["xlsx"])
with col2:
    file_full = st.file_uploader("Upload Full Year (np. 2024 vs 2025)", type=["xlsx"])

if not file_l4l and not file_full:
    st.warning("⬆️ Wgraj przynajmniej jeden plik Excel aby rozpocząć.")
    st.stop()

# ================= LOAD DATA =================
df_l4l, cols_l4l = load_and_prep_data(file_l4l) if file_l4l else (None, None)
df_full, cols_full = load_and_prep_data(file_full) if file_full else (None, None)

base_df = df_l4l if df_l4l is not None else df_full
base_cols = cols_l4l if cols_l4l is not None else cols_full

st.divider()

# ================= GLOBAL FILTERS =================
st.markdown("### 🔍 Globalne Filtry (Dla zakładki 2 i 3)")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    countries = ["All Countries"] + sorted(base_df[base_cols["Country"]].replace("", pd.NA).dropna().unique())
    g_country = st.selectbox("🌍 Select Country", countries)

with col_f2:
    customers = ["All Customers"] + sorted(base_df[base_cols["Customer"]].replace("", pd.NA).dropna().unique())
    g_customer = st.selectbox("👤 Select Customer", customers)

with col_f3:
    categories = ["All Categories"] + sorted(base_df["Category Clean"].dropna().unique())
    g_category = st.selectbox("📂 Select Category", categories)

# ================= APPLY GLOBAL FILTERS =================
def apply_filters(df, c_cols):
    if df is None: return None, None
    d = df.copy()
    if g_country != "All Countries": d = d[d[c_cols["Country"]] == g_country]
    d_original_all = d.copy() 
    
    if g_customer != "All Customers": d = d[d[c_cols["Customer"]] == g_customer]
    if g_category != "All Categories": d = d[d["Category Clean"] == g_category]
    return d, d_original_all

df_l4l_f, df_l4l_orig = apply_filters(df_l4l, cols_l4l)
df_full_f, df_full_orig = apply_filters(df_full, cols_full)

st.divider()

# ================= TABS =================
tab1, tab2, tab3 = st.tabs([
    "📈 1. Overview (3 Years L4L)", 
    "📅 2. Detailed L4L (Month Select)", 
    "📊 3. Full Year"
])

# ----------------- TAB 1: 3 YEARS OVERVIEW -----------------
with tab1:
    st.header("Porównanie 3 lat (YTD na podstawie miesięcy L4L)")
    if df_l4l is not None and df_full is not None:
        available_months = df_l4l_orig[cols_l4l["Month"]].dropna().unique()
        st.info(f"💡 Zestawienie L4L obejmuje dane globalne z miesięcy: **{', '.join(available_months)}** (wykryte w pliku L4L).")
        
        df_full_ytd = df_full_orig[df_full_orig[cols_full["Month"]].isin(available_months)]
        
        val_year1 = decimal_sum(df_full_ytd[cols_full["Val_Old"]]) 
        val_year2 = decimal_sum(df_l4l_orig[cols_l4l["Val_Old"]])  
        val_year3 = decimal_sum(df_l4l_orig[cols_l4l["Val_New"]])  
        
        y1_name = cols_full["Val_Old"]
        y2_name = cols_l4l["Val_Old"]
        y3_name = cols_l4l["Val_New"]
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total Sales {y1_name} (YTD)", format_number_plain(val_year1))
        c2.metric(f"Total Sales {y2_name} (YTD)", format_number_plain(val_year2), yoy_label(calc_yoy_clean(val_year2, val_year1)))
        c3.metric(f"Total Sales {y3_name} (YTD)", format_number_plain(val_year3), yoy_label(calc_yoy_clean(val_year3, val_year2)))
        
        chart_data = pd.DataFrame({
            "Rok": [y1_name, y2_name, y3_name],
            "Sprzedaż": [float(val_year1), float(val_year2), float(val_year3)]
        })
        st.plotly_chart(px.bar(chart_data, x="Rok", y="Sprzedaż", text="Sprzedaż", title="Total Sales L4L (3 lata)"), use_container_width=True)
    else:
        st.warning("⚠️ Aby zobaczyć zestawienie z 3 lat, musisz wgrać oba pliki (L4L oraz Full Year).")

# ----------------- TAB 2: DETAILED L4L -----------------
with tab2:
    if df_l4l is not None:
        st.header("Szczegółowa Analiza L4L (Wybór Miesięcy)")
        
        c_mode, c_months = st.columns([1, 2])
        with c_mode:
            options = ["Plik L4L (Najnowszy)"]
            if df_full is not None: options.append("Plik Full Year (Poprzedni)")
            l4l_mode = st.radio("Wybierz zestaw danych", options)
        
        active_df_f = df_l4l_f if l4l_mode == "Plik L4L (Najnowszy)" else df_full_f
        active_df_orig = df_l4l_orig if l4l_mode == "Plik L4L (Najnowszy)" else df_full_orig
        active_cols = cols_l4l if l4l_mode == "Plik L4L (Najnowszy)" else cols_full

        with c_months:
            available_m = active_df_orig[active_cols["Month"]].dropna().unique().tolist()
            available_m = sorted(available_m, key=lambda m: MONTHS_ORDER.index(m) if m in MONTHS_ORDER else 99)
            selected_months = st.multiselect("Wybierz miesiące do analizy L4L", MONTHS_ORDER, default=available_m)
        
        active_df_f = active_df_f[active_df_f[active_cols["Month"]].isin(selected_months)]
        active_df_orig = active_df_orig[active_df_orig[active_cols["Month"]].isin(selected_months)]
        
        if selected_months:
            render_dashboard(active_df_f, active_df_orig, active_cols, g_category, g_customer, g_country, prefix="tab2")
        else:
            st.info("Wybierz przynajmniej jeden miesiąc.")
    else:
        st.warning("⚠️ Wgraj plik L4L aby wyświetlić tę zakładkę.")

# ----------------- TAB 3: FULL YEAR -----------------
with tab3:
    if df_full is not None:
        st.header(f"Szczegółowa Analiza - Full Year ({cols_full['Val_Old']} vs {cols_full['Val_New']})")
        st.info("Wszystkie widoki wygenerowane na podstawie pełnego roku ze starszego pliku.")
        render_dashboard(df_full_f, df_full_orig, cols_full, g_category, g_customer, g_country, prefix="tab3")
    else:
        st.warning("⚠️ Wgraj plik Full Year aby wyświetlić tę zakładkę.")
