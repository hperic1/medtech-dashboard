import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="MedTech M&A & Venture Dashboard",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define color palette
COLORS = {
    'ma_primary': '#7FA8C9',      # Muted blue for M&A
    'ma_secondary': '#A8C9D1',    # Lighter muted blue
    'venture_primary': '#C9A77F',  # Muted orange/tan for Venture
    'venture_secondary': '#D9C9A8', # Lighter muted tan
    'count_line': '#90A9B0',       # Muted teal for count lines
    'accent': '#B8A690'            # Neutral accent
}

# Custom CSS for full-width tables and card styling
st.markdown("""
<style>
    .dataframe {
        width: 100% !important;
    }
    div[data-testid="stDataFrame"] > div {
        width: 100% !important;
    }
    .stDataFrame {
        width: 100%;
    }
    /* Make tables span full width */
    .element-container {
        width: 100%;
    }
    
    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #7FA8C9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .metric-card-venture {
        background: linear-gradient(135deg, #fdfbf7 0%, #ebdec2 100%);
        border-left: 4px solid #C9A77F;
    }
    
    /* Filter container styling */
    .filter-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Data loading function
@st.cache_data
def load_data():
    """Load data from Excel file"""
    try:
        # Try multiple possible file paths
        possible_paths = [
            'data/MedTech_YTD_Standardized.xlsx',
            './data/MedTech_YTD_Standardized.xlsx',
            'MedTech_YTD_Standardized.xlsx',
            'MedTech_Deals.xlsx',
            './MedTech_Deals.xlsx',
            'data/MedTech_Deals.xlsx',
            '/mnt/project/MedTech_YTD_Standardized.xlsx',
            os.path.join(os.path.dirname(__file__), 'data', 'MedTech_YTD_Standardized.xlsx'),
            os.path.join(os.path.dirname(__file__), 'MedTech_YTD_Standardized.xlsx'),
            os.path.join(os.path.dirname(__file__), 'MedTech_Deals.xlsx')
        ]
        
        excel_path = None
        for path in possible_paths:
            if os.path.exists(path):
                excel_path = path
                break
        
        if excel_path is None:
            st.error("❌ Cannot find MedTech data file. Please ensure the file is in the correct directory")
            st.info("🔍 Looking in these locations:\n" + "\n".join(f"- {p}" for p in possible_paths))
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Load M&A data
        ma_df = pd.read_excel(excel_path, sheet_name='YTD M&A Activity')
        
        # Load Investment data
        inv_df = pd.read_excel(excel_path, sheet_name='YTD Investment Activity')
        
        # Load IPO data
        try:
            ipo_df = pd.read_excel(excel_path, sheet_name='YTD IPO')
        except:
            ipo_df = pd.DataFrame()
        
        # Clean and standardize data
        ma_df = ma_df.fillna('Undisclosed')
        inv_df = inv_df.fillna('Undisclosed')
        
        # Remove unnamed columns
        ma_df = ma_df.loc[:, ~ma_df.columns.str.contains('^Unnamed')]
        inv_df = inv_df.loc[:, ~inv_df.columns.str.contains('^Unnamed')]
        if not ipo_df.empty:
            ipo_df = ipo_df.loc[:, ~ipo_df.columns.str.contains('^Unnamed')]
        
        # Strip year from Quarter column (e.g., "Q1 2025" -> "Q1")
        if 'Quarter' in ma_df.columns:
            ma_df['Quarter'] = ma_df['Quarter'].astype(str).str.extract(r'(Q[1-4])', expand=False)
            ma_df['Quarter'] = ma_df['Quarter'].fillna('Undisclosed')
        
        if 'Quarter' in inv_df.columns:
            inv_df['Quarter'] = inv_df['Quarter'].astype(str).str.extract(r'(Q[1-4])', expand=False)
            inv_df['Quarter'] = inv_df['Quarter'].fillna('Undisclosed')
        
        if not ipo_df.empty and 'Quarter' in ipo_df.columns:
            ipo_df['Quarter'] = ipo_df['Quarter'].astype(str).str.extract(r'(Q[1-4])', expand=False)
            ipo_df['Quarter'] = ipo_df['Quarter'].fillna('Undisclosed')
        
        return ma_df, inv_df, ipo_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def save_data(ma_df, inv_df, ipo_df=None):
    """Save data back to Excel file with backup for undo"""
    try:
        possible_paths = [
            'data/MedTech_YTD_Standardized.xlsx',
            './data/MedTech_YTD_Standardized.xlsx',
            'MedTech_YTD_Standardized.xlsx',
            'MedTech_Deals.xlsx',
            './MedTech_Deals.xlsx',
            os.path.join(os.path.dirname(__file__), 'data', 'MedTech_YTD_Standardized.xlsx'),
            os.path.join(os.path.dirname(__file__), 'MedTech_YTD_Standardized.xlsx')
        ]
        
        excel_path = None
        for path in possible_paths:
            if os.path.exists(path):
                excel_path = path
                break
        
        if excel_path is None:
            os.makedirs('data', exist_ok=True)
            excel_path = 'data/MedTech_YTD_Standardized.xlsx'
        
        # Create backup before saving
        backup_path = excel_path.replace('.xlsx', '_backup.xlsx')
        if os.path.exists(excel_path):
            import shutil
            shutil.copy2(excel_path, backup_path)
            st.session_state.last_backup_time = pd.Timestamp.now()
        
        # Save with correct sheet names
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer:
            ma_df.to_excel(writer, sheet_name='YTD M&A Activity', index=False)
            inv_df.to_excel(writer, sheet_name='YTD Investment Activity', index=False)
            if ipo_df is not None and not ipo_df.empty:
                ipo_df.to_excel(writer, sheet_name='YTD IPO', index=False)
        
        st.session_state.changes_made = True
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        st.warning("⚠️ Note: Streamlit Cloud has a read-only file system. Changes won't persist after app restarts.")
        return False

def create_filter_section(df, section_key, show_conference=True):
    """Create a unified filter section that returns filtered dataframe"""
    with st.container():
        st.markdown('<div class="filter-container">', unsafe_allow_html=True)
        
        # Create columns for filters
        if show_conference:
            col1, col2, col3, col4 = st.columns(4)
        else:
            col1, col2, col3 = st.columns(3)
        
        with col1:
            quarters = ['All'] + sorted([q for q in df['Quarter'].unique() if q != 'Undisclosed'])
            selected_quarter = st.selectbox("Quarter", quarters, key=f'quarter_{section_key}')
        
        with col2:
            months = ['All'] + sorted([m for m in df['Month'].unique() if m != 'Undisclosed'])
            selected_month = st.selectbox("Month", months, key=f'month_{section_key}')
        
        with col3:
            sectors = ['All'] + sorted([s for s in df['Sector'].unique() if s != 'Undisclosed'])
            selected_sector = st.selectbox("Sector", sectors, key=f'sector_{section_key}')
        
        if show_conference:
            with col4:
                conferences = ['All'] + sorted([c for c in df['Conference'].unique() if c != 'Undisclosed'])
                selected_conference = st.selectbox("Conference", conferences, key=f'conference_{section_key}')
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_quarter != 'All':
        filtered_df = filtered_df[filtered_df['Quarter'] == selected_quarter]
    if selected_month != 'All':
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]
    if selected_sector != 'All':
        filtered_df = filtered_df[filtered_df['Sector'] == selected_sector]
    if show_conference and selected_conference != 'All':
        filtered_df = filtered_df[filtered_df['Conference'] == selected_conference]
    
    return filtered_df

def format_currency(value):
    """Format currency values"""
    if pd.isna(value) or value == 'Undisclosed':
        return 'Undisclosed'
    try:
        value = float(str(value).replace('$', '').replace('B', '').replace('M', '').replace(',', ''))
        if value >= 1000:
            return f"${value/1000:.1f}B"
        elif value > 0:
            return f"${value:.0f}M"
        else:
            return 'Undisclosed'
    except:
        return str(value)

def create_metric_card(label, value, color_scheme='ma'):
    """Create a styled metric card"""
    card_class = 'metric-card' if color_scheme == 'ma' else 'metric-card metric-card-venture'
    
    return f"""
    <div class="{card_class}">
        <p style='margin: 0; font-size: 14px; color: #666; font-weight: 500;'>{label}</p>
        <p style='margin: 5px 0 0 0; font-size: 32px; font-weight: bold; color: #333;'>{value}</p>
    </div>
    """

def create_quarterly_chart(df, value_col, title, chart_type='ma', height=500):
    """Create quarterly stacked bar chart with deal count overlay"""
    try:
        # Set colors based on chart type
        bar_color = COLORS['ma_primary'] if chart_type == 'ma' else COLORS['venture_primary']
        line_color = COLORS['count_line']
        
        # Filter out 'Undisclosed' quarters for cleaner data
        df_filtered = df[df['Quarter'] != 'Undisclosed'].copy()
        
        if len(df_filtered) == 0:
            st.warning(f"No data available for {title}")
            return None
        
        # Prepare data
        quarterly_data = df_filtered.groupby('Quarter').agg({
            value_col: lambda x: sum([float(str(v).replace('$', '').replace('B', '').replace('M', '').replace(',', '')) 
                                     if v != 'Undisclosed' else 0 for v in x]),
            'Company': 'count'
        }).reset_index()
        quarterly_data.columns = ['Quarter', 'Total_Value', 'Deal_Count']
        
        # Sort quarters
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarterly_data['Quarter'] = pd.Categorical(quarterly_data['Quarter'], categories=quarter_order, ordered=True)
        quarterly_data = quarterly_data.sort_values('Quarter')
        
        # Remove any NaN quarters
        quarterly_data = quarterly_data[quarterly_data['Quarter'].notna()]
        
        if len(quarterly_data) == 0:
            st.warning(f"No valid quarterly data for {title}")
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Add bar chart for deal values
        fig.add_trace(go.Bar(
            x=quarterly_data['Quarter'].astype(str),
            y=quarterly_data['Total_Value'],
            name='Deal Value',
            marker_color=bar_color,
            text=[f"${v:,.0f}" for v in quarterly_data['Total_Value']],
            textposition='outside',
            yaxis='y',
            hovertemplate='<b>%{x}</b><br>Deal Value: $%{y:,.0f}<br><extra></extra>'
        ))
        
        # Add line chart for deal count
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'].astype(str),
            y=quarterly_data['Deal_Count'],
            name='Deal Count',
            mode='lines+markers+text',
            line=dict(color=line_color, width=3),
            marker=dict(size=10, color=line_color),
            text=quarterly_data['Deal_Count'],
            textposition='top center',
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Deal Count: %{y}<br><extra></extra>',
            connectgaps=True  # Ensure lines are connected
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color='#333')),
            xaxis=dict(title='Quarter', showgrid=False),
            yaxis=dict(
                title='Total Deal Value (USD)',
                side='left',
                showgrid=False,
                range=[0, max(quarterly_data['Total_Value']) * 1.2] if len(quarterly_data) > 0 else [0, 1000]
            ),
            yaxis2=dict(
                title='Number of Deals',
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(quarterly_data['Deal_Count']) * 1.3] if len(quarterly_data) > 0 else [0, 10]
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=height,
            margin=dict(t=100, b=50, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def create_jp_morgan_chart_by_category(category, color):
    """Create JP Morgan chart for a specific category with deal count overlay"""
    try:
        quarters = ['Q1', 'Q2', 'Q3']
        
        # Actual data from JP Morgan 2025 reports
        data_map = {
            'M&A': {
                'values': [9200, 2100, 21700],
                'counts': [57, 43, 65]
            },
            'Venture': {
                'values': [3700, 2600, 2900],
                'counts': [117, 90, 67]
            }
        }
        
        category_data = data_map.get(category, {'values': [0, 0, 0], 'counts': [0, 0, 0]})
        values = category_data['values']
        counts = category_data['counts']
        
        fig = go.Figure()
        
        # Add bars for deal values
        fig.add_trace(go.Bar(
            x=quarters,
            y=values,
            name='Deal Value ($M)',
            marker_color=color,
            text=[format_currency(v) for v in values],
            textposition='outside',
            yaxis='y',
            hovertemplate='<b>%{x}</b><br>Deal Value: %{text}<br><extra></extra>'
        ))
        
        # Add line chart for deal count
        fig.add_trace(go.Scatter(
            x=quarters,
            y=counts,
            name='Deal Count',
            mode='lines+markers+text',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line']),
            text=[str(c) if c > 0 else '' for c in counts],
            textposition='top center',
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Deal Count: %{y}<br><extra></extra>',
            connectgaps=True
        ))
        
        # Update layout with dual y-axes
        fig.update_layout(
            title=dict(text=f'{category} Activity', font=dict(size=16, color='#333')),
            xaxis=dict(title='Quarter', showgrid=False),
            yaxis=dict(
                title='Deal Value (Millions USD)',
                side='left',
                showgrid=False,
                range=[0, max(values) * 1.2]
            ),
            yaxis2=dict(
                title='Number of Deals',
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(counts) * 1.3] if max(counts) > 0 else [0, 100]
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=350,
            margin=dict(t=80, b=50, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating {category} chart: {str(e)}")
        return None

def create_sunburst_chart(df, value_col, deal_type, sector_col='Sector'):
    """Create sunburst chart showing deal values by sector"""
    try:
        # Filter out 'Undisclosed' sectors
        df_filtered = df[df[sector_col] != 'Undisclosed'].copy()
        
        if len(df_filtered) == 0:
            st.info(f"No sector data available for {deal_type}")
            return None
        
        # Parse values to numeric
        def parse_value(val):
            if val == 'Undisclosed' or pd.isna(val):
                return 0
            val_str = str(val).replace('$', '').replace('B', '').replace('M', '').replace(',', '').strip()
            try:
                return float(val_str)
            except:
                return 0
        
        # Group by sector and sum values
        sector_data = df_filtered.groupby(sector_col).agg({
            value_col: lambda x: sum([parse_value(v) for v in x])
        }).reset_index()
        sector_data.columns = ['Sector', 'Total_Value']
        
        # Remove sectors with zero value
        sector_data = sector_data[sector_data['Total_Value'] > 0]
        
        if len(sector_data) == 0:
            st.info(f"No deal value data available for {deal_type} sectors")
            return None
        
        # Sort by value descending
        sector_data = sector_data.sort_values('Total_Value', ascending=False)
        
        # Create complementary muted color palette
        if deal_type == 'M&A':
            # Muted blues and related colors
            color_palette = [
                '#7FA8C9', '#A8C9D1', '#6B8BA3', '#94B4C9', '#5A7A94',
                '#8AA9BE', '#B5D0DC', '#6F98B3', '#84A8BD', '#9BBDD1'
            ]
        else:  # Venture
            # Muted oranges, tans, and warm colors
            color_palette = [
                '#C9A77F', '#D9C9A8', '#B89968', '#CCBB99', '#A88E6C',
                '#D4BC94', '#E0D4BC', '#BEA77A', '#C8B490', '#D6C5A3'
            ]
        
        # Assign colors (cycle if more sectors than colors)
        colors = [color_palette[i % len(color_palette)] for i in range(len(sector_data))]
        
        # Format values for display
        def format_value_display(val):
            if val >= 1000000000:
                return f"${val/1000000000:.2f}B"
            elif val >= 1000000:
                return f"${val/1000000:.1f}M"
            else:
                return f"${val:,.0f}"
        
        sector_data['Value_Display'] = sector_data['Total_Value'].apply(format_value_display)
        
        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            labels=sector_data['Sector'],
            parents=[''] * len(sector_data),  # All sectors are at root level
            values=sector_data['Total_Value'],
            text=sector_data['Value_Display'],
            textinfo='label+text',
            marker=dict(colors=colors, line=dict(color='white', width=2)),
            hovertemplate='<b>%{label}</b><br>Total Value: %{text}<br>Percentage: %{percentRoot:.1%}<extra></extra>',
            branchvalues='total'
        ))
        
        # Update layout
        fig.update_layout(
            height=400,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor='white',
            showlegend=False  # Sunburst is self-labeled
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating sunburst chart: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

# Main app
def main():
    st.title("🥼 MedTech M&A & Venture Dashboard")
    
    # Horizontal navigation with emojis
    page = st.radio(
        "Navigation",
        ["📊 Deal Activity", "📈 JP Morgan Summary", "🏢 IPO Activity", "📤 Upload New Dataset"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Load data
    ma_df, inv_df, ipo_df = load_data()
    
    if page == "📊 Deal Activity":
        show_deal_activity(ma_df, inv_df)
    elif page == "📈 JP Morgan Summary":
        show_jp_morgan_summary(ma_df, inv_df)
    elif page == "🏢 IPO Activity":
        show_ipo_activity(ipo_df)
    elif page == "📤 Upload New Dataset":
        show_upload_dataset(ma_df, inv_df, ipo_df)

def show_deal_activity(ma_df, inv_df):
    """Display deal activity dashboard"""
    st.header("Deal Activity Dashboard")
    
    # Overview section with smaller charts and cards below
    st.markdown("### YTD Overview")
    
    # Two columns for overview
    col1, col2 = st.columns(2)
    
    with col1:
        # M&A Overview Chart (smaller)
        fig_ma_overview = create_quarterly_chart(ma_df, 'Deal Value', 'M&A Activity Overview', 'ma', height=350)
        if fig_ma_overview:
            st.plotly_chart(fig_ma_overview, use_container_width=True)
        
        # Calculate M&A metrics
        def parse_to_numeric(val):
            if val == 'Undisclosed' or pd.isna(val):
                return 0
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except:
                return 0
        
        total_ma_deals = len(ma_df)
        total_ma_value = sum(ma_df['Deal Value'].apply(parse_to_numeric))
        if total_ma_value >= 1000000000:
            ma_value_display = f"${total_ma_value/1000000000:.2f}B"
        elif total_ma_value >= 1000000:
            ma_value_display = f"${total_ma_value/1000000:.0f}M"
        else:
            ma_value_display = f"${total_ma_value:,.0f}"
        
        # Display metric cards
        st.markdown(create_metric_card("Total M&A Deal Value", ma_value_display, 'ma'), unsafe_allow_html=True)
        st.markdown(create_metric_card("Total M&A Deal Count", total_ma_deals, 'ma'), unsafe_allow_html=True)
        
        # M&A Sunburst Chart
        st.markdown("#### M&A Deals by Sector")
        
        # Independent quarter filter for M&A sunburst
        quarters_ma_sun = ['All'] + sorted([q for q in ma_df['Quarter'].unique() if q != 'Undisclosed'])
        selected_quarter_ma_sun = st.selectbox("Filter by Quarter", quarters_ma_sun, key='ma_sunburst_quarter')
        
        filtered_ma_sun = ma_df.copy()
        if selected_quarter_ma_sun != 'All':
            filtered_ma_sun = filtered_ma_sun[filtered_ma_sun['Quarter'] == selected_quarter_ma_sun]
        
        fig_ma_sunburst = create_sunburst_chart(filtered_ma_sun, 'Deal Value', 'M&A', 'Sector')
        if fig_ma_sunburst:
            st.plotly_chart(fig_ma_sunburst, use_container_width=True)
    
    with col2:
        # Venture Overview Chart (smaller)
        fig_inv_overview = create_quarterly_chart(inv_df, 'Amount Raised', 'Venture Investment Overview', 'venture', height=350)
        if fig_inv_overview:
            st.plotly_chart(fig_inv_overview, use_container_width=True)
        
        # Calculate Venture metrics
        total_inv_deals = len(inv_df)
        total_inv_value = sum(inv_df['Amount Raised'].apply(
            lambda x: float(x) if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else 0
        ))
        if total_inv_value >= 1000000000:
            inv_value_display = f"${total_inv_value/1000000000:.2f}B"
        elif total_inv_value >= 1000000:
            inv_value_display = f"${total_inv_value/1000000:.0f}M"
        else:
            inv_value_display = f"${total_inv_value:,.0f}"
        
        # Display metric cards
        st.markdown(create_metric_card("Total Investment Value", inv_value_display, 'venture'), unsafe_allow_html=True)
        st.markdown(create_metric_card("Total Investment Count", total_inv_deals, 'venture'), unsafe_allow_html=True)
        
        # Venture Sunburst Chart
        st.markdown("#### Venture Deals by Sector")
        
        # Independent quarter filter for Venture sunburst
        quarters_inv_sun = ['All'] + sorted([q for q in inv_df['Quarter'].unique() if q != 'Undisclosed'])
        selected_quarter_inv_sun = st.selectbox("Filter by Quarter", quarters_inv_sun, key='inv_sunburst_quarter')
        
        filtered_inv_sun = inv_df.copy()
        if selected_quarter_inv_sun != 'All':
            filtered_inv_sun = filtered_inv_sun[filtered_inv_sun['Quarter'] == selected_quarter_inv_sun]
        
        fig_inv_sunburst = create_sunburst_chart(filtered_inv_sun, 'Amount Raised', 'Venture', 'Sector')
        if fig_inv_sunburst:
            st.plotly_chart(fig_inv_sunburst, use_container_width=True)
    
    st.markdown("---")
    
    # M&A Activity Section
    st.subheader("M&A Activity")
    
    # Search box
    search_ma = st.text_input("🔍 Search M&A Deals", placeholder="Search by company, acquirer, technology...", key='search_ma')
    
    # Filters above table
    st.markdown("#### Filters")
    filtered_ma = create_filter_section(ma_df, 'ma_table', show_conference=True)
    
    # Apply search filter
    if search_ma:
        mask = filtered_ma.apply(lambda row: row.astype(str).str.contains(search_ma, case=False).any(), axis=1)
        filtered_ma = filtered_ma[mask]
    
    # Tabs for table, top deals, and charts
    tab1, tab2, tab3 = st.tabs(["📊 Table", "🏆 Top Deals", "📈 Charts"])
    
    with tab1:
        # Create display dataframe with sortable numeric values
        ma_display = filtered_ma.copy()
        
        def parse_to_numeric(val):
            if val == 'Undisclosed' or pd.isna(val):
                return -1
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except:
                return -1
        
        ma_display['_Deal_Value_Numeric'] = ma_display['Deal Value'].apply(parse_to_numeric)
        ma_display = ma_display.sort_values('_Deal_Value_Numeric', ascending=False)
        
        # Display without the numeric column and unnamed columns
        # Filter out: columns starting with '_', 'Unnamed', or empty strings
        display_cols = [col for col in ma_display.columns 
                       if not col.startswith('_') 
                       and not col.startswith('Unnamed')
                       and col.strip() != '']
        
        st.dataframe(
            ma_display[display_cols], 
            use_container_width=True,
            height=500,
            column_config={
                "Deal Value": st.column_config.TextColumn("Deal Value", help="Deal value in USD"),
            },
            hide_index=True
        )
    
    with tab2:
        # Top 3 deals with formatted values
        top_deals = filtered_ma.copy()
        top_deals['Deal_Value_Numeric'] = top_deals['Deal Value'].apply(parse_to_numeric)
        top_deals = top_deals.nlargest(3, 'Deal_Value_Numeric')
        
        for idx, row in top_deals.iterrows():
            # Format value with $ and commas
            deal_value = row['Deal Value']
            if deal_value != 'Undisclosed' and parse_to_numeric(deal_value) > 0:
                try:
                    numeric_val = parse_to_numeric(deal_value)
                    formatted_value = f"${numeric_val:,.0f}"
                except:
                    formatted_value = str(deal_value)
            else:
                formatted_value = 'Undisclosed'
            
            deal_type = row['Deal Type (Merger / Acquisition)']
            verb = "merged with" if deal_type == "Merger" else "acquired"
            
            st.markdown(f"**{row['Acquirer']} {verb} {row['Company']}**")
            st.markdown(f"<h1 style='margin-top: -10px; margin-bottom: 5px; color: {COLORS['ma_primary']};'>{formatted_value}</h1>", unsafe_allow_html=True)
            
            # Add technology description in small font
            tech_desc = str(row['Technology/Description']) if row['Technology/Description'] != 'Undisclosed' else 'No description available'
            st.markdown(f"<p style='font-size: 12px; color: #666; margin-top: 5px;'><b>Technology:</b> {tech_desc}</p>", unsafe_allow_html=True)
            
            # Add deal details
            sector = str(row['Sector']) if row['Sector'] != 'Undisclosed' else 'N/A'
            quarter = str(row['Quarter']) if row['Quarter'] != 'Undisclosed' else 'N/A'
            month = str(row['Month']) if row['Month'] != 'Undisclosed' else 'N/A'
            st.markdown(f"<p style='font-size: 11px; color: #888;'><b>Sector:</b> {sector} | <b>Quarter:</b> {quarter} | <b>Month:</b> {month}</p>", unsafe_allow_html=True)
            
            st.markdown("---")
    
    with tab3:
        st.markdown("#### Chart Filters")
        filtered_ma_chart = create_filter_section(ma_df, 'ma_chart', show_conference=True)
        
        fig = create_quarterly_chart(filtered_ma_chart, 'Deal Value', 'M&A Activity by Quarter', 'ma')
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Add spacing
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Venture Investment Activity Section
    st.subheader("Venture Investment Activity")
    
    # Search box
    search_inv = st.text_input("🔍 Search Investment Deals", placeholder="Search by company, investors, technology...", key='search_inv')
    
    # Filters above table
    st.markdown("#### Filters")
    filtered_inv = create_filter_section(inv_df, 'inv_table', show_conference=True)
    
    # Apply search filter
    if search_inv:
        mask = filtered_inv.apply(lambda row: row.astype(str).str.contains(search_inv, case=False).any(), axis=1)
        filtered_inv = filtered_inv[mask]
    
    # Tabs for table, top deals, and charts
    tab1, tab2, tab3 = st.tabs(["📊 Table", "🏆 Top Deals", "📈 Charts"])
    
    with tab1:
        # Format Amount Raised column for display
        inv_display = filtered_inv.copy()
        inv_display['_Amount_Numeric'] = inv_display['Amount Raised'].apply(
            lambda x: float(x) if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else -1
        )
        inv_display = inv_display.sort_values('_Amount_Numeric', ascending=False)
        
        # Format for display
        inv_display['Amount Raised'] = inv_display['Amount Raised'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else x
        )
        
        # Display without the numeric column and unnamed columns
        # Filter out: columns starting with '_', 'Unnamed', or empty strings
        display_cols = [col for col in inv_display.columns 
                       if not col.startswith('_') 
                       and not col.startswith('Unnamed')
                       and col.strip() != '']
        
        st.dataframe(
            inv_display[display_cols],
            use_container_width=True,
            height=500,
            column_config={
                "Amount Raised": st.column_config.TextColumn("Amount Raised", help="Investment amount in USD"),
            },
            hide_index=True
        )
    
    with tab2:
        # Top 3 deals with formatted values
        top_deals = filtered_inv.copy()
        def parse_amount_value(val):
            if val == 'Undisclosed' or pd.isna(val):
                return 0
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except:
                return 0
        
        top_deals['Amount_Numeric'] = top_deals['Amount Raised'].apply(parse_amount_value)
        top_deals = top_deals.nlargest(3, 'Amount_Numeric')
        
        for idx, row in top_deals.iterrows():
            # Format amount with $ and commas
            amount_val = row['Amount Raised']
            if pd.notna(amount_val) and amount_val != 'Undisclosed':
                try:
                    formatted_value = f"${float(amount_val):,.0f}"
                except:
                    formatted_value = str(amount_val)
            else:
                formatted_value = "Undisclosed"
            
            st.markdown(f"**{row['Company']}**")
            st.markdown(f"<h1 style='margin-top: -10px; margin-bottom: 5px; color: {COLORS['venture_primary']};'>{formatted_value}</h1>", unsafe_allow_html=True)
            
            # Add technology description in small font
            tech_desc = str(row['Technology/Description']) if row['Technology/Description'] != 'Undisclosed' else 'No description available'
            st.markdown(f"<p style='font-size: 12px; color: #666; margin-top: 5px;'><b>Technology:</b> {tech_desc}</p>", unsafe_allow_html=True)
            
            # Add deal details
            funding_type = str(row['Funding type (VC / PE)']) if row['Funding type (VC / PE)'] != 'Undisclosed' else 'N/A'
            sector = str(row['Sector']) if row['Sector'] != 'Undisclosed' else 'N/A'
            lead_investors = str(row['Lead Investors']) if row['Lead Investors'] != 'Undisclosed' else 'N/A'
            quarter = str(row['Quarter']) if row['Quarter'] != 'Undisclosed' else 'N/A'
            st.markdown(f"<p style='font-size: 11px; color: #888;'><b>Type:</b> {funding_type} | <b>Sector:</b> {sector} | <b>Quarter:</b> {quarter}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 11px; color: #888;'><b>Lead Investors:</b> {lead_investors}</p>", unsafe_allow_html=True)
            
            st.markdown("---")
    
    with tab3:
        st.markdown("#### Chart Filters")
        filtered_inv_chart = create_filter_section(inv_df, 'inv_chart', show_conference=True)
        
        fig = create_quarterly_chart(filtered_inv_chart, 'Amount Raised', 'Venture Investment by Quarter', 'venture')
        if fig:
            st.plotly_chart(fig, use_container_width=True)

def show_jp_morgan_summary(ma_df, inv_df):
    """Display JP Morgan summary"""
    st.header("JP Morgan MedTech Industry Report")
    
    # Calculate BeaconOne quarterly stats
    def calc_quarterly_stats(df, quarter, value_col):
        q_data = df[df['Quarter'] == quarter]
        
        def parse_value(val):
            if val == 'Undisclosed' or pd.isna(val):
                return 0
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except:
                return 0
        
        total_value = sum(q_data[value_col].apply(parse_value))
        count = len(q_data)
        
        if total_value >= 1000000000:
            formatted_value = f"${total_value/1000000000:.1f}B"
        elif total_value >= 1000000:
            formatted_value = f"${total_value/1000000:.0f}M"
        else:
            formatted_value = "$0"
            
        return count, formatted_value
    
    # Calculate stats for each quarter
    beacon_stats = {}
    for q in ['Q1', 'Q2', 'Q3']:
        ma_count, ma_value = calc_quarterly_stats(ma_df, q, 'Deal Value')
        inv_count, inv_value = calc_quarterly_stats(inv_df, q, 'Amount Raised')
        beacon_stats[q] = {
            'ma_count': ma_count,
            'ma_value': ma_value,
            'inv_count': inv_count,
            'inv_value': inv_value
        }
    
    st.markdown("### 2025 Q1-Q3 Activity by Category")
    
    # Create 1x2 grid for charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_ma = create_jp_morgan_chart_by_category('M&A', COLORS['ma_primary'])
        if fig_ma:
            st.plotly_chart(fig_ma, use_container_width=True)
    
    with col2:
        fig_venture = create_jp_morgan_chart_by_category('Venture', COLORS['venture_primary'])
        if fig_venture:
            st.plotly_chart(fig_venture, use_container_width=True)
    
    # Key trends
    st.markdown("---")
    st.subheader("Key Market Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(create_metric_card("M&A Activity", "Strategic Consolidation", 'ma'), unsafe_allow_html=True)
        st.markdown("""
        • **Q1 2025**: 57 medtech M&A deals were announced, totaling $9.2 billion
        
        • **Q2 2025**: 43 medtech M&A deals were announced, totaling $2.1 billion
        
        • **Q3 2025**: 65 medtech M&A deals were announced, totaling $21.7 billion in upfront cash and equity
        
        **Overarching Trend**: Medtech M&A activity increased through Q3 2025, surpassing full-year 2024 numbers, with strategic consolidation driving large-scale transactions
        """)
        
    with col2:
        st.markdown(create_metric_card("Venture Capital", "Selective Investment", 'venture'), unsafe_allow_html=True)
        st.markdown("""
        • **Q1 2025**: Medtech venture investment activity continued to see larger rounds into fewer companies to post a higher dollar total for Q1 2025, exceeding Q1 2024
        
        • **Q2 2025**: The medtech venture landscape continues to show resilience, with total venture funding reaching $6.8 billion in the first half of 2025, positioning the sector to potentially exceed 2024's $12.7 billion full-year total
        
        • **Q3 2025**: Medtech venture funding started the year strong yet had a weaker Q2 and Q3 in a challenging venture funding environment across all of healthcare and life sciences
        
        **Overarching Trend**: Late-stage venture rounds continue to dominate at $7.9B YTD, while early-stage funding remains selective as investors focus on companies with proven traction
        """)

    # Add comparison section
    st.markdown("---")
    st.markdown("### JPMorgan vs BeaconOne Data - Quarterly Comparison")
    
    # Create three columns for Q1, Q2, Q3
    q1_col, q2_col, q3_col = st.columns(3)
    
    for col, quarter, ma_color, inv_color in [
        (q1_col, 'Q1', '#4A90E2', '#50C878'),
        (q2_col, 'Q2', '#4A90E2', '#50C878'),
        (q3_col, 'Q3', '#9B59B6', '#50C878')
    ]:
        with col:
            st.markdown(f"#### {quarter} 2025")
            
            # JP Morgan data
            jp_ma_count = {'Q1': 57, 'Q2': 43, 'Q3': 65}[quarter]
            jp_ma_value = {'Q1': '$9.2B', 'Q2': '$2.1B', 'Q3': '$21.7B'}[quarter]
            jp_inv_count = {'Q1': 117, 'Q2': 90, 'Q3': 67}[quarter]
            jp_inv_value = {'Q1': '$3.7B', 'Q2': '$2.6B', 'Q3': '$2.9B'}[quarter]
            
            st.markdown(f"""
            <div style='background-color: {ma_color}; padding: 20px; border-radius: 10px; margin-bottom: 10px;'>
                <p style='color: white; margin: 0; font-size: 12px;'>M&A Deal Count</p>
                <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                    <div>
                        <p style='color: white; margin: 0; font-size: 10px;'>JPMorgan</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{jp_ma_count}</p>
                    </div>
                    <div style='text-align: right;'>
                        <p style='color: white; margin: 0; font-size: 10px;'>BeaconOne</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{beacon_stats[quarter]['ma_count']}</p>
                    </div>
                </div>
            </div>
            <div style='background-color: {ma_color}; opacity: 0.8; padding: 20px; border-radius: 10px; margin-bottom: 10px;'>
                <p style='color: white; margin: 0; font-size: 12px;'>M&A Deal Value</p>
                <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                    <div>
                        <p style='color: white; margin: 0; font-size: 10px;'>JPMorgan</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{jp_ma_value}</p>
                    </div>
                    <div style='text-align: right;'>
                        <p style='color: white; margin: 0; font-size: 10px;'>BeaconOne</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{beacon_stats[quarter]['ma_value']}</p>
                    </div>
                </div>
            </div>
            <div style='background-color: {inv_color}; padding: 20px; border-radius: 10px; margin-bottom: 10px;'>
                <p style='color: white; margin: 0; font-size: 12px;'>Investment Count</p>
                <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                    <div>
                        <p style='color: white; margin: 0; font-size: 10px;'>JPMorgan</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{jp_inv_count}</p>
                    </div>
                    <div style='text-align: right;'>
                        <p style='color: white; margin: 0; font-size: 10px;'>BeaconOne</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{beacon_stats[quarter]['inv_count']}</p>
                    </div>
                </div>
            </div>
            <div style='background-color: {inv_color}; opacity: 0.8; padding: 20px; border-radius: 10px;'>
                <p style='color: white; margin: 0; font-size: 12px;'>Investment Value</p>
                <div style='display: flex; justify-content: space-between; align-items: baseline;'>
                    <div>
                        <p style='color: white; margin: 0; font-size: 10px;'>JPMorgan</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{jp_inv_value}</p>
                    </div>
                    <div style='text-align: right;'>
                        <p style='color: white; margin: 0; font-size: 10px;'>BeaconOne</p>
                        <p style='color: white; margin: 0; font-size: 32px; font-weight: bold;'>{beacon_stats[quarter]['inv_value']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_ipo_activity(ipo_df):
    """Display IPO activity"""
    st.header("IPO Activity - YTD 2025")
    
    if ipo_df.empty:
        st.info("No IPO data available")
        return
    
    # Search and filters
    search_ipo = st.text_input("🔍 Search IPOs", placeholder="Search by company, type, technology...", key='search_ipo')
    
    st.markdown("#### Filters")
    filtered_ipo = ipo_df.copy()
    
    col1, col2 = st.columns(2)
    with col1:
        quarters = ['All'] + sorted([q for q in ipo_df['Quarter'].unique() if pd.notna(q)])
        selected_quarter = st.selectbox("Quarter", quarters, key='ipo_quarter')
        if selected_quarter != 'All':
            filtered_ipo = filtered_ipo[filtered_ipo['Quarter'] == selected_quarter]
    
    with col2:
        types = ['All'] + sorted([t for t in ipo_df['Type'].unique() if pd.notna(t)])
        selected_type = st.selectbox("Type", types, key='ipo_type')
        if selected_type != 'All':
            filtered_ipo = filtered_ipo[filtered_ipo['Type'] == selected_type]
    
    # Apply search
    if search_ipo:
        mask = filtered_ipo.apply(lambda row: row.astype(str).str.contains(search_ipo, case=False).any(), axis=1)
        filtered_ipo = filtered_ipo[mask]
    
    # Display metrics
    total_ipos = len(filtered_ipo)
    st.markdown(create_metric_card("Total IPOs YTD", total_ipos, 'ma'), unsafe_allow_html=True)
    
    # Display table
    st.dataframe(filtered_ipo, use_container_width=True, height=500, hide_index=True)

def show_upload_dataset(ma_df, inv_df, ipo_df):
    """Password-protected data upload page"""
    st.header("📤 Upload New Dataset")
    
    # Password protection
    if 'upload_authenticated' not in st.session_state:
        st.session_state.upload_authenticated = False
    
    if not st.session_state.upload_authenticated:
        st.info("🔒 This page is password-protected. Please enter the password to continue.")
        
        password = st.text_input("Password", type="password", key="upload_password")
        
        if st.button("Submit", type="primary"):
            if password == "BeaconOne":
                st.session_state.upload_authenticated = True
                st.success("✅ Access granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
        
        return
    
    # Show upload interface after authentication
    st.success("🔓 Authenticated")
    
    if st.button("🔒 Lock Page", type="secondary"):
        st.session_state.upload_authenticated = False
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("""
    ### Instructions
    1. Upload your Excel file with the following sheets:
       - **YTD M&A Activity**
       - **YTD Investment Activity** 
       - **YTD IPO** (optional)
    2. Choose whether to **append** new deals or **replace** all existing data
    3. Click **Upload** to process the file
    4. **Refresh the page** to see updated data
    """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose Excel file",
        type=['xlsx', 'xls'],
        help="Upload MedTech deals data file"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Preview uploaded data
        try:
            preview_ma = pd.read_excel(uploaded_file, sheet_name='YTD M&A Activity', nrows=5)
            preview_inv = pd.read_excel(uploaded_file, sheet_name='YTD Investment Activity', nrows=5)
            
            st.markdown("### Preview")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**M&A Activity (first 5 rows)**")
                st.dataframe(preview_ma, use_container_width=True)
            
            with col2:
                st.markdown("**Investment Activity (first 5 rows)**")
                st.dataframe(preview_inv, use_container_width=True)
            
            # Upload options
            st.markdown("---")
            st.markdown("### Upload Options")
            
            upload_mode = st.radio(
                "How would you like to update the data?",
                ["Append new deals to existing data", "Replace all existing data"],
                help="Append will add new deals to current data. Replace will overwrite everything."
            )
            
            if st.button("📤 Upload and Process Data", type="primary", use_container_width=True):
                with st.spinner("Processing upload..."):
                    try:
                        # Read full datasets
                        new_ma = pd.read_excel(uploaded_file, sheet_name='YTD M&A Activity')
                        new_inv = pd.read_excel(uploaded_file, sheet_name='YTD Investment Activity')
                        
                        try:
                            new_ipo = pd.read_excel(uploaded_file, sheet_name='YTD IPO')
                        except:
                            new_ipo = ipo_df  # Keep existing if not in upload
                        
                        # Clean data
                        new_ma = new_ma.fillna('Undisclosed')
                        new_inv = new_inv.fillna('Undisclosed')
                        
                        # Remove unnamed columns
                        new_ma = new_ma.loc[:, ~new_ma.columns.str.contains('^Unnamed')]
                        new_inv = new_inv.loc[:, ~new_inv.columns.str.contains('^Unnamed')]
                        if not new_ipo.empty:
                            new_ipo = new_ipo.loc[:, ~new_ipo.columns.str.contains('^Unnamed')]
                        
                        # Strip year from Quarter column
                        if 'Quarter' in new_ma.columns:
                            new_ma['Quarter'] = new_ma['Quarter'].astype(str).str.extract(r'(Q[1-4])', expand=False)
                            new_ma['Quarter'] = new_ma['Quarter'].fillna('Undisclosed')
                        
                        if 'Quarter' in new_inv.columns:
                            new_inv['Quarter'] = new_inv['Quarter'].astype(str).str.extract(r'(Q[1-4])', expand=False)
                            new_inv['Quarter'] = new_inv['Quarter'].fillna('Undisclosed')
                        
                        if not new_ipo.empty and 'Quarter' in new_ipo.columns:
                            new_ipo['Quarter'] = new_ipo['Quarter'].astype(str).str.extract(r'(Q[1-4])', expand=False)
                            new_ipo['Quarter'] = new_ipo['Quarter'].fillna('Undisclosed')
                        
                        if upload_mode == "Append new deals to existing data":
                            # Append mode - combine old and new
                            final_ma = pd.concat([ma_df, new_ma], ignore_index=True)
                            final_inv = pd.concat([inv_df, new_inv], ignore_index=True)
                            
                            # Remove duplicates based on key columns
                            final_ma = final_ma.drop_duplicates(subset=['Company', 'Acquirer', 'Deal Value'], keep='last')
                            final_inv = final_inv.drop_duplicates(subset=['Company', 'Amount Raised'], keep='last')
                            
                            st.info(f"📊 Added {len(final_ma) - len(ma_df)} new M&A deals and {len(final_inv) - len(inv_df)} new investment deals")
                        else:
                            # Replace mode - use only new data
                            final_ma = new_ma
                            final_inv = new_inv
                            st.info(f"📊 Replaced data: {len(final_ma)} M&A deals, {len(final_inv)} investment deals")
                        
                        # Save to file
                        if save_data(final_ma, final_inv, new_ipo):
                            st.success("✅ Data uploaded successfully!")
                            st.balloons()
                            st.markdown("---")
                            st.markdown("### ⚠️ Important: Please refresh the page to see updated data")
                            st.markdown("Press **R** or click the refresh button in your browser")
                        
                    except Exception as e:
                        st.error(f"❌ Error processing upload: {str(e)}")
                        st.info("Make sure your Excel file has the correct sheet names and column structure")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please ensure the file has 'YTD M&A Activity' and 'YTD Investment Activity' sheets")

if __name__ == "__main__":
    main()