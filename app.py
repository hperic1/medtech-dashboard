
import os
import re
from typing import List, Tuple

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="MedTech M&A & Venture Dashboard",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

COLORS = {
    "ma_primary": "#7FA8C9",
    "ma_secondary": "#A8C9D1",
    "venture_primary": "#C9A77F",
    "venture_secondary": "#D9C9A8",
    "count_line": "#A3A3A3",
}

st.markdown(
    """
<style>
    .dataframe { width: 100% !important; }
    div[data-testid="stDataFrame"] > div { width: 100% !important; }
    .stDataFrame { width: 100%; }
    .element-container { width: 100%; }
    .filter-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
    }
    .metric-box {
        padding: 15px;
        border-radius: 10px;
        margin: 8px 0 14px 0;
        border-left: 4px solid #7FA8C9;
        background: linear-gradient(135deg, #e8f1f8 0%, #b8d4e8 100%);
    }
    .metric-box-venture {
        border-left: 4px solid #C9A77F;
        background: linear-gradient(135deg, #faf6f0 0%, #e8dcc8 100%);
    }
</style>
""",
    unsafe_allow_html=True,
)


def find_excel_path() -> str | None:
    possible_paths = [
        "data/MedTech_YTD_Standardized.xlsx",
        "./data/MedTech_YTD_Standardized.xlsx",
        "MedTech_YTD_Standardized.xlsx",
        "MedTech_Deals.xlsx",
        "./MedTech_Deals.xlsx",
        "data/MedTech_Deals.xlsx",
        "/mnt/project/MedTech_YTD_Standardized.xlsx",
        os.path.join(os.path.dirname(__file__), "data", "MedTech_YTD_Standardized.xlsx"),
        os.path.join(os.path.dirname(__file__), "MedTech_YTD_Standardized.xlsx"),
        os.path.join(os.path.dirname(__file__), "MedTech_Deals.xlsx"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def extract_year(value) -> str:
    match = re.search(r"(20\d{2})", str(value))
    return match.group(1) if match else "Undisclosed"


def extract_quarter_label(value) -> str:
    match = re.search(r"(Q[1-4])", str(value).upper())
    return match.group(1) if match else "Undisclosed"


def quarter_sort_key(label: str) -> int:
    return {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(label, 99)


def parse_money(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text in {"", "Undisclosed", "nan", "None"}:
        return 0.0
    multiplier = 1.0
    if "B" in text:
        multiplier = 1_000_000_000
    elif "M" in text:
        multiplier = 1_000_000
    cleaned = (
        text.replace("$", "")
        .replace(",", "")
        .replace("B", "")
        .replace("M", "")
        .strip()
    )
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return 0.0


def format_currency_abbreviated(value) -> str:
    if pd.isna(value):
        return "Undisclosed"
    value = float(value)
    if value <= 0:
        return "Undisclosed"
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    return f"${value:,.0f}"


def format_currency_full(value) -> str:
    if pd.isna(value):
        return "Undisclosed"
    value = float(value)
    if value <= 0:
        return "Undisclosed"
    return f"${value:,.0f}"


def normalize_dataframe(df: pd.DataFrame, value_column: str) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]
    if "Sector" in df.columns:
        df = df.rename(columns={"Sector": "Category"})
    if "Conference" in df.columns:
        df = df.drop(columns=["Conference"])
    df = df.fillna("Undisclosed")

    if "Quarter" in df.columns:
        df["Quarter"] = df["Quarter"].astype(str)
        df["Year"] = df["Quarter"].apply(extract_year)
        df["Quarter Label"] = df["Quarter"].apply(extract_quarter_label)
    else:
        df["Year"] = "Undisclosed"
        df["Quarter Label"] = "Undisclosed"

    if "Month" in df.columns:
        df["Month"] = df["Month"].astype(str)

    df["_value_numeric"] = df[value_column].apply(parse_money)
    return df


@st.cache_data
def load_data():
    try:
        excel_path = find_excel_path()
        if not excel_path:
            st.error("❌ Cannot find MedTech data file.")
            return pd.DataFrame(), pd.DataFrame()

        ma_df = pd.read_excel(excel_path, sheet_name="YTD M&A Activity")
        inv_df = pd.read_excel(excel_path, sheet_name="YTD Investment Activity")

        ma_df = normalize_dataframe(ma_df, "Deal Value")
        inv_df = normalize_dataframe(inv_df, "Amount Raised")
        return ma_df, inv_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()


def save_data(ma_df: pd.DataFrame, inv_df: pd.DataFrame) -> bool:
    try:
        excel_path = find_excel_path()
        if excel_path is None:
            os.makedirs("data", exist_ok=True)
            excel_path = "data/MedTech_Deals.xlsx"

        backup_path = excel_path.replace(".xlsx", "_backup.xlsx")
        if os.path.exists(excel_path):
            import shutil
            shutil.copy2(excel_path, backup_path)
            st.session_state.last_backup_time = pd.Timestamp.now()
            st.session_state.backup_available = True

        ma_to_save = ma_df.copy()
        inv_to_save = inv_df.copy()

        for df in (ma_to_save, inv_to_save):
            for helper_col in ["Year", "Quarter Label", "_value_numeric"]:
                if helper_col in df.columns:
                    df.drop(columns=[helper_col], inplace=True)

        if "Category" in ma_to_save.columns:
            ma_to_save = ma_to_save.rename(columns={"Category": "Sector"})
        if "Category" in inv_to_save.columns:
            inv_to_save = inv_to_save.rename(columns={"Category": "Sector"})

        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="w") as writer:
            ma_to_save.to_excel(writer, sheet_name="YTD M&A Activity", index=False)
            inv_to_save.to_excel(writer, sheet_name="YTD Investment Activity", index=False)

        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        st.warning("⚠️ Streamlit Cloud may not persist local file changes after restarts.")
        return False


def undo_last_upload():
    try:
        excel_path = find_excel_path()
        if not excel_path:
            return False, "Could not find data file"
        backup_path = excel_path.replace(".xlsx", "_backup.xlsx")
        if not os.path.exists(backup_path):
            return False, "No backup file found"
        import shutil
        shutil.copy2(backup_path, excel_path)
        st.session_state.backup_available = False
        st.session_state.last_backup_time = None
        return True, "Successfully restored previous version"
    except Exception as e:
        return False, f"Error restoring backup: {e}"


def get_available_years(df: pd.DataFrame) -> List[str]:
    years = sorted(
        [y for y in df["Year"].dropna().astype(str).unique() if y != "Undisclosed"],
        key=lambda x: int(x),
    )
    return years


def default_current_year(years: List[str]) -> List[str]:
    return [max(years, key=int)] if years else []


def apply_filters(
    df: pd.DataFrame,
    years: List[str],
    quarters: List[str],
    categories: List[str],
    months: List[str] | None = None,
    search_text: str = "",
) -> pd.DataFrame:
    filtered = df.copy()
    if years:
        filtered = filtered[filtered["Year"].isin(years)]
    if quarters:
        filtered = filtered[filtered["Quarter Label"].isin(quarters)]
    if categories:
        filtered = filtered[filtered["Category"].isin(categories)]
    if months:
        filtered = filtered[filtered["Month"].isin(months)]
    if search_text:
        mask = filtered.apply(
            lambda row: row.astype(str).str.contains(search_text, case=False, na=False).any(),
            axis=1,
        )
        filtered = filtered[mask]
    return filtered


def render_filter_controls(df: pd.DataFrame, key_prefix: str, show_month: bool = True):
    years = get_available_years(df)
    categories = sorted([c for c in df["Category"].unique() if c != "Undisclosed"])
    quarter_options = [q for q in ["Q1", "Q2", "Q3", "Q4"] if q in set(df["Quarter Label"])]
    month_options = []
    if show_month and "Month" in df.columns:
        month_options = sorted([m for m in df["Month"].unique() if m != "Undisclosed"])

    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    cols = st.columns(4 if show_month else 3)

    with cols[0]:
        selected_years = st.multiselect(
            "Year",
            options=years,
            default=default_current_year(years),
            key=f"{key_prefix}_years",
            help="Default is the most current year. Add another year to compare side by side.",
        )
    with cols[1]:
        selected_quarters = st.multiselect(
            "Quarter",
            options=quarter_options,
            default=quarter_options,
            key=f"{key_prefix}_quarters",
            help="Compare the same quarter across years by selecting one or more quarters here.",
        )
    with cols[2]:
        selected_categories = st.multiselect(
            "Category",
            options=categories,
            default=[],
            key=f"{key_prefix}_categories",
        )
    if show_month:
        with cols[3]:
            selected_months = st.multiselect(
                "Month",
                options=month_options,
                default=[],
                key=f"{key_prefix}_months",
            )
    else:
        selected_months = []
    st.markdown("</div>", unsafe_allow_html=True)

    return selected_years, selected_quarters, selected_categories, selected_months


def create_metric_box(label: str, value: str, venture: bool = False):
    box_class = "metric-box metric-box-venture" if venture else "metric-box"
    st.markdown(
        f"""
        <div class="{box_class}">
            <div style="font-size:12px;color:#555;font-weight:500;margin-bottom:4px;">{label}</div>
            <div style="font-size:24px;font-weight:700;color:#2c3e50;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_quarterly_comparison_chart(
    df: pd.DataFrame,
    title: str,
    chart_type: str,
    value_label: str,
):
    if df.empty:
        st.info(f"No data available for {title.lower()}.")
        return None

    grouped = (
        df[df["Quarter Label"] != "Undisclosed"]
        .groupby(["Year", "Quarter Label"], as_index=False)
        .agg(Total_Value=("_value_numeric", "sum"), Deal_Count=("Company", "count"))
    )
    if grouped.empty:
        st.info(f"No quarterly data available for {title.lower()}.")
        return None

    grouped["Quarter Sort"] = grouped["Quarter Label"].apply(quarter_sort_key)
    grouped["Year Sort"] = grouped["Year"].apply(lambda x: int(x) if str(x).isdigit() else 9999)
    grouped = grouped.sort_values(["Quarter Sort", "Year Sort"])

    year_order = sorted(grouped["Year"].unique(), key=int)
    base_color = COLORS["ma_primary"] if chart_type == "ma" else COLORS["venture_primary"]
    secondary_color = COLORS["ma_secondary"] if chart_type == "ma" else COLORS["venture_secondary"]
    palette = [base_color, secondary_color, "#B8B8B8", "#8EA8A1"]

    fig = go.Figure()
    max_value = max(grouped["Total_Value"].max(), 1)
    max_count = max(grouped["Deal_Count"].max(), 1)

    for idx, year in enumerate(year_order):
        year_df = grouped[grouped["Year"] == year].sort_values("Quarter Sort")
        fig.add_trace(
            go.Bar(
                x=year_df["Quarter Label"],
                y=year_df["Total_Value"],
                name=f"{year} Value",
                marker_color=palette[idx % len(palette)],
                text=[format_currency_abbreviated(v) for v in year_df["Total_Value"]],
                textposition="outside",
                offsetgroup=str(year),
                legendgroup=str(year),
                hovertemplate="<b>%{x} %{customdata}</b><br>Value: %{text}<extra></extra>",
                customdata=[year] * len(year_df),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=year_df["Quarter Label"],
                y=year_df["Deal_Count"],
                name=f"{year} Count",
                mode="lines+markers+text",
                text=year_df["Deal_Count"],
                textposition="top center",
                yaxis="y2",
                line=dict(width=2, dash="solid"),
                marker=dict(size=9),
                legendgroup=str(year),
                hovertemplate="<b>%{x} %{customdata}</b><br>Count: %{y}<extra></extra>",
                customdata=[year] * len(year_df),
            )
        )

    fig.update_layout(
        title=title,
        barmode="group",
        height=420,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(title="Quarter", showgrid=False, categoryorder="array", categoryarray=["Q1", "Q2", "Q3", "Q4"]),
        yaxis=dict(title=value_label, showgrid=False, range=[0, max_value * 1.3]),
        yaxis2=dict(title="Deal Count", overlaying="y", side="right", showgrid=False, range=[0, max_count * 1.4]),
        margin=dict(t=90, l=40, r=40, b=40),
    )
    return fig


def create_sunburst_chart(df: pd.DataFrame, deal_type: str):
    if df.empty:
        st.info(f"No category data available for {deal_type.lower()}.")
        return None

    grouped = (
        df[(df["Category"] != "Undisclosed") & (df["_value_numeric"] > 0)]
        .groupby("Category", as_index=False)
        .agg(Total_Value=("_value_numeric", "sum"))
        .sort_values("Total_Value", ascending=False)
    )
    if grouped.empty:
        st.info(f"No category data available for {deal_type.lower()}.")
        return None

    color_palette = (
        ["#7FA8C9", "#A8C9D1", "#6B8BA3", "#94B4C9", "#5A7A94"]
        if deal_type == "M&A"
        else ["#C9A77F", "#D9C9A8", "#B89968", "#CCBB99", "#A88E6C"]
    )

    fig = go.Figure(
        go.Sunburst(
            labels=grouped["Category"],
            parents=[""] * len(grouped),
            values=grouped["Total_Value"],
            text=[format_currency_abbreviated(v) for v in grouped["Total_Value"]],
            textinfo="label+text",
            marker=dict(colors=[color_palette[i % len(color_palette)] for i in range(len(grouped))]),
            hovertemplate="<b>%{label}</b><br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(height=380, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="white")
    return fig


def display_summary_table(df: pd.DataFrame, value_col: str, title_prefix: str):
    if df.empty:
        st.info("No rows match the current filters.")
        return

    summary = (
        df.groupby(["Year", "Quarter Label"], as_index=False)
        .agg(Deal_Count=("Company", "count"), Total_Value=("_value_numeric", "sum"))
    )
    summary["Quarter Sort"] = summary["Quarter Label"].apply(quarter_sort_key)
    summary = summary.sort_values(["Year", "Quarter Sort"])
    summary["Total Value"] = summary["Total_Value"].apply(format_currency_abbreviated)
    st.markdown(f"#### {title_prefix} summary by year and quarter")
    st.dataframe(
        summary[["Year", "Quarter Label", "Deal_Count", "Total Value"]],
        hide_index=True,
        use_container_width=True,
    )


def display_deal_tables_by_year(df: pd.DataFrame, value_column: str, title_prefix: str):
    if df.empty:
        st.info("No rows match the current filters.")
        return

    selected_years = sorted(df["Year"].unique(), key=int)
    num_years = len(selected_years)
    cols = st.columns(num_years) if num_years > 1 else [st.container()]

    for idx, year in enumerate(selected_years):
        target = cols[idx] if num_years > 1 else cols[0]
        with target:
            year_df = df[df["Year"] == year].copy()
            year_df = year_df.sort_values(["Quarter Label", "_value_numeric"], ascending=[True, False])
            year_df[value_column] = year_df["_value_numeric"].apply(format_currency_full)
            display_cols = [
                c for c in year_df.columns
                if c not in {"_value_numeric"} and not c.startswith("Unnamed") and c.strip() != ""
            ]
            st.markdown(f"#### {title_prefix} — {year}")
            st.dataframe(year_df[display_cols], hide_index=True, use_container_width=True)


def show_home():
    st.markdown("# Welcome to the MedTech M&A & Venture Dashboard")
    st.write(
        "This dashboard lets you explore MedTech M&A and venture activity with year and quarter filters. "
        "The default view focuses on the most current year, and you can add prior years to compare side by side."
    )
    st.write(
        "Use the Deal Activity tab to analyze transactions, filter across years and quarters, "
        "and review charts and tables for M&A and venture activity."
    )
    st.markdown("---")
    try:
        with open("assets/dashboard_walkthrough.webm", "rb") as video_file:
            st.video(video_file.read())
    except FileNotFoundError:
        st.info("📹 Video walkthrough coming soon!")
    st.markdown("---")
    st.markdown(
        "**Sources:** Desk Research and [JP Morgan Biopharma & MedTech Deal Reports]"
        "(https://www.jpmorgan.com/insights/markets-and-economy/outlook/biopharma-medtech-deal-reports)",
        unsafe_allow_html=True,
    )


def show_deal_activity(ma_df: pd.DataFrame, inv_df: pd.DataFrame):
    st.header("Deal Activity Dashboard")

    overview_col1, overview_col2 = st.columns(2)

    with overview_col1:
        st.markdown("### M&A Activity")
        years, quarters, categories, months = render_filter_controls(ma_df, "ma_overview", show_month=True)
        filtered_ma = apply_filters(ma_df, years, quarters, categories, months)

        create_metric_box("Total M&A Deal Value", format_currency_abbreviated(filtered_ma["_value_numeric"].sum()))
        create_metric_box("Total M&A Deal Count", str(len(filtered_ma)))

        fig = create_quarterly_comparison_chart(filtered_ma, "M&A Activity by Quarter", "ma", "Total Deal Value (USD)")
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### M&A Deals by Category")
        sunburst = create_sunburst_chart(filtered_ma, "M&A")
        if sunburst:
            st.plotly_chart(sunburst, use_container_width=True)

    with overview_col2:
        st.markdown("### Venture Investment")
        years, quarters, categories, _ = render_filter_controls(inv_df, "inv_overview", show_month=False)
        filtered_inv = apply_filters(inv_df, years, quarters, categories)

        create_metric_box(
            "Total Investment Value",
            format_currency_abbreviated(filtered_inv["_value_numeric"].sum()),
            venture=True,
        )
        create_metric_box("Total Investment Deal Count", str(len(filtered_inv)), venture=True)

        fig = create_quarterly_comparison_chart(
            filtered_inv,
            "Venture Investment by Quarter",
            "venture",
            "Total Investment Value (USD)",
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Venture Deals by Category")
        sunburst = create_sunburst_chart(filtered_inv, "Venture")
        if sunburst:
            st.plotly_chart(sunburst, use_container_width=True)

    st.markdown("---")
    st.subheader("M&A Activity")
    search_ma = st.text_input("🔍 Search M&A Deals", placeholder="Search by company, acquirer, technology...", key="search_ma")
    years, quarters, categories, months = render_filter_controls(ma_df, "ma_table", show_month=True)
    filtered_ma = apply_filters(ma_df, years, quarters, categories, months, search_text=search_ma)
    tab1, tab2, tab3 = st.tabs(["📊 Tables", "🏆 Top Deals", "📈 Summary"])

    with tab1:
        display_deal_tables_by_year(filtered_ma, "Deal Value", "M&A Deals")
    with tab2:
        if filtered_ma.empty:
            st.info("No M&A deals match the current filters.")
        else:
            top_deals = filtered_ma.sort_values("_value_numeric", ascending=False).head(3)
            for _, row in top_deals.iterrows():
                verb = "merged with" if row.get("Deal Type (Merger / Acquisition)", "") == "Merger" else "acquired"
                st.markdown(f"**{row['Acquirer']} {verb} {row['Company']}**")
                st.markdown(
                    f"<h2 style='margin-top:-8px;color:{COLORS['ma_primary']};'>{format_currency_abbreviated(row['_value_numeric'])}</h2>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"Category: {row.get('Category', 'N/A')} | Quarter: {row.get('Quarter', 'N/A')} | "
                    f"Month: {row.get('Month', 'N/A')}"
                )
                st.markdown("---")
    with tab3:
        display_summary_table(filtered_ma, "Deal Value", "M&A")

    st.markdown("---")
    st.subheader("Venture Investment Activity")
    search_inv = st.text_input(
        "🔍 Search Investment Deals",
        placeholder="Search by company, investors, technology...",
        key="search_inv",
    )
    years, quarters, categories, _ = render_filter_controls(inv_df, "inv_table", show_month=False)
    filtered_inv = apply_filters(inv_df, years, quarters, categories, search_text=search_inv)
    tab1, tab2, tab3 = st.tabs(["📊 Tables", "🏆 Top Deals", "📈 Summary"])

    with tab1:
        display_deal_tables_by_year(filtered_inv, "Amount Raised", "Investment Deals")
    with tab2:
        if filtered_inv.empty:
            st.info("No investment deals match the current filters.")
        else:
            top_deals = filtered_inv.sort_values("_value_numeric", ascending=False).head(3)
            for _, row in top_deals.iterrows():
                st.markdown(f"**{row['Company']}**")
                st.markdown(
                    f"<h2 style='margin-top:-8px;color:{COLORS['venture_primary']};'>{format_currency_abbreviated(row['_value_numeric'])}</h2>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"Type: {row.get('Funding type (VC / PE)', 'N/A')} | Category: {row.get('Category', 'N/A')} | "
                    f"Quarter: {row.get('Quarter', 'N/A')}"
                )
                lead = row.get("Lead Investors", "Undisclosed")
                if lead != "Undisclosed":
                    st.write(f"Lead Investors: {lead}")
                st.markdown("---")
    with tab3:
        display_summary_table(filtered_inv, "Amount Raised", "Venture")


def create_jp_morgan_chart_by_category(category, color, selected_quarters, selected_years):
    try:
        all_data = {
            "M&A": {
                "2024": {"Q1": {"value": 18000, "count": 47}, "Q2": {"value": 40300, "count": 114}, "Q3": {"value": 47000, "count": 195}, "Q4": {"value": 63100, "count": 305}},
                "2025": {"Q1": {"value": 9200, "count": 57}, "Q2": {"value": 2100, "count": 43}, "Q3": {"value": 21700, "count": 65}, "Q4": {"value": 43500, "count": 35}},
                "2026": {"Q1": {"value": 26600, "count": 38}},
            },
            "Venture": {
                "2024": {"Q1": {"value": 5500, "count": 182}, "Q2": {"value": 4300, "count": 167}, "Q3": {"value": 5100, "count": 154}, "Q4": {"value": 3000, "count": 125}},
                "2025": {"Q1": {"value": 3700, "count": 117}, "Q2": {"value": 2600, "count": 90}, "Q3": {"value": 2900, "count": 67}},
            },
        }

        quarters, values, counts = [], [], []
        for year in selected_years:
            for quarter in selected_quarters:
                if year in all_data[category] and quarter in all_data[category][year]:
                    quarters.append(f"{quarter} {year}")
                    values.append(all_data[category][year][quarter]["value"])
                    counts.append(all_data[category][year][quarter]["count"])

        if not quarters:
            st.info("No data available for selected quarters and years")
            return None

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=quarters,
                y=[v / 1000 for v in values],
                name="Deal Value",
                marker_color=color,
                text=[format_currency_abbreviated(v * 1_000_000) for v in values],
                textposition="outside",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=quarters,
                y=counts,
                name="Deal Count",
                mode="lines+markers+text",
                text=counts,
                textposition="top center",
                yaxis="y2",
                line=dict(color=COLORS["count_line"], width=3),
            )
        )
        fig.update_layout(
            title=f"{category} Activity",
            xaxis=dict(title="Quarter", showgrid=False),
            yaxis=dict(title="Deal Value (Billions USD)", showgrid=False),
            yaxis2=dict(title="Number of Deals", overlaying="y", side="right", showgrid=False),
            hovermode="x unified",
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=350,
        )
        return fig
    except Exception as e:
        st.error(f"Error creating {category} chart: {e}")
        return None


def show_jp_morgan_summary(ma_df: pd.DataFrame, inv_df: pd.DataFrame):
    st.header("JP Morgan MedTech Industry Report")

    st.markdown("**Filters**")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_quarters = st.multiselect("Quarters", ["Q1", "Q2", "Q3", "Q4"], default=["Q1", "Q2", "Q3", "Q4"])
    with filter_col2:
        selected_years = st.multiselect("Years", ["2024", "2025", "2026"], default=["2025", "2026"])

    if not selected_quarters or not selected_years:
        st.warning("Please select at least one quarter and one year.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### M&A Activity")
        fig = create_jp_morgan_chart_by_category("M&A", COLORS["ma_primary"], selected_quarters, selected_years)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### Venture Investment")
        fig = create_jp_morgan_chart_by_category("Venture", COLORS["venture_primary"], selected_quarters, selected_years)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption("Source: JP Morgan Biopharma & MedTech Deal Reports")


def show_upload_dataset(ma_df: pd.DataFrame, inv_df: pd.DataFrame):
    st.header("📤 Upload New Dataset")

    if "upload_authenticated" not in st.session_state:
        st.session_state.upload_authenticated = False

    if not st.session_state.upload_authenticated:
        st.info("🔒 This page is password-protected. Please enter the password to continue.")
        password = st.text_input("Password", type="password", key="upload_password")
        if st.button("Submit", type="primary"):
            if password == "BeaconOne":
                st.session_state.upload_authenticated = True
                st.success("✅ Access granted!")
                st.rerun()
            st.error("❌ Incorrect password. Please try again.")
        return

    st.success("🔓 Authenticated")
    if st.button("🔒 Lock Page"):
        st.session_state.upload_authenticated = False
        st.rerun()

    st.markdown("---")
    st.markdown("### ↩️ Undo Last Upload")
    if "backup_available" not in st.session_state:
        st.session_state.backup_available = False

    if st.session_state.get("backup_available", False):
        last_backup = st.session_state.get("last_backup_time", None)
        if last_backup is not None:
            st.info(f"📦 Backup available from: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}")
        if st.button("↩️ Undo", type="primary"):
            success, message = undo_last_upload()
            if success:
                st.success(f"✅ {message}")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"❌ {message}")
    else:
        st.info("ℹ️ No backup available. Upload a file to create a backup.")

    st.markdown("---")
    st.markdown(
        """
### Instructions
1. Upload your Excel file with these sheets:
   - **YTD M&A Activity**
   - **YTD Investment Activity**
2. Choose whether to **append** new deals or **replace** all existing data
3. Click **Upload** to process the file
"""
    )

    uploaded_file = st.file_uploader("Choose Excel file", type=["xlsx", "xls"], help="Upload MedTech deals data file")

    if uploaded_file is None:
        return

    st.success(f"✅ File uploaded: {uploaded_file.name}")

    try:
        preview_ma = pd.read_excel(uploaded_file, sheet_name="YTD M&A Activity", nrows=5)
        preview_inv = pd.read_excel(uploaded_file, sheet_name="YTD Investment Activity", nrows=5)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**M&A Activity (first 5 rows)**")
            st.dataframe(preview_ma, use_container_width=True)
        with col2:
            st.markdown("**Investment Activity (first 5 rows)**")
            st.dataframe(preview_inv, use_container_width=True)

        upload_mode = st.radio(
            "How would you like to update the data?",
            ["Append new deals to existing data", "Replace all existing data"],
        )

        if st.button("📤 Upload and Process Data", type="primary", use_container_width=True):
            new_ma = normalize_dataframe(pd.read_excel(uploaded_file, sheet_name="YTD M&A Activity"), "Deal Value")
            new_inv = normalize_dataframe(pd.read_excel(uploaded_file, sheet_name="YTD Investment Activity"), "Amount Raised")

            if upload_mode == "Append new deals to existing data":
                final_ma = pd.concat([ma_df, new_ma], ignore_index=True)
                final_inv = pd.concat([inv_df, new_inv], ignore_index=True)
                final_ma = final_ma.drop_duplicates(subset=["Company", "Acquirer", "Deal Value", "Quarter"], keep="last")
                final_inv = final_inv.drop_duplicates(subset=["Company", "Amount Raised", "Quarter"], keep="last")
            else:
                final_ma = new_ma
                final_inv = new_inv

            if save_data(final_ma, final_inv):
                st.success("✅ Data uploaded successfully!")
                st.cache_data.clear()
                st.rerun()
    except Exception as e:
        st.error(f"❌ Error processing upload: {e}")
        st.info("Please ensure the file has 'YTD M&A Activity' and 'YTD Investment Activity' sheets.")


def main():
    st.title("🤝 MedTech M&A & Venture Dashboard")
    page = st.radio(
        "Navigation",
        ["🏠 Home: Start Here", "📊 Deal Activity", "📈 JP Morgan Industry Report", "📤 Upload New Dataset"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("---")

    ma_df, inv_df = load_data()

    if page == "🏠 Home: Start Here":
        show_home()
    elif page == "📊 Deal Activity":
        show_deal_activity(ma_df, inv_df)
    elif page == "📈 JP Morgan Industry Report":
        show_jp_morgan_summary(ma_df, inv_df)
    elif page == "📤 Upload New Dataset":
        show_upload_dataset(ma_df, inv_df)


if __name__ == "__main__":
    main()
