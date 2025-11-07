import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="MedTech M&A & Venture Dashboard",
    page_icon="🤝",
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
    
    /* Ensure all text in markdown sections is black */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        color: #000000 !important;
    }
    
    /* Ensure consistent font family */
    .stMarkdown * {
        font-family: "Source Sans Pro", sans-serif !important;
    }
    
    /* Bold table headers */
    .dataframe thead th {
        font-weight: bold !important;
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
    """Create unified filter section that returns filtered dataframe"""
    if df.empty:
        return df
    
    # Get unique values for filters
    quarters = ['All'] + sorted([q for q in df['Quarter'].unique() if q != 'Undisclosed'])
    months = ['All'] + sorted([m for m in df['Month'].unique() if m != 'Undisclosed'])
    
    # Check if Sector and Conference columns exist
    has_sector = 'Sector' in df.columns
    has_conference = 'Conference' in df.columns and show_conference
    
    if has_sector:
        sectors = ['All'] + sorted([s for s in df['Sector'].unique() if s != 'Undisclosed'])
    
    if has_conference:
        conferences = ['All'] + sorted([c for c in df['Conference'].unique() if c != 'Undisclosed'])
    
    # Create filter layout
    filter_cols = st.columns(4 if has_conference else 3)
    
    with filter_cols[0]:
        selected_quarter = st.selectbox("Filter by Quarter", quarters, key=f'{section_key}_quarter')
    
    with filter_cols[1]:
        selected_month = st.selectbox("Filter by Month", months, key=f'{section_key}_month')
    
    if has_sector:
        with filter_cols[2]:
            selected_sector = st.selectbox("Filter by Sector", sectors, key=f'{section_key}_sector')
    
    if has_conference:
        with filter_cols[3 if has_sector else 2]:
            selected_conference = st.selectbox("Filter by Conference", conferences, key=f'{section_key}_conference')
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_quarter != 'All':
        filtered_df = filtered_df[filtered_df['Quarter'] == selected_quarter]
    
    if selected_month != 'All':
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]
    
    if has_sector and selected_sector != 'All':
        filtered_df = filtered_df[filtered_df['Sector'] == selected_sector]
    
    if has_conference and selected_conference != 'All':
        filtered_df = filtered_df[filtered_df['Conference'] == selected_conference]
    
    return filtered_df

def format_currency_abbreviated(value):
    """Format currency values in abbreviated form (e.g., $2.1B, $350M)"""
    if pd.isna(value) or value == 'Undisclosed':
        return 'Undisclosed'
    try:
        value = float(str(value).replace('$', '').replace('B', '').replace('M', '').replace(',', ''))
        if value >= 1000000000:
            return f"${value/1000000000:.1f}B"
        elif value >= 1000000:
            return f"${value/1000000:.0f}M"
        else:
            return 'Undisclosed'
    except:
        return str(value)

def create_quarterly_chart(df, value_col, title, chart_type='ma'):
    """Create quarterly stacked bar chart with deal count overlay - with muted colors and no gridlines"""
    try:
        # Check if dataframe is empty or column doesn't exist
        if df.empty or value_col not in df.columns:
            st.warning(f"No data available for {title}")
            return None
        
        # Prepare data
        def parse_value(val):
            if pd.isna(val) or val == 'Undisclosed' or val == '' or val is None:
                return 0
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except (ValueError, TypeError, AttributeError):
                return 0
        
        # Group by quarter
        quarterly_data = df.groupby('Quarter').agg({
            value_col: lambda x: sum([parse_value(v) for v in x]),
            'Company': 'count'
        }).reset_index()
        quarterly_data.columns = ['Quarter', 'Total_Value', 'Deal_Count']
        
        # Sort quarters
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarterly_data['Quarter'] = pd.Categorical(quarterly_data['Quarter'], categories=quarter_order, ordered=True)
        quarterly_data = quarterly_data.sort_values('Quarter')
        
        # Remove any rows where Quarter is 'Undisclosed'
        quarterly_data = quarterly_data[quarterly_data['Quarter'] != 'Undisclosed']
        
        # Check if we have any data after filtering
        if quarterly_data.empty:
            st.warning(f"No quarterly data available for {title}")
            return None
        
        # Create figure with colors based on chart type
        fig = go.Figure()
        
        # Select color based on chart type
        bar_color = COLORS['ma_primary'] if chart_type == 'ma' else COLORS['venture_primary']
        
        # Add bar chart for deal values
        fig.add_trace(go.Bar(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Total_Value'],
            name='Deal Value',
            marker_color=bar_color,
            text=[format_currency_abbreviated(v) for v in quarterly_data['Total_Value']],
            textposition='outside',
            textfont=dict(size=14, color='#333'),
            yaxis='y',
            hovertemplate='<b>%{x}</b><br>Deal Value: %{text}<br><extra></extra>'
        ))
        
        # Add line chart for deal count
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Deal_Count'],
            name='Deal Count',
            mode='lines+markers+text',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line']),
            text=quarterly_data['Deal_Count'],
            textposition='top center',
            textfont=dict(size=14, color='#333'),
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Deal Count: %{y}<br><extra></extra>'
        ))
        
        # Update layout with modern styling
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333', family='Arial, sans-serif')),
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),
                showgrid=False,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(text='Total Deal Value (USD)', font=dict(size=16)),
                side='left',
                showgrid=False,
                range=[0, max(quarterly_data['Total_Value']) * 1.35] if len(quarterly_data) > 0 else [0, 1000],
                tickfont=dict(size=13)
            ),
            yaxis2=dict(
                title=dict(text='Number of Deals', font=dict(size=16)),
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(quarterly_data['Deal_Count']) * 1.5] if len(quarterly_data) > 0 else [0, 10],
                tickfont=dict(size=13)
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=13)
            ),
            height=450,
            margin=dict(t=100, b=50, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=13, family='Arial, sans-serif')
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def create_comparison_mini_chart(metric_name, jp_value, beacon_value, color, height=120):
    """Create mini bar chart comparing JP Morgan and BeaconOne data with REDUCED height for better fit"""
    try:
        # Parse values for comparison
        def parse_for_display(val):
            """Just return the value as-is for display"""
            return str(val)
        
        # Display values
        jp_display = parse_for_display(jp_value)
        beacon_display = parse_for_display(beacon_value)
        
        # Create figure
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            x=['JPMorgan', 'BeaconOne'],
            y=[1, 1],  # Equal heights for visual comparison
            text=[jp_display, beacon_display],
            textposition='inside',
            textfont=dict(size=16, color='white', family='Arial Black, sans-serif'),
            marker_color=color,
            hovertemplate='<b>%{x}</b><br>' + metric_name + ': %{text}<br><extra></extra>',
            showlegend=False
        ))
        
        # Update layout - REDUCED padding and margins
        fig.update_layout(
            title=dict(
                text=f'<b>{metric_name}</b>',
                font=dict(size=11, color='#333', family='Arial, sans-serif'),
                x=0.5,
                xanchor='center',
                y=0.98,
                yanchor='top'
            ),
            xaxis=dict(
                showticklabels=True,
                tickfont=dict(size=10),
                showgrid=False
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                range=[0, 1.1]
            ),
            height=height,  # Use the passed height parameter (now 120 instead of 140)
            margin=dict(t=25, b=20, l=5, r=5),  # Reduced margins
            plot_bgcolor='white',
            paper_bgcolor='white',
            hovermode='x'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating mini chart: {str(e)}")
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
            text=[format_currency_abbreviated(v) for v in values],
            textposition='outside',
            textfont=dict(size=14, color='#333'),
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
            textfont=dict(size=14, color='#333'),
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Deal Count: %{y}<br><extra></extra>'
        ))
        
        # Update layout with dual y-axes
        fig.update_layout(
            title=dict(text=f'{category} Activity', font=dict(size=20, color='#333', family='Arial, sans-serif')),
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),
                showgrid=False,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(text='Deal Value (Millions USD)', font=dict(size=16)),
                side='left',
                showgrid=False,
                range=[0, max(values) * 1.35],
                tickfont=dict(size=13)
            ),
            yaxis2=dict(
                title=dict(text='Number of Deals', font=dict(size=16)),
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(counts) * 1.5] if max(counts) > 0 else [0, 100],
                tickfont=dict(size=13)
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=13)
            ),
            height=350,
            margin=dict(t=80, b=50, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=13, family='Arial, sans-serif')
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating {category} chart: {str(e)}")
        return None

def create_metric_card(title, subtitle, card_type='ma'):
    """Create a styled metric card"""
    card_class = 'metric-card' if card_type == 'ma' else 'metric-card metric-card-venture'
    return f"""
    <div class="{card_class}">
        <h3 style="margin: 0 0 5px 0; color: #333; font-size: 18px; font-weight: bold;">{title}</h3>
        <p style="margin: 0; color: #666; font-size: 14px;">{subtitle}</p>
    </div>
    """

# Main app
def main():
    st.title("🤝 MedTech M&A & Venture Dashboard")
    
    # Load data
    ma_df, inv_df, ipo_df = load_data()
    
    # Horizontal navigation using tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Home",
        "📊 Deals",
        "📈 JP Morgan",
        "💼 IPO",
        "📤 Upload"
    ])
    
    with tab1:
        show_home(ma_df, inv_df, ipo_df)
    
    with tab2:
        show_deal_activity(ma_df, inv_df)
    
    with tab3:
        show_jp_morgan_summary(ma_df, inv_df)
    
    with tab4:
        show_ipo_activity(ipo_df)
    
    with tab5:
        show_upload_dataset(ma_df, inv_df, ipo_df)

def show_home(ma_df, inv_df, ipo_df):
    """Display home page with overview"""
    st.header("Welcome to the MedTech Dashboard")
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total M&A Deals", len(ma_df) if not ma_df.empty else 0)
    
    with col2:
        st.metric("Total Venture Deals", len(inv_df) if not inv_df.empty else 0)
    
    with col3:
        st.metric("Total IPOs", len(ipo_df) if not ipo_df.empty else 0)
    
    st.markdown("---")
    
    # Quick charts
    st.subheader("2025 Year-to-Date Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not ma_df.empty:
            fig_ma = create_quarterly_chart(ma_df, 'Deal Value', 'M&A Activity Overview', 'ma')
            if fig_ma:
                st.plotly_chart(fig_ma, use_container_width=True)
    
    with col2:
        if not inv_df.empty:
            fig_inv = create_quarterly_chart(inv_df, 'Amount Raised', 'Venture Investment Overview', 'venture')
            if fig_inv:
                st.plotly_chart(fig_inv, use_container_width=True)

def show_deal_activity(ma_df, inv_df):
    """Display deal activity dashboard"""
    st.header("Deal Activity Dashboard")
    
    # M&A Activity Section
    st.subheader("M&A Activity")
    
    # Search box
    search_ma = st.text_input("🔍 Search M&A Deals", placeholder="Search by company, acquirer, technology...", key='search_ma')
    
    # Create filter section
    st.markdown("#### Filters")
    filtered_ma = create_filter_section(ma_df, 'ma', show_conference=True)
    
    # Apply search filter
    if search_ma:
        mask = filtered_ma.apply(lambda row: row.astype(str).str.contains(search_ma, case=False).any(), axis=1)
        filtered_ma = filtered_ma[mask]
    
    # Tabs for table, top deals, and charts
    tab1, tab2, tab3 = st.tabs(["📊 Table", "🏆 Top Deals", "📈 Charts"])
    
    with tab1:
        # Create display dataframe with sortable numeric values
        ma_display = filtered_ma.copy()
        
        # Add hidden numeric column for sorting
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
        
        # Format Deal Value for display
        ma_display['Deal Value'] = ma_display['Deal Value'].apply(
            lambda x: format_currency_abbreviated(float(x)) if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else x
        )
        
        # Display without the numeric column
        display_cols = [col for col in ma_display.columns if not col.startswith('_')]
        
        # Create column config to bold headers
        column_config = {col: st.column_config.TextColumn(col, help=f"{col}") for col in display_cols}
        
        st.dataframe(
            ma_display[display_cols],
            use_container_width=True,
            height=400,
            column_config=column_config
        )
    
    with tab2:
        # Top 3 deals
        top_deals = filtered_ma.copy()
        
        def parse_deal_value(val):
            if val == 'Undisclosed' or pd.isna(val):
                return 0
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except:
                return 0
        
        top_deals['Deal_Value_Numeric'] = top_deals['Deal Value'].apply(parse_deal_value)
        top_deals = top_deals.nlargest(3, 'Deal_Value_Numeric')
        
        for idx, row in top_deals.iterrows():
            # Format value
            formatted_value = format_currency_abbreviated(row['Deal Value'])
            
            # Get deal type verb
            deal_type = row['Deal Type (Merger / Acquisition)']
            verb = "merged with" if deal_type == "Merger" else "acquired"
            
            st.markdown(f"**{row['Acquirer']} {verb} {row['Company']}**")
            st.markdown(f"<h1 style='margin-top: -10px; margin-bottom: 5px; color: {COLORS['ma_primary']};'>{formatted_value}</h1>", unsafe_allow_html=True)
            
            # Add technology description
            tech_desc = str(row['Technology/Description']) if row['Technology/Description'] != 'Undisclosed' else 'No description available'
            st.markdown(f"<p style='font-size: 12px; color: #666; margin-top: 5px;'><b>Technology:</b> {tech_desc}</p>", unsafe_allow_html=True)
            
            # Add deal details
            sector = str(row['Sector']) if row['Sector'] != 'Undisclosed' else 'N/A'
            quarter = str(row['Quarter']) if row['Quarter'] != 'Undisclosed' else 'N/A'
            st.markdown(f"<p style='font-size: 11px; color: #888;'><b>Sector:</b> {sector} | <b>Quarter:</b> {quarter}</p>", unsafe_allow_html=True)
            
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
    
    # Create filter section
    st.markdown("#### Filters")
    filtered_inv = create_filter_section(inv_df, 'inv', show_conference=True)
    
    # Apply search filter
    if search_inv:
        mask = filtered_inv.apply(lambda row: row.astype(str).str.contains(search_inv, case=False).any(), axis=1)
        filtered_inv = filtered_inv[mask]
    
    # Tabs for table, top deals, and charts
    tab1, tab2, tab3 = st.tabs(["📊 Table", "🏆 Top Deals", "📈 Charts"])
    
    with tab1:
        # Format Amount Raised column for display
        inv_display = filtered_inv.copy()
        
        # Add numeric sort column
        inv_display['_Amount_Numeric'] = inv_display['Amount Raised'].apply(
            lambda x: float(x) if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else -1
        )
        
        inv_display = inv_display.sort_values('_Amount_Numeric', ascending=False)
        
        # Format for display
        inv_display['Amount Raised'] = inv_display['Amount Raised'].apply(
            lambda x: format_currency_abbreviated(float(x)) if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else x
        )
        
        # Display without the numeric column
        display_cols = [col for col in inv_display.columns if not col.startswith('_')]
        
        # Create column config to bold headers
        column_config = {col: st.column_config.TextColumn(col, help=f"{col}") for col in display_cols}
        
        st.dataframe(
            inv_display[display_cols],
            use_container_width=True,
            height=400,
            column_config=column_config
        )
    
    with tab2:
        # Top 3 deals
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
            # Format amount - use abbreviated format for display (e.g., $2.1B)
            amount_val = row['Amount Raised']
            if pd.notna(amount_val) and amount_val != 'Undisclosed':
                try:
                    formatted_value = format_currency_abbreviated(float(amount_val))
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
        try:
            if df.empty or value_col not in df.columns:
                return 0, "$0"
                
            q_data = df[df['Quarter'] == quarter]
            
            if q_data.empty:
                return 0, "$0"
            
            def parse_value(val):
                if pd.isna(val) or val == 'Undisclosed' or val == '' or val is None:
                    return 0
                val_str = str(val).replace('$', '').replace(',', '').strip()
                try:
                    return float(val_str)
                except (ValueError, TypeError, AttributeError):
                    return 0
            
            try:
                total_value = sum(q_data[value_col].apply(parse_value))
            except Exception:
                total_value = 0
                
            count = len(q_data)
            
            if total_value >= 1000000000:
                formatted_value = f"${total_value/1000000000:.1f}B"
            elif total_value >= 1000000:
                formatted_value = f"${total_value/1000000:.0f}M"
            else:
                formatted_value = "$0"
                
            return count, formatted_value
            
        except Exception as e:
            print(f"Error in calc_quarterly_stats: {e}")
            return 0, "$0"
    
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
    
    # ====== QUARTERLY COMPARISON TABLE WITH KEY TRENDS ======
    st.markdown("---")
    st.markdown("### Quarterly Comparison")
    
    # Create two-column layout: table on left, key trends on right
    table_col, trends_col = st.columns([2, 1])
    
    with table_col:
        # Create comparison dataframe with M&A first, Venture second
        comparison_data = {
            'Quarter': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024', 'Q1 2025', 'Q2 2025', 'Q3 2025'],
            'M&A ($B)': [18.0, 40.3, 47.0, 63.1, 9.2, 2.1, 21.7],
            'M&A QoQ Change': ['None', '↑124%', '↑16.6%', '↑34.3%', '↓85.4%', '↓77.2%', '↑933%'],
            'M&A YoY Change': ['None', 'None', 'None', '↑34%', '↓49%', '↓94.8%', '↓53.8%'],
            'Venture ($B)': [5.5, 4.3, 5.1, 3.0, 3.7, 2.6, 2.9],
            'Venture QoQ Change': ['None', '↓21.8%', '↑18.6%', '↓41.2%', '↑23.3%', '↓29.7%', '↑11.5%'],
            'Venture YoY Change': ['None', 'None', '↑27%', '↑12%', '↓32.7%', '↓39.5%', '↓43.1%']
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Function to color-code cells
        def color_delta_cells(val):
            """Color code ONLY significant changes (≥50%), leave others black"""
            if val == 'None' or pd.isna(val):
                return 'color: #000000'
            
            if '↑' in str(val):
                pct = float(str(val).replace('↑', '').replace('%', ''))
                if pct >= 50:
                    return 'color: #00A86B; font-weight: bold'
                else:
                    return 'color: #000000'
            elif '↓' in str(val):
                pct = float(str(val).replace('↓', '').replace('%', ''))
                if pct >= 50:
                    return 'color: #D85252; font-weight: bold'
                else:
                    return 'color: #000000'
            
            return 'color: #000000'
        
        # Apply styling
        styled_df = comparison_df.style.applymap(
            color_delta_cells,
            subset=['M&A QoQ Change', 'M&A YoY Change', 'Venture QoQ Change', 'Venture YoY Change']
        ).set_properties(**{
            'text-align': 'center',
            'font-size': '13px',
            'border': '1px solid #ddd'
        }).set_table_styles([
            {'selector': 'th', 'props': [('font-weight', 'bold'), ('text-align', 'center'), ('background-color', '#f0f2f6'), ('border', '1px solid #ddd')]},
            {'selector': 'td', 'props': [('border', '1px solid #ddd')]}
        ])
        
        st.dataframe(styled_df, use_container_width=True, height=350)
    
    with trends_col:
        st.markdown("#### Key Overall Trends")
        st.markdown("""
        <div style="font-size: 13px; color: #000; line-height: 1.5;">
        <b>EOY 2024:</b><br>
        M&A ended the year at $168.4B (2,256 deals), up 34% YoY. Venture reached $19.1B (691 rounds), up 12% YoY. Large-cap consolidation and selective late-stage funding dominated activity.
        <br><br>
        <b>YTD 2025:</b><br>
        M&A totals $33B (165 deals) through Q3, led by Waters' $17.5B BD merger. Venture stands at $9.5B (259 rounds), down from 2024's pace, with investors favoring proven assets amid macro headwinds.
        </div>
        """, unsafe_allow_html=True)
    
    # Key trends section
    st.markdown("---")
    st.subheader("Key Market Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(create_metric_card("M&A Activity", "Key Theme of 2025: Strategic Consolidation", 'ma'), unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 14px; color: #000;">
        <b>Q1 2025</b><br>
        57 deals totaling $9.2 B, fewer transactions but significantly higher value than Q4 2024, led by Stryker's $4.9 B acquisition of Inari Medical and Zimmer Biomet's $1.2 B purchase of Paragon 28. Median upfronts rose to $250 M, signaling confidence in scaling revenue-stage assets.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q2 2025</b><br>
        43 deals worth $2.1 B, down from Q1's $9.2 B as elevated interest rates and valuation gaps slowed new bids. Notable activity included Merit Medical's purchase of Biolife Delaware, reflecting steady appetite for niche device integrations despite market caution.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q3 2025</b><br>
        65 transactions totaling $21.7 B, the most active quarter since 2022 and second-highest value in three years. The surge was led by Waters Corp's $17.5 B merger with BD's Biosciences & Diagnostics Solutions unit, alongside Terumo/OrganOx ($1.5 B) and ArchiMed/ZimVie ($730 M), underscoring renewed large-cap consolidation momentum.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card("Venture Capital", "Key Theme of 2025: Selective Investment", 'venture'), unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 14px; color: #000;">
        <b>Q1 2024</b><br>
        ~$5.5 B invested across 182 rounds as early signs of recovery emerged after a weak 2023. Most checks were under $50 M, but multiple $100 M+ raises (e.g., Element Biosciences and Lila Sciences) signaled returning investor confidence in AI-driven diagnostics and platform plays.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q2 2024</b><br>
        $4.3 B raised across 167 rounds (H1 total $9.7 B / 341 rounds). The quarter saw a modest expansion led by Amber Therapeutics' $100 M Series A and early-stage capital revival ($2.4 B in Seed and Series A funding). Momentum reflected growing appetite for device and neuro-stimulation platforms.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q3 2024</b><br>
        $5.1 B across 154 rounds (YTD $16.1 B / 554). Most rounds remained below $50 M (383 of 486 disclosed), though a cluster of large deals including Element Biosciences ($277 M) and Flo Health ($200 M) helped drive a 27% YoY growth trajectory.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q4 2024</b><br>
        $3.0 B across 125 rounds (2024 total $19.1 B / 691 rounds). While the number of rounds fell 5% YoY, the dollar total rose 12%. Selective confidence in high-value plays continued, highlighted by Impress ($117 M) and Nusano ($115 M) later-stage raises amid tight funding conditions.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q1 2025</b><br>
        $3.7 B invested across 117 rounds (+9% YoY), driven by fewer but larger financings. Mega-rounds like Lila Sciences ($200 M) and OganOx ($142 M) marked investor preference for AI-enabled diagnostics and advanced therapeutic devices amid slower seed formation and consolidation around later-stage bets.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q2 2025</b><br>
        $2.6 B across 90 rounds (H1 total $6.8 B/194 rounds), sustaining a "flight to quality." Large financings like Neuralink ($650 M Series E) and Biolinq ($100 M Series C) dominated, while early-stage participation fell as investors favored proven clinical and regulatory traction.
        </div>
        <br>
        <div style="font-size: 14px; color: #000;">
        <b>Q3 2025</b><br>
        $2.9 B across 67 rounds (YTD $9.5 B/259 rounds), a sequential uptick from Q2 but still below 2024 levels. Late-stage deals like Lila Sciences ($235 M Series A), Supira Medical ($120 M Series E), and SetPoint Medical ($115 M Series D) drove totals while early-stage rounds lagged amid macro pressure.
        </div>
        """, unsafe_allow_html=True)

    # Add comparison section with CONDENSED spacing
    st.markdown("---")
    st.markdown("### JPMorgan vs BeaconOne Data - Quarterly Comparison")
    
    # Define colors for each metric
    METRIC_COLORS = {
        'ma_count': '#5B9BD5',
        'ma_value': '#2E5C8A',
        'inv_count': '#D4A574',
        'inv_value': '#8B6F47'
    }
    
    # Different border color for EACH quarter
    QUARTER_COLORS = {
        'Q1': '#7FA8C9',
        'Q2': '#C9A77F',
        'Q3': '#9B8BA8'
    }
    
    # Create columns with separators - CONDENSED spacing
    q1_col, sep1, q2_col, sep2, q3_col = st.columns([10, 0.3, 10, 0.3, 10])
    
    quarters_data = [
        (q1_col, 'Q1', QUARTER_COLORS['Q1']),
        (q2_col, 'Q2', QUARTER_COLORS['Q2']),
        (q3_col, 'Q3', QUARTER_COLORS['Q3'])
    ]
    
    for col, quarter, border_color in quarters_data:
        with col:
            with st.container():
                # CONDENSED header and padding
                st.markdown(f"""
                <div style="border: 3px solid {border_color}; border-radius: 10px; padding: 10px 8px 10px 8px; background-color: #fafbfc; margin-bottom: 15px;">
                    <h3 style="text-align: center; color: #333; margin: 0 0 15px 0; font-family: Arial, sans-serif; font-size: 18px; font-weight: bold;">{quarter} 2025</h3>
                """, unsafe_allow_html=True)
                
                # JP Morgan data
                jp_ma_count = {'Q1': 57, 'Q2': 43, 'Q3': 65}[quarter]
                jp_ma_value = {'Q1': '$9.2B', 'Q2': '$2.1B', 'Q3': '$21.7B'}[quarter]
                jp_inv_count = {'Q1': 117, 'Q2': 90, 'Q3': 67}[quarter]
                jp_inv_value = {'Q1': '$3.7B', 'Q2': '$2.6B', 'Q3': '$2.9B'}[quarter]
                
                # M&A Deal Count chart - REDUCED height
                fig_ma_count = create_comparison_mini_chart(
                    'M&A Deal Count',
                    jp_ma_count,
                    beacon_stats[quarter]['ma_count'],
                    METRIC_COLORS['ma_count'],
                    height=120
                )
                if fig_ma_count:
                    st.plotly_chart(fig_ma_count, use_container_width=True, key=f'{quarter}_ma_count', config={'displayModeBar': False})
                
                # REDUCED spacing between charts
                st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)
                
                # M&A Deal Value chart
                fig_ma_value = create_comparison_mini_chart(
                    'M&A Deal Value',
                    jp_ma_value,
                    beacon_stats[quarter]['ma_value'],
                    METRIC_COLORS['ma_value'],
                    height=120
                )
                if fig_ma_value:
                    st.plotly_chart(fig_ma_value, use_container_width=True, key=f'{quarter}_ma_value', config={'displayModeBar': False})
                
                st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)
                
                # Investment Count chart
                fig_inv_count = create_comparison_mini_chart(
                    'Venture Investment Count',
                    jp_inv_count,
                    beacon_stats[quarter]['inv_count'],
                    METRIC_COLORS['inv_count'],
                    height=120
                )
                if fig_inv_count:
                    st.plotly_chart(fig_inv_count, use_container_width=True, key=f'{quarter}_inv_count', config={'displayModeBar': False})
                
                st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)
                
                # Investment Value chart
                fig_inv_value = create_comparison_mini_chart(
                    'Venture Investment Value',
                    jp_inv_value,
                    beacon_stats[quarter]['inv_value'],
                    METRIC_COLORS['inv_value'],
                    height=120
                )
                if fig_inv_value:
                    st.plotly_chart(fig_inv_value, use_container_width=True, key=f'{quarter}_inv_value', config={'displayModeBar': False})
                
                # Closing border div
                st.markdown("</div>", unsafe_allow_html=True)

def show_ipo_activity(ipo_df):
    """Display IPO activity dashboard"""
    st.header("IPO Activity Dashboard")
    
    if ipo_df.empty:
        st.warning("No IPO data available yet.")
        return
    
    # Search box
    search_ipo = st.text_input("🔍 Search IPOs", placeholder="Search by company, sector...", key='search_ipo')
    
    # Create filter section
    st.markdown("#### Filters")
    filtered_ipo = create_filter_section(ipo_df, 'ipo', show_conference=False)
    
    # Apply search filter
    if search_ipo:
        mask = filtered_ipo.apply(lambda row: row.astype(str).str.contains(search_ipo, case=False).any(), axis=1)
        filtered_ipo = filtered_ipo[mask]
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Table", "🏆 Top IPOs", "📈 Charts"])
    
    with tab1:
        # Display IPO table
        ipo_display = filtered_ipo.copy()
        
        # Format Amount for display if it exists
        if 'Amount' in ipo_display.columns:
            ipo_display['_Amount_Numeric'] = ipo_display['Amount'].apply(
                lambda x: float(x) if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else -1
            )
            ipo_display = ipo_display.sort_values('_Amount_Numeric', ascending=False)
            ipo_display['Amount'] = ipo_display['Amount'].apply(
                lambda x: format_currency_abbreviated(float(x)) if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else x
            )
        
        display_cols = [col for col in ipo_display.columns if not col.startswith('_')]
        
        # Create column config to bold headers
        column_config = {col: st.column_config.TextColumn(col, help=f"{col}") for col in display_cols}
        
        st.dataframe(
            ipo_display[display_cols],
            use_container_width=True,
            height=400,
            column_config=column_config
        )
    
    with tab2:
        st.markdown("### Top 3 IPOs by Amount Raised")
        
        if 'Amount' in filtered_ipo.columns:
            top_ipos = filtered_ipo.copy()
            
            def parse_ipo_amount(val):
                if val == 'Undisclosed' or pd.isna(val):
                    return 0
                val_str = str(val).replace('$', '').replace(',', '').strip()
                try:
                    return float(val_str)
                except:
                    return 0
            
            top_ipos['Amount_Numeric'] = top_ipos['Amount'].apply(parse_ipo_amount)
            top_ipos = top_ipos.nlargest(3, 'Amount_Numeric')
            
            for idx, row in top_ipos.iterrows():
                formatted_value = format_currency_abbreviated(row['Amount'])
                
                st.markdown(f"**{row['Company']}**")
                st.markdown(f"<h1 style='margin-top: -10px; margin-bottom: 5px; color: #9B59B6;'>{formatted_value}</h1>", unsafe_allow_html=True)
                
                # Add details
                sector = str(row['Sector']) if 'Sector' in row and row['Sector'] != 'Undisclosed' else 'N/A'
                quarter = str(row['Quarter']) if row['Quarter'] != 'Undisclosed' else 'N/A'
                st.markdown(f"<p style='font-size: 11px; color: #888;'><b>Sector:</b> {sector} | <b>Quarter:</b> {quarter}</p>", unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.info("Amount data not available for IPOs")
    
    with tab3:
        st.markdown("#### Chart Filters")
        filtered_ipo_chart = create_filter_section(ipo_df, 'ipo_chart', show_conference=False)
        
        fig = create_ipo_quarterly_chart(filtered_ipo_chart)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

def create_ipo_quarterly_chart(df):
    """Create quarterly IPO chart"""
    try:
        if df.empty or 'Amount' not in df.columns:
            st.warning("No IPO data available for chart")
            return None
        
        def parse_value(val):
            if pd.isna(val) or val == 'Undisclosed' or val == '' or val is None:
                return 0
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except (ValueError, TypeError, AttributeError):
                return 0
        
        # Group by quarter
        quarterly_data = df.groupby('Quarter').agg({
            'Amount': lambda x: sum([parse_value(v) for v in x]),
            'Company': 'count'
        }).reset_index()
        quarterly_data.columns = ['Quarter', 'Total_Amount', 'IPO_Count']
        
        # Sort quarters
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarterly_data['Quarter'] = pd.Categorical(quarterly_data['Quarter'], categories=quarter_order, ordered=True)
        quarterly_data = quarterly_data.sort_values('Quarter')
        quarterly_data = quarterly_data[quarterly_data['Quarter'] != 'Undisclosed']
        
        if quarterly_data.empty:
            st.warning("No quarterly data available for IPO chart")
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Total_Amount'],
            name='IPO Value',
            marker_color='#9B59B6',
            text=[format_currency_abbreviated(v) for v in quarterly_data['Total_Amount']],
            textposition='outside',
            textfont=dict(size=14, color='#333'),
            yaxis='y',
            hovertemplate='<b>%{x}</b><br>IPO Value: %{text}<br><extra></extra>'
        ))
        
        # Add line for count
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'],
            y=quarterly_data['IPO_Count'],
            name='IPO Count',
            mode='lines+markers+text',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line']),
            text=quarterly_data['IPO_Count'],
            textposition='top center',
            textfont=dict(size=14, color='#333'),
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>IPO Count: %{y}<br><extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(text='IPO Activity by Quarter', font=dict(size=20, color='#333', family='Arial, sans-serif')),
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),
                showgrid=False,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(text='Total IPO Value (USD)', font=dict(size=16)),
                side='left',
                showgrid=False,
                range=[0, max(quarterly_data['Total_Amount']) * 1.35] if len(quarterly_data) > 0 else [0, 1000],
                tickfont=dict(size=13)
            ),
            yaxis2=dict(
                title=dict(text='Number of IPOs', font=dict(size=16)),
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(quarterly_data['IPO_Count']) * 1.5] if len(quarterly_data) > 0 else [0, 10],
                tickfont=dict(size=13)
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=13)
            ),
            height=450,
            margin=dict(t=100, b=50, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=13, family='Arial, sans-serif')
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating IPO chart: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

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
                            new_ipo = ipo_df
                        
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
                            # Append mode
                            final_ma = pd.concat([ma_df, new_ma], ignore_index=True)
                            final_inv = pd.concat([inv_df, new_inv], ignore_index=True)
                            
                            # Remove duplicates
                            final_ma = final_ma.drop_duplicates(subset=['Company', 'Acquirer', 'Deal Value'], keep='last')
                            final_inv = final_inv.drop_duplicates(subset=['Company', 'Amount Raised'], keep='last')
                            
                            st.info(f"📊 Added {len(final_ma) - len(ma_df)} new M&A deals and {len(final_inv) - len(inv_df)} new investment deals")
                        else:
                            # Replace mode
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