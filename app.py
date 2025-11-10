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
    'count_line': '#CCCCCC',       # Very light gray for count lines
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
        # Fill Conference column with '--' for blank cells, other columns with 'Undisclosed'
        for col in ma_df.columns:
            if col == 'Conference':
                ma_df[col] = ma_df[col].fillna('--')
            else:
                ma_df[col] = ma_df[col].fillna('Undisclosed')
        
        for col in inv_df.columns:
            if col == 'Conference':
                inv_df[col] = inv_df[col].fillna('--')
            else:
                inv_df[col] = inv_df[col].fillna('Undisclosed')
        
        if not ipo_df.empty:
            ipo_df = ipo_df.fillna('Undisclosed')
        
        # Remove unnamed columns
        ma_df = ma_df.loc[:, ~ma_df.columns.str.contains('^Unnamed')]
        inv_df = inv_df.loc[:, ~inv_df.columns.str.contains('^Unnamed')]
        if not ipo_df.empty:
            ipo_df = ipo_df.loc[:, ~ipo_df.columns.str.contains('^Unnamed')]
        
        # Rename Sector to Category for display
        if 'Sector' in ma_df.columns:
            ma_df = ma_df.rename(columns={'Sector': 'Category'})
        if 'Sector' in inv_df.columns:
            inv_df = inv_df.rename(columns={'Sector': 'Category'})
        
        # Keep year in Quarter column for context (e.g., "Q1 2025" stays as "Q1 2025")
        # This ensures quarters display with year throughout the app
        if 'Quarter' in ma_df.columns:
            ma_df['Quarter'] = ma_df['Quarter'].astype(str)
            ma_df['Quarter'] = ma_df['Quarter'].fillna('Undisclosed')
        
        if 'Quarter' in inv_df.columns:
            inv_df['Quarter'] = inv_df['Quarter'].astype(str)
            inv_df['Quarter'] = inv_df['Quarter'].fillna('Undisclosed')
        
        if not ipo_df.empty and 'Quarter' in ipo_df.columns:
            ipo_df['Quarter'] = ipo_df['Quarter'].astype(str)
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
            st.session_state.backup_available = True
        
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

def undo_last_upload():
    """Restore data from the backup file"""
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
            return False, "Could not find data file"
        
        backup_path = excel_path.replace('.xlsx', '_backup.xlsx')
        
        if not os.path.exists(backup_path):
            return False, "No backup file found"
        
        # Restore from backup
        import shutil
        shutil.copy2(backup_path, excel_path)
        
        # Clear backup availability flag
        st.session_state.backup_available = False
        st.session_state.last_backup_time = None
        
        return True, "Successfully restored previous version"
        
    except Exception as e:
        return False, f"Error restoring backup: {str(e)}"

def create_inline_comparison_bars(jp_value, beacon_value, color, is_value=False, max_value=None):
    """Create inline horizontal comparison bars for table display"""
    # Parse values to get numeric comparison
    def parse_value(val):
        if isinstance(val, str):
            val_str = str(val).replace('$', '').replace(',', '').strip()
            if 'B' in val_str:
                return float(val_str.replace('B', '')) * 1000
            elif 'M' in val_str:
                return float(val_str.replace('M', ''))
            else:
                try:
                    return float(val_str)
                except:
                    return 0
        return float(val) if val else 0
    
    jp_numeric = parse_value(jp_value)
    beacon_numeric = parse_value(beacon_value)
    
    # Calculate percentages for bar widths
    # If max_value provided, use it for calibration; otherwise use local max
    if max_value is not None and max_value > 0:
        max_val = max_value
    else:
        max_val = max(jp_numeric, beacon_numeric)
    
    if max_val > 0:
        jp_pct = (jp_numeric / max_val) * 100
        beacon_pct = (beacon_numeric / max_val) * 100
    else:
        jp_pct = 0
        beacon_pct = 0
    
    # Lighter version of color for BeaconOne
    def hex_to_rgba(hex_color, opacity=0.6):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f'rgba({r},{g},{b},{opacity})'
        return hex_color
    
    beacon_color = hex_to_rgba(color, 0.5)
    
    html = f"""
    <div style="padding: 8px 0;">
        <div style="margin-bottom: 6px; display: flex; align-items: center;">
            <span style="font-size: 11px; color: #666; width: 80px; font-weight: 500;">JPMorgan:</span>
            <div style="flex: 1; background-color: #f0f0f0; height: 20px; border-radius: 3px; position: relative; margin-right: 8px;">
                <div style="background-color: {color}; height: 100%; width: {jp_pct}%; border-radius: 3px;"></div>
            </div>
            <span style="font-size: 12px; font-weight: bold; color: #333; min-width: 50px; text-align: right;">{jp_value}</span>
        </div>
        <div style="display: flex; align-items: center;">
            <span style="font-size: 11px; color: #666; width: 80px; font-weight: 500;">BeaconOne:</span>
            <div style="flex: 1; background-color: #f0f0f0; height: 20px; border-radius: 3px; position: relative; margin-right: 8px;">
                <div style="background-color: {beacon_color}; height: 100%; width: {beacon_pct}%; border-radius: 3px;"></div>
            </div>
            <span style="font-size: 12px; font-weight: bold; color: #333; min-width: 50px; text-align: right;">{beacon_value}</span>
        </div>
    </div>
    """
    return html

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
            categories = ['All'] + sorted([s for s in df['Category'].unique() if s != 'Undisclosed'])
            selected_category = st.selectbox("Category", categories, key=f'category_{section_key}')
        
        if show_conference:
            with col4:
                conferences = ['All'] + sorted([c for c in df['Conference'].unique() if c not in ['Undisclosed', '--']])
                selected_conference = st.selectbox("Conference", conferences, key=f'conference_{section_key}')
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_quarter != 'All':
        filtered_df = filtered_df[filtered_df['Quarter'] == selected_quarter]
    if selected_month != 'All':
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    if show_conference and selected_conference != 'All':
        filtered_df = filtered_df[filtered_df['Conference'] == selected_conference]
    
    return filtered_df

def format_currency_abbreviated(value):
    """Format currency values for charts and cards (e.g., $2.1B or $350.0M)"""
    if pd.isna(value) or value == 'Undisclosed':
        return 'Undisclosed'
    try:
        value = float(str(value).replace('$', '').replace('B', '').replace('M', '').replace(',', ''))
        if value >= 1000000000:  # 1 billion or more
            return f"${value/1000000000:.1f}B"
        elif value >= 1000000:  # 1 million or more
            return f"${value/1000000:.1f}M"
        elif value > 0:
            return f"${value:,.0f}"
        else:
            return 'Undisclosed'
    except:
        return str(value)

def format_currency_from_millions(value):
    """Format currency values when input is in millions (e.g., 9200 -> $9.2B)"""
    if pd.isna(value) or value == 'Undisclosed':
        return 'Undisclosed'
    try:
        value = float(str(value).replace('$', '').replace('B', '').replace('M', '').replace(',', ''))
        # Value is in millions, so multiply by 1,000,000 to get actual dollars
        value_in_dollars = value * 1000000
        if value_in_dollars >= 1000000000:  # 1 billion or more
            return f"${value_in_dollars/1000000000:.1f}B"
        elif value_in_dollars >= 1000000:  # 1 million or more
            return f"${value_in_dollars/1000000:.1f}M"
        elif value_in_dollars > 0:
            return f"${value_in_dollars:,.0f}"
        else:
            return 'Undisclosed'
    except:
        return str(value)

def format_currency_full(value):
    """Format currency values for tables (e.g., $350,000,000)"""
    if pd.isna(value) or value == 'Undisclosed':
        return 'Undisclosed'
    try:
        value = float(str(value).replace('$', '').replace('B', '').replace('M', '').replace(',', ''))
        if value > 0:
            return f"${value:,.0f}"
        else:
            return 'Undisclosed'
    except:
        return str(value)

def format_currency(value):
    """Deprecated: Use format_currency_abbreviated() or format_currency_full() instead"""
    return format_currency_abbreviated(value)

def create_metric_card(label, value, color_scheme='ma'):
    """Create a styled metric card"""
    card_class = 'metric-card' if color_scheme == 'ma' else 'metric-card metric-card-venture'
    
    return f"""
    <div class="{card_class}">
        <p style='margin: 0; font-size: 14px; color: #666; font-weight: 500;'>{label}</p>
        <p style='margin: 5px 0 0 0; font-size: 32px; font-weight: bold; color: #333;'>{value}</p>
    </div>
    """

def create_comparison_mini_chart(metric_name, jp_value, beacon_value, bar_color, height=150):
    """Create mini bar chart comparing JPMorgan vs BeaconOne data"""
    try:
        # Convert hex to rgba with opacity for second bar
        def hex_to_rgba(hex_color, opacity=0.8):
            """Convert hex color to rgba with specified opacity"""
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                return f'rgba({r},{g},{b},{opacity})'
            return hex_color
        
        # Convert string values to numeric for comparison
        def parse_value(val):
            if isinstance(val, str):
                val_str = str(val).replace('$', '').replace(',', '').strip()
                try:
                    # Check if it's billions before removing B
                    if 'B' in val_str:
                        numeric_val = float(val_str.replace('B', ''))
                        return numeric_val * 1000  # Convert billions to millions for consistent scale
                    elif 'M' in val_str:
                        return float(val_str.replace('M', ''))
                    else:
                        return float(val_str)
                except:
                    return 0
            return float(val) if val else 0
        
        jp_numeric = parse_value(jp_value)
        beacon_numeric = parse_value(beacon_value)
        
        # Create figure
        fig = go.Figure()
        
        # Add bars with proper color format - THINNER bars, READABLE data labels
        fig.add_trace(go.Bar(
            x=['JPMorgan', 'BeaconOne'],
            y=[jp_numeric, beacon_numeric],
            marker=dict(
                color=[bar_color, hex_to_rgba(bar_color, 0.7)],  # Colored bars
                line=dict(color='white', width=2)  # White outline on bars
            ),
            width=0.25,  # Make bars much thinner (was 0.5, now about half size)
            text=[str(jp_value), str(beacon_value)],
            textposition='outside',
            textfont=dict(size=18, color='#333', family='Arial, sans-serif', weight='bold'),  # Readable size (18px) and bold
            hovertemplate='<b>%{x}</b><br>%{text}<br><extra></extra>',
            showlegend=False
        ))
        
        # Update layout - light background, dark text, NO GRIDLINES, COMPACT
        fig.update_layout(
            title=dict(
                text=metric_name,
                font=dict(size=15, color='#333', family='Arial, sans-serif', weight='bold'),  # Title size
                x=0.5,
                xanchor='center',
                y=0.95,
                yanchor='top'
            ),
            plot_bgcolor='white',  # Clean white background
            paper_bgcolor='white',
            xaxis=dict(
                showgrid=False,  # No gridlines
                showticklabels=True,
                tickfont=dict(size=12, color='#666'),  # Axis labels
                title=None,
                showline=False,  # No axis line
                zeroline=False
            ),
            yaxis=dict(
                showgrid=False,  # No gridlines
                gridcolor='#e0e0e0',
                gridwidth=1,
                showticklabels=False,
                title=None,
                range=[0, max(jp_numeric, beacon_numeric) * 1.8] if max(jp_numeric, beacon_numeric) > 0 else [0, 100],  # Zoomed out more for better label visibility
                showline=False,  # No axis line
                zeroline=False
            ),
            height=height,
            margin=dict(t=50, b=20, l=15, r=15),  # More condensed margins
            hovermode='x'
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating comparison chart: {str(e)}")
        return None

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
        
        # Sort quarters properly with years (e.g., Q1 2024, Q2 2024, ..., Q1 2025, Q2 2025, etc.)
        # Extract quarter and year for proper sorting
        def sort_key(q):
            """Create a sort key for quarters like 'Q1 2025' -> (2025, 1)"""
            try:
                parts = str(q).split()
                if len(parts) == 2:
                    quarter_num = int(parts[0].replace('Q', ''))
                    year = int(parts[1])
                    return (year, quarter_num)
                else:
                    return (9999, 99)  # Put malformed quarters at the end
            except:
                return (9999, 99)
        
        quarterly_data['_sort_key'] = quarterly_data['Quarter'].apply(sort_key)
        quarterly_data = quarterly_data.sort_values('_sort_key')
        quarterly_data = quarterly_data.drop('_sort_key', axis=1)
        
        # Remove any invalid quarters
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
            text=[f"<b>{format_currency_abbreviated(v)}</b>" for v in quarterly_data['Total_Value']],  # Bold abbreviated format
            textposition='outside',
            textfont=dict(size=14),  # Larger text
            yaxis='y',
            hovertemplate='<b>%{x}</b><br>Deal Value: $%{y:,.0f}<br><extra></extra>'
        ))
        
        # Add line chart for deal count
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'].astype(str),
            y=quarterly_data['Deal_Count'],
            name='Deal Count',
            mode='lines+markers',
            line=dict(color=line_color, width=3),
            marker=dict(size=10, color=line_color, line=dict(color='white', width=2)),
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Deal Count: %{y}<br><extra></extra>',
            connectgaps=True,
            cliponaxis=False
        ))
        
        # Add annotations with white background for deal count labels
        annotations = []
        for i, row in quarterly_data.iterrows():
            annotations.append(
                dict(
                    x=str(row['Quarter']),
                    y=row['Deal_Count'],
                    text=str(int(row['Deal_Count'])),
                    showarrow=False,
                    yref='y2',
                    font=dict(size=13, color='#000000'),
                    bgcolor='#CCCCCC',
                    borderpad=4,
                    yshift=10
                )
            )
        
        # Update layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333', family='Arial, sans-serif')),  # Larger title
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),  # Modern syntax
                showgrid=False,
                tickfont=dict(size=14)  # Larger tick labels
            ),
            yaxis=dict(
                title=dict(text='Total Deal Value (USD)', font=dict(size=16)),  # Modern syntax
                side='left',
                showgrid=False,
                range=[0, max(quarterly_data['Total_Value']) * 1.45] if len(quarterly_data) > 0 else [0, 1000],  # Increased for more label space
                tickfont=dict(size=13)  # Larger tick labels
            ),
            yaxis2=dict(
                title=dict(text='Number of Deals', font=dict(size=16)),  # Modern syntax
                overlaying='y',
                side='right',
                showgrid=False,
                tickfont=dict(size=13)  # Larger tick labels
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=13)  # Larger legend text
            ),
            height=height,
            margin=dict(t=100, b=50, l=50, r=50),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=13, family='Arial, sans-serif'),  # Base font larger
            annotations=annotations  # Add the annotations with white backgrounds
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
        quarters = ['Q1 2025', 'Q2 2025', 'Q3 2025']
        
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
        
        # Add bars for deal values - convert to billions for display
        fig.add_trace(go.Bar(
            x=quarters,
            y=[v/1000 for v in values],  # Convert millions to billions for Y-axis
            name='Deal Value',
            marker_color=color,
            text=[f"<b>{format_currency_from_millions(v)}</b>" for v in values],  # Values are in millions
            textposition='outside',
            textfont=dict(size=14),  # Larger text
            yaxis='y',
            hovertemplate='<b>%{x}</b><br>Deal Value: %{text}<br><extra></extra>'
        ))
        
        # Add line chart for deal count
        fig.add_trace(go.Scatter(
            x=quarters,
            y=counts,
            name='Deal Count',
            mode='lines+markers',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line'], line=dict(color='white', width=2)),
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Deal Count: %{y}<br><extra></extra>',
            connectgaps=True,
            cliponaxis=False
        ))
        
        # Add annotations with white background for deal count labels
        annotations = []
        for i, (quarter, count) in enumerate(zip(quarters, counts)):
            if count > 0:
                annotations.append(
                    dict(
                        x=quarter,
                        y=count,
                        text=str(count),
                        showarrow=False,
                        yref='y2',
                        font=dict(size=13, color='#000000'),
                        bgcolor='#CCCCCC',
                        borderpad=4,
                        yshift=10
                    )
                )
        
        # Update layout with dual y-axes
        fig.update_layout(
            title=dict(text=f'{category} Activity', font=dict(size=18, color='#333', family='Arial, sans-serif')),
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),  # Modern syntax
                showgrid=False,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(text='Deal Value (Billions USD)', font=dict(size=16)),  # Changed to Billions
                side='left',
                showgrid=False,
                range=[0, max([v/1000 for v in values]) * 1.45],  # Increased for more label space
                tickfont=dict(size=13)
            ),
            yaxis2=dict(
                title=dict(text='Number of Deals', font=dict(size=16)),  # Modern syntax
                overlaying='y',
                side='right',
                showgrid=False,
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
            font=dict(size=13, family='Arial, sans-serif'),
            annotations=annotations  # Add the annotations with white backgrounds
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating {category} chart: {str(e)}")
        return None

def create_sunburst_chart(df, value_col, deal_type, category_col='Category'):
    """Create sunburst chart showing deal values by category with top deals in hover"""
    try:
        # Filter out 'Undisclosed' categories
        df_filtered = df[df[category_col] != 'Undisclosed'].copy()
        
        if len(df_filtered) == 0:
            st.info(f"No category data available for {deal_type}")
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
        
        # Add numeric value column for sorting
        df_filtered['_numeric_value'] = df_filtered[value_col].apply(parse_value)
        
        # Group by category and get stats + top deals
        category_stats = []
        for category in df_filtered[category_col].unique():
            category_df = df_filtered[df_filtered[category_col] == category]
            total_value = category_df['_numeric_value'].sum()
            
            # Get top 3 deals for this category
            top_deals = category_df.nlargest(3, '_numeric_value')
            deal_list = []
            for idx, deal in top_deals.iterrows():
                company = deal['Company']
                value = deal['_numeric_value']
                if value > 0:
                    if value >= 1000000000:
                        val_str = f"${value/1000000000:.1f}B"
                    elif value >= 1000000:
                        val_str = f"${value/1000000:.0f}M"
                    else:
                        val_str = f"${value:,.0f}"
                    deal_list.append(f"{company} ({val_str})")
            
            category_stats.append({
                'Category': category,
                'Total_Value': total_value,
                'Top_Deals': '<br>  • '.join(deal_list) if deal_list else 'No deals'
            })
        
        category_data = pd.DataFrame(category_stats)
        
        # Remove categories with zero value
        category_data = category_data[category_data['Total_Value'] > 0]
        
        if len(category_data) == 0:
            st.info(f"No deal value data available for {deal_type} categories")
            return None
        
        # Sort by value descending
        category_data = category_data.sort_values('Total_Value', ascending=False)
        
        # Create complementary muted color palette
        if deal_type == 'M&A':
            color_palette = [
                '#7FA8C9', '#A8C9D1', '#6B8BA3', '#94B4C9', '#5A7A94',
                '#8AA9BE', '#B5D0DC', '#6F98B3', '#84A8BD', '#9BBDD1'
            ]
        else:  # Venture
            color_palette = [
                '#C9A77F', '#D9C9A8', '#B89968', '#CCBB99', '#A88E6C',
                '#D4BC94', '#E0D4BC', '#BEA77A', '#C8B490', '#D6C5A3'
            ]
        
        # Assign colors
        colors = [color_palette[i % len(color_palette)] for i in range(len(category_data))]
        
        # Format values for display
        def format_value_display(val):
            if val >= 1000000000:
                return f"${val/1000000000:.2f}B"
            elif val >= 1000000:
                return f"${val/1000000:.1f}M"
            else:
                return f"${val:,.0f}"
        
        category_data['Value_Display'] = category_data['Total_Value'].apply(format_value_display)
        
        # Calculate percentages
        total = category_data['Total_Value'].sum()
        category_data['Percentage'] = (category_data['Total_Value'] / total * 100).round(1)
        
        # Create custom hover text with top deals
        hover_text = []
        for idx, row in category_data.iterrows():
            hover = f"<b>{row['Category']}</b><br>"
            hover += f"<b>Total Value:</b> {row['Value_Display']}<br>"
            hover += f"<b>Percentage:</b> {row['Percentage']}%<br>"
            hover += f"<b>Top Deals:</b><br>  • {row['Top_Deals']}"
            hover_text.append(hover)
        
        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            labels=category_data['Category'],
            parents=[''] * len(category_data),
            values=category_data['Total_Value'],
            text=category_data['Value_Display'],
            textinfo='label+text',
            textfont=dict(size=14, family='Arial, sans-serif'),  # Larger text
            marker=dict(colors=colors, line=dict(color='white', width=2)),
            customdata=hover_text,
            hovertemplate='%{customdata}<extra></extra>',
            branchvalues='total'
        ))
        
        # Update layout
        fig.update_layout(
            height=400,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor='white',
            showlegend=False,
            font=dict(size=14)  # Larger base font
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating sunburst chart: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

# Main app
def main():
    st.title("🤝 MedTech M&A & Venture Dashboard")
    
    # Horizontal navigation with emojis
    page = st.radio(
        "Navigation",
        ["📊 Deal Activity", "📈 JP Morgan Industry Report", "🏢 IPO Activity", "🎤 Conferences", "📤 Upload New Dataset"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Load data
    ma_df, inv_df, ipo_df = load_data()
    
    if page == "📊 Deal Activity":
        show_deal_activity(ma_df, inv_df)
    elif page == "📈 JP Morgan Industry Report":
        show_jp_morgan_summary(ma_df, inv_df)
    elif page == "🏢 IPO Activity":
        show_ipo_activity(ipo_df)
    elif page == "🎤 Conferences":
        show_conferences(ma_df, inv_df)
    elif page == "📤 Upload New Dataset":
        show_upload_dataset(ma_df, inv_df, ipo_df)

def show_deal_activity(ma_df, inv_df):
    """Display deal activity dashboard"""
    st.header("Deal Activity Dashboard (Source: BeaconOne Desk Research)")
    
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
        ma_value_display = format_currency_abbreviated(total_ma_value)
        
        # Display metric cards
        st.markdown(create_metric_card("Total M&A Deal Value", ma_value_display, 'ma'), unsafe_allow_html=True)
        st.markdown(create_metric_card("Total M&A Deal Count", total_ma_deals, 'ma'), unsafe_allow_html=True)
        
        # M&A Sunburst Chart
        st.markdown("#### M&A Deals by Category")
        
        # Independent quarter filter for M&A sunburst
        quarters_ma_sun = ['All'] + sorted([q for q in ma_df['Quarter'].unique() if q != 'Undisclosed'])
        selected_quarter_ma_sun = st.selectbox("Filter by Quarter", quarters_ma_sun, key='ma_sunburst_quarter')
        
        filtered_ma_sun = ma_df.copy()
        if selected_quarter_ma_sun != 'All':
            filtered_ma_sun = filtered_ma_sun[filtered_ma_sun['Quarter'] == selected_quarter_ma_sun]
        
        fig_ma_sunburst = create_sunburst_chart(filtered_ma_sun, 'Deal Value', 'M&A', 'Category')
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
        inv_value_display = format_currency_abbreviated(total_inv_value)
        
        # Display metric cards
        st.markdown(create_metric_card("Total Investment Value", inv_value_display, 'venture'), unsafe_allow_html=True)
        st.markdown(create_metric_card("Total Investment Deal Count", total_inv_deals, 'venture'), unsafe_allow_html=True)
        
        # Venture Sunburst Chart
        st.markdown("#### Venture Deals by Category")
        
        # Independent quarter filter for Venture sunburst
        quarters_inv_sun = ['All'] + sorted([q for q in inv_df['Quarter'].unique() if q != 'Undisclosed'])
        selected_quarter_inv_sun = st.selectbox("Filter by Quarter", quarters_inv_sun, key='inv_sunburst_quarter')
        
        filtered_inv_sun = inv_df.copy()
        if selected_quarter_inv_sun != 'All':
            filtered_inv_sun = filtered_inv_sun[filtered_inv_sun['Quarter'] == selected_quarter_inv_sun]
        
        fig_inv_sunburst = create_sunburst_chart(filtered_inv_sun, 'Amount Raised', 'Venture', 'Category')
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
        
        # Format Deal Value with $ and commas
        ma_display['Deal Value'] = ma_display['Deal Value'].apply(
            lambda x: f"${float(str(x).replace('$', '').replace(',', '')):,.0f}" if x != 'Undisclosed' and pd.notna(x) and parse_to_numeric(x) > 0 else x
        )
        
        # Display without the numeric column and unnamed columns
        # Filter out: columns starting with '_', 'Unnamed', or empty strings
        display_cols = [col for col in ma_display.columns 
                       if not col.startswith('_') 
                       and not col.startswith('Unnamed')
                       and col.strip() != '']
        
        st.dataframe(
            ma_display[display_cols], 
            use_container_width=True,
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
            # Format value - use abbreviated format for display (e.g., $2.1B)
            deal_value = row['Deal Value']
            if deal_value != 'Undisclosed' and parse_to_numeric(deal_value) > 0:
                try:
                    numeric_val = parse_to_numeric(deal_value)
                    formatted_value = format_currency_abbreviated(numeric_val)
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
            category = str(row['Category']) if row['Category'] != 'Undisclosed' else 'N/A'
            quarter = str(row['Quarter']) if row['Quarter'] != 'Undisclosed' else 'N/A'
            month = str(row['Month']) if row['Month'] != 'Undisclosed' else 'N/A'
            st.markdown(f"<p style='font-size: 11px; color: #888;'><b>Category:</b> {category} | <b>Quarter:</b> {quarter} | <b>Month:</b> {month}</p>", unsafe_allow_html=True)
            
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
            category = str(row['Category']) if row['Category'] != 'Undisclosed' else 'N/A'
            lead_investors = str(row['Lead Investors']) if row['Lead Investors'] != 'Undisclosed' else 'N/A'
            quarter = str(row['Quarter']) if row['Quarter'] != 'Undisclosed' else 'N/A'
            st.markdown(f"<p style='font-size: 11px; color: #888;'><b>Type:</b> {funding_type} | <b>Category:</b> {category} | <b>Quarter:</b> {quarter}</p>", unsafe_allow_html=True)
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
            # Check if dataframe is empty or column doesn't exist
            if df.empty or value_col not in df.columns:
                return 0, "$0"
                
            q_data = df[df['Quarter'] == quarter]
            
            # Check if quarter data is empty
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
            
            # Safely calculate total value
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
            # If anything fails, return safe defaults
            print(f"Error in calc_quarterly_stats: {e}")
            return 0, "$0"
    
    # Calculate stats for each quarter
    beacon_stats = {}
    for q in ['Q1 2025', 'Q2 2025', 'Q3 2025']:
        ma_count, ma_value = calc_quarterly_stats(ma_df, q, 'Deal Value')
        inv_count, inv_value = calc_quarterly_stats(inv_df, q, 'Amount Raised')
        # Store with short key for display
        q_short = q.split()[0]  # Just 'Q1', 'Q2', 'Q3' for keys
        beacon_stats[q_short] = {
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
    # ====== QUARTERLY COMPARISON TABLE - NOW ABOVE KEY TRENDS ======
    st.markdown("---")
    st.markdown("### Quarterly Comparison")
    
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
    
    # Function to color-code cells based on their values
    def color_delta_cells(val):
        """Color code ONLY significant changes (≥50%), leave others black"""
        if val == 'None' or pd.isna(val):
            return 'color: #000000'  # Black for None
        
        if '↑' in str(val):
            # Extract percentage
            pct = float(str(val).replace('↑', '').replace('%', ''))
            if pct >= 50:
                return 'color: #00A86B; font-weight: bold'  # Dark green ONLY for ≥50% increase
            else:
                return 'color: #000000'  # Black for <50% increase
        elif '↓' in str(val):
            # Extract percentage
            pct = float(str(val).replace('↓', '').replace('%', ''))
            if pct >= 50:
                return 'color: #D85252; font-weight: bold'  # Dark red ONLY for ≥50% decrease
            else:
                return 'color: #000000'  # Black for <50% decrease
        
        return 'color: #000000'  # Default black
    
    # Function to format dollar values
    def format_dollar_value(val):
        """Format numeric values as $X.XB"""
        try:
            # Round to 1 decimal to avoid floating point errors
            rounded_val = round(float(val), 1)
            return f"${rounded_val:.1f}B"
        except:
            return str(val)
    
    # Function to add separator line between 2024 and 2025
    def highlight_year_separator(row):
        """Add bottom border after Q4 2024 to separate years"""
        if row.name == 3:  # Index 3 is Q4 2024 (0-indexed)
            return ['border-bottom: 3px solid #2c3e50;'] * len(row)
        return [''] * len(row)
    
    # Apply styling to the dataframe
    styled_df = comparison_df.style.applymap(
        color_delta_cells,
        subset=['M&A QoQ Change', 'M&A YoY Change', 'Venture QoQ Change', 'Venture YoY Change']
    ).format(
        format_dollar_value,
        subset=['M&A ($B)', 'Venture ($B)']
    ).apply(
        highlight_year_separator, 
        axis=1
    ).set_properties(**{
        'text-align': 'center'
    }, subset=['M&A QoQ Change', 'M&A YoY Change', 'Venture QoQ Change', 'Venture YoY Change']
    ).set_properties(**{
        'text-align': 'right'
    }, subset=['M&A ($B)', 'Venture ($B)']
    ).set_properties(**{
        'text-align': 'left'
    }, subset=['Quarter']
    ).set_properties(**{
        'font-size': '13px'  # Make table more condensed
    }).set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#f0f2f5'), ('color', '#2c3e50'), ('font-weight', 'bold'), ('text-align', 'center'), ('padding', '8px'), ('font-size', '13px')]},  # Reduced padding
        {'selector': 'td', 'props': [('padding', '6px'), ('border', '1px solid #e0e0e0'), ('font-size', '13px')]},  # Reduced padding
        {'selector': 'tr:nth-of-type(even)', 'props': [('background-color', '#fafbfc')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#f5f5f5')]},
    ])
    
    # Create layout with table on left and key trends on right
    table_col, trends_col = st.columns([3, 2])
    
    with table_col:
        # Display the styled dataframe without fixed height to prevent empty rows
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    with trends_col:
        st.markdown("#### Key Overall Trends")
        st.markdown("""
        <div style="font-size: 13px; color: #000; line-height: 1.6;">
        <b>2025 YTD Summary</b><br>
        <b>M&A:</b> Volumes remained historically strong at 165+ deals totaling ~$33B, highlighting strategic expansion by industry leaders into adjacent diagnostic and therapeutic markets despite lingering macro headwinds.<br><br>
        <b>Venture:</b> Capital reached $9.5B across 259 rounds (through Q3), with capital increasingly concentrated in AI-driven platform and neuro-tech devices.
        </div>
        """, unsafe_allow_html=True)
    
    # ====== KEY MARKET TRENDS - NOW 2 COLUMNS (NO TABLE IN MIDDLE) ======
    st.markdown("---")
    st.subheader("Key Market Trends")
    
    # Create TWO columns instead of three: M&A text | Venture text
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(create_metric_card("M&A Activity", "Key Theme of 2025: Strategic Consolidation", 'ma'), unsafe_allow_html=True)
        st.markdown("""
        <div style="border: 2px solid #5B9BD5; border-radius: 12px; padding: 16px; background-color: #f8fafb; margin-top: 10px;">
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q1 2024</b><br>
                47 deals worth ~$18 B, a rebound driven by renewed strategic activity among large buyers. Continued strength in digital health and diagnostics acquisitions pointed to normalization of post-COVID valuations.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q2 2024</b><br>
                114 deals totaling $40.3 B, nearly matching all of 2023 within six months. Headline transactions included J&J / Shockwave ($13 B) and Boston Scientific / Silk Road ($1.2 B), solidifying H1 as the strongest since 2021.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q3 2024</b><br>
                195 deals worth $47 B through Q3, exceeding 2023 totals and positioning 2024 to rival 2021. Major transactions included J&J / V-Wave ($1.7 B) and Edwards Lifesciences / JenaValve ($1.6 B), marking a return to large-cap strategic acquisitions.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q4 2024</b><br>
                305 transactions valued at $63.1 B for 2024 (up from 134 / $47 B in 2023), making it the second-highest year on record after 2021. Biggest deals included Novo Holdings / Catalent ($16.5 B) and J&J / Shockwave ($13.1 B) alongside Cardinal's acquisitions of GI Alliance and Advanced Diabetes Supply.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q1 2025</b><br>
                57 deals totaling $9.2 B, fewer transactions but significantly higher value than Q4 2024, led by Stryker's $4.9 B acquisition of Inari Medical and Zimmer Biomet's $1.2 B purchase of Paragon 28. Median upfronts rose to $250 M, signaling confidence in scaling revenue-stage assets.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q2 2025</b><br>
                43 deals worth $2.1 B, down from Q1's $9.2 B as elevated interest rates and valuation gaps slowed new bids. Notable activity included Merit Medical's purchase of Biolife Delaware, reflecting steady appetite for niche device integrations despite market caution.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5;">
                <b>Q3 2025</b><br>
                65 transactions totaling $21.7 B, the most active quarter since 2022 and second-highest value in three years. The surge was led by Waters Corp's $17.5 B merger with BD's Biosciences & Diagnostics Solutions unit, alongside Terumo/OrganOx ($1.5 B) and ArchiMed/ZimVie ($730 M), underscoring renewed large-cap consolidation momentum.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card("Venture Capital", "Key Theme of 2025: Selective Investment", 'venture'), unsafe_allow_html=True)
        st.markdown("""
        <div style="border: 2px solid #D4A574; border-radius: 12px; padding: 16px; background-color: #fdfbf8; margin-top: 10px;">
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q1 2024</b><br>
                ~$5.5 B invested across 182 rounds as early signs of recovery emerged after a weak 2023. Most checks were under $50 M, but multiple $100 M+ raises (e.g., Element Biosciences and Lila Sciences) signaled returning investor confidence in AI-driven diagnostics and platform plays.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q2 2024</b><br>
                $4.3 B raised across 167 rounds (H1 total $9.7 B / 341 rounds). The quarter saw a modest expansion led by Amber Therapeutics' $100 M Series A and early-stage capital revival ($2.4 B in Seed and Series A funding). Momentum reflected growing appetite for device and neuro-stimulation platforms.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q3 2024</b><br>
                $5.1 B across 154 rounds (YTD $16.1 B / 554). Most rounds remained below $50 M (383 of 486 disclosed), though a cluster of large deals including Element Biosciences ($277 M) and Flo Health ($200 M) helped drive a 27% YoY growth trajectory.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q4 2024</b><br>
                $3.0 B across 125 rounds (2024 total $19.1 B / 691 rounds). While the number of rounds fell 5% YoY, the dollar total rose 12%. Selective confidence in high-value plays continued, highlighted by Impress ($117 M) and Nusano ($115 M) later-stage raises amid tight funding conditions.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q1 2025</b><br>
                $3.7 B invested across 117 rounds (+9% YoY), driven by fewer but larger financings. Mega-rounds like Lila Sciences ($200 M) and OganOx ($142 M) marked investor preference for AI-enabled diagnostics and advanced therapeutic devices amid slower seed formation and consolidation around later-stage bets.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5; margin-bottom: 10px;">
                <b>Q2 2025</b><br>
                $2.6 B across 90 rounds (H1 total $6.8 B/194 rounds), sustaining a "flight to quality." Large financings like Neuralink ($650 M Series E) and Biolinq ($100 M Series C) dominated, while early-stage participation fell as investors favored proven clinical and regulatory traction.
            </div>
            <div style="font-size: 13px; color: #000; line-height: 1.5;">
                <b>Q3 2025</b><br>
                $2.9 B across 67 rounds (YTD $9.5 B/259 rounds), a sequential uptick from Q2 but still below 2024 levels. Late-stage deals like Lila Sciences ($235 M Series A), Supira Medical ($120 M Series E), and SetPoint Medical ($115 M Series D) drove totals while early-stage rounds lagged amid macro pressure.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Add comparison section
    st.markdown("---")
    st.markdown("### JPMorgan vs BeaconOne Data - Quarterly Comparison")
    
    # Define colors for each metric
    METRIC_COLORS = {
        'ma_count': '#5B9BD5',      # Bright blue for M&A count
        'ma_value': '#2E5C8A',      # Dark navy for M&A value
        'inv_count': '#D4A574',     # Bright tan for Investment count
        'inv_value': '#8B6F47'      # Dark brown for Investment value
    }
    
    # JP Morgan data
    jp_data = {
        'Q1': {'ma_count': 57, 'ma_value': '$9.2B', 'inv_count': 117, 'inv_value': '$3.7B'},
        'Q2': {'ma_count': 43, 'ma_value': '$2.1B', 'inv_count': 90, 'inv_value': '$2.6B'},
        'Q3': {'ma_count': 65, 'ma_value': '$21.7B', 'inv_count': 67, 'inv_value': '$2.9B'}
    }
    
    # Helper function to parse values for max calculation
    def parse_for_max(val):
        if isinstance(val, str):
            val_str = str(val).replace('$', '').replace(',', '').strip()
            if 'B' in val_str:
                return float(val_str.replace('B', '')) * 1000
            elif 'M' in val_str:
                return float(val_str.replace('M', ''))
        return float(val) if val else 0
    
    # Calculate global maximums for each metric type across all quarters
    max_ma_count = 0
    max_ma_value = 0
    max_inv_count = 0
    max_inv_value = 0
    
    for q in ['Q1', 'Q2', 'Q3']:
        max_ma_count = max(max_ma_count, jp_data[q]['ma_count'], beacon_stats[q]['ma_count'])
        max_ma_value = max(max_ma_value, parse_for_max(jp_data[q]['ma_value']), parse_for_max(beacon_stats[q]['ma_value']))
        max_inv_count = max(max_inv_count, jp_data[q]['inv_count'], beacon_stats[q]['inv_count'])
        max_inv_value = max(max_inv_value, parse_for_max(jp_data[q]['inv_value']), parse_for_max(beacon_stats[q]['inv_value']))
    
    # Build table HTML
    table_html = """
    <style>
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-family: Arial, sans-serif;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .comparison-table th {
            background-color: #f0f2f5;
            color: #2c3e50;
            font-weight: bold;
            padding: 12px;
            text-align: center;
            border: 1px solid #e0e0e0;
            font-size: 14px;
        }
        .comparison-table td {
            padding: 12px;
            border: 1px solid #e0e0e0;
            vertical-align: middle;
        }
        .comparison-table .metric-label {
            font-weight: 600;
            color: #333;
            font-size: 13px;
            background-color: #fafbfc;
            white-space: nowrap;
        }
        .comparison-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        .quarter-header {
            font-size: 15px;
            font-weight: bold;
        }
        .q1-header { color: #7FA8C9; }
        .q2-header { color: #C9A77F; }
        .q3-header { color: #9B8BA8; }
        .section-separator td {
            border-bottom: 3px solid #2c3e50 !important;
            padding-bottom: 16px !important;
        }
        .section-start td {
            padding-top: 16px !important;
        }
    </style>
    
    <table class="comparison-table">
        <thead>
            <tr>
                <th style="width: 15%;">Metric</th>
                <th style="width: 28.3%;" class="quarter-header q1-header">Q1 2025</th>
                <th style="width: 28.3%;" class="quarter-header q2-header">Q2 2025</th>
                <th style="width: 28.3%;" class="quarter-header q3-header">Q3 2025</th>
            </tr>
        </thead>
        <tbody>
    """
    
    # Add M&A Deal Count row
    table_html += '<tr><td class="metric-label">M&A Deal Count</td>'
    for q in ['Q1', 'Q2', 'Q3']:
        jp_val = jp_data[q]['ma_count']
        beacon_val = beacon_stats[q]['ma_count']
        table_html += f'<td>{create_inline_comparison_bars(jp_val, beacon_val, METRIC_COLORS["ma_count"], max_value=max_ma_count)}</td>'
    table_html += '</tr>'
    
    # Add M&A Deal Value row
    table_html += '<tr class="section-separator"><td class="metric-label">M&A Deal Value</td>'
    for q in ['Q1', 'Q2', 'Q3']:
        jp_val = jp_data[q]['ma_value']
        beacon_val = beacon_stats[q]['ma_value']
        table_html += f'<td>{create_inline_comparison_bars(jp_val, beacon_val, METRIC_COLORS["ma_value"], is_value=True, max_value=max_ma_value)}</td>'
    table_html += '</tr>'
    
    # Add Investment Count row
    table_html += '<tr class="section-start"><td class="metric-label">Investment Count</td>'
    for q in ['Q1', 'Q2', 'Q3']:
        jp_val = jp_data[q]['inv_count']
        beacon_val = beacon_stats[q]['inv_count']
        table_html += f'<td>{create_inline_comparison_bars(jp_val, beacon_val, METRIC_COLORS["inv_count"], max_value=max_inv_count)}</td>'
    table_html += '</tr>'
    
    # Add Investment Value row
    table_html += '<tr><td class="metric-label">Investment Value</td>'
    for q in ['Q1', 'Q2', 'Q3']:
        jp_val = jp_data[q]['inv_value']
        beacon_val = beacon_stats[q]['inv_value']
        table_html += f'<td>{create_inline_comparison_bars(jp_val, beacon_val, METRIC_COLORS["inv_value"], is_value=True, max_value=max_inv_value)}</td>'
    table_html += '</tr>'
    
    table_html += """
        </tbody>
    </table>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Add source link at the bottom
    st.markdown("---")
    st.markdown("""
    <p style="font-size: 11px; color: #666; text-align: center; margin-top: 20px;">
    Source: <a href="https://www.jpmorgan.com/insights/markets-and-economy/outlook/biopharma-medtech-deal-reports" target="_blank" style="color: #666;">JP Morgan Biopharma & MedTech Deal Reports</a>
    </p>
    """, unsafe_allow_html=True)


def show_ipo_activity(ipo_df):
    """Display IPO activity"""
    st.header("IPO Activity - YTD 2025")
    
    if ipo_df.empty:
        st.info("No IPO data available")
        return
    
    # YTD Overview Chart
    st.markdown("### YTD IPO Overview")
    
    # Quarter filter for IPO chart
    quarters_ipo = ['All'] + sorted([q for q in ipo_df['Quarter'].unique() if pd.notna(q) and q != 'Undisclosed'])
    selected_quarter_ipo = st.selectbox("Filter by Quarter", quarters_ipo, key='ipo_chart_quarter')
    
    # Filter data for chart
    filtered_ipo_chart = ipo_df.copy()
    if selected_quarter_ipo != 'All':
        filtered_ipo_chart = filtered_ipo_chart[filtered_ipo_chart['Quarter'] == selected_quarter_ipo]
    
    # Create IPO chart
    fig_ipo = create_ipo_chart(filtered_ipo_chart)
    if fig_ipo:
        st.plotly_chart(fig_ipo, use_container_width=True)
    
    st.markdown("---")
    
    # Search and filters for table
    search_ipo = st.text_input("🔍 Search IPOs", placeholder="Search by company, type, technology...", key='search_ipo')
    
    st.markdown("#### Filters")
    filtered_ipo = ipo_df.copy()
    
    col1, col2 = st.columns(2)
    with col1:
        quarters = ['All'] + sorted([q for q in ipo_df['Quarter'].unique() if pd.notna(q)])
        selected_quarter = st.selectbox("Quarter", quarters, key='ipo_table_quarter')
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
    
    # Format Amount column with $ and commas
    ipo_display = filtered_ipo.copy()
    if 'Amount' in ipo_display.columns:
        ipo_display['Amount'] = ipo_display['Amount'].apply(
            lambda x: f"${float(x):,.0f}" if pd.notna(x) and x != 'Undisclosed' and str(x).replace('.','').replace('-','').isdigit() else x
        )
    
    # Remove unnamed columns and Date column
    display_cols = [col for col in ipo_display.columns 
                   if not col.startswith('_') 
                   and not col.startswith('Unnamed')
                   and col.strip() != ''
                   and col != 'Date']  # Exclude Date column
    
    # Display table
    st.dataframe(
        ipo_display[display_cols], 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Amount": st.column_config.TextColumn("Amount", help="IPO amount in USD"),
        }
    )

def create_ipo_chart(df):
    """Create IPO quarterly chart"""
    try:
        # Filter out undisclosed quarters
        df_filtered = df[df['Quarter'] != 'Undisclosed'].copy()
        
        if len(df_filtered) == 0:
            st.warning("No data available for IPO chart")
            return None
        
        # Parse amount values
        def parse_amount(val):
            if val == 'Undisclosed' or pd.isna(val):
                return 0
            val_str = str(val).replace('$', '').replace(',', '').strip()
            try:
                return float(val_str)
            except:
                return 0
        
        df_filtered['_Amount_Numeric'] = df_filtered['Amount'].apply(parse_amount)
        
        # Group by quarter
        quarterly_data = df_filtered.groupby('Quarter').agg({
            '_Amount_Numeric': 'sum',
            'Company': 'count'
        }).reset_index()
        quarterly_data.columns = ['Quarter', 'Total_Amount', 'IPO_Count']
        
        # Sort quarters properly with years (e.g., Q1 2024, Q2 2024, ..., Q1 2025, Q2 2025, etc.)
        def sort_key(q):
            """Create a sort key for quarters like 'Q1 2025' -> (2025, 1)"""
            try:
                parts = str(q).split()
                if len(parts) == 2:
                    quarter_num = int(parts[0].replace('Q', ''))
                    year = int(parts[1])
                    return (year, quarter_num)
                else:
                    return (9999, 99)  # Put malformed quarters at the end
            except:
                return (9999, 99)
        
        quarterly_data['_sort_key'] = quarterly_data['Quarter'].apply(sort_key)
        quarterly_data = quarterly_data.sort_values('_sort_key')
        quarterly_data = quarterly_data.drop('_sort_key', axis=1)
        quarterly_data = quarterly_data[quarterly_data['Quarter'].notna()]
        
        if len(quarterly_data) == 0:
            st.warning("No valid quarterly data for IPO chart")
            return None
        
        # Create figure
        fig = go.Figure()
        
        # Add bars for IPO amounts
        fig.add_trace(go.Bar(
            x=quarterly_data['Quarter'].astype(str),
            y=quarterly_data['Total_Amount'],
            name='IPO Value',
            marker_color='#9B59B6',  # Purple for IPO
            text=[f"<b>{format_currency_abbreviated(v)}</b>" for v in quarterly_data['Total_Amount']],
            textposition='outside',
            textfont=dict(size=14),
            yaxis='y',
            hovertemplate='<b>%{x}</b><br>IPO Value: $%{y:,.0f}<br><extra></extra>'
        ))
        
        # Add line for IPO count
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'].astype(str),
            y=quarterly_data['IPO_Count'],
            name='IPO Count',
            mode='lines+markers+text',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line']),
            text=[f"<b>{c}</b>" for c in quarterly_data['IPO_Count']],
            textposition='top center',
            textfont=dict(size=13, color=COLORS['count_line']),  # Slightly smaller and colored
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>IPO Count: %{y}<br><extra></extra>',
            connectgaps=True,
            cliponaxis=False  # Allow labels to extend beyond plot area
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(text='IPO Activity by Quarter', font=dict(size=20, color='#333', family='Arial, sans-serif')),
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),  # Modern syntax
                showgrid=False,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(text='Total IPO Value (USD)', font=dict(size=16)),  # Modern syntax
                side='left',
                showgrid=False,
                range=[0, max(quarterly_data['Total_Amount']) * 1.45] if len(quarterly_data) > 0 else [0, 1000],  # Increased for more label space
                tickfont=dict(size=13)
            ),
            yaxis2=dict(
                title=dict(text='Number of IPOs', font=dict(size=16)),  # Modern syntax
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(quarterly_data['IPO_Count']) * 1.6] if len(quarterly_data) > 0 else [0, 10],  # Increased for more label space
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

def show_conferences(ma_df, inv_df):
    """Display conferences tab with company deal summaries and export options"""
    st.header("🎤 Conference Deal Briefs")
    st.markdown("Generate exportable lists of companies with recent deal activity for specific conferences.")
    
    st.markdown("---")
    
    # Get all unique non-blank conferences from both datasets
    ma_conferences = set(ma_df[ma_df['Conference'] != '--']['Conference'].unique())
    inv_conferences = set(inv_df[inv_df['Conference'] != '--']['Conference'].unique())
    all_conferences = sorted(list(ma_conferences.union(inv_conferences)))
    
    if not all_conferences:
        st.info("No conference data available in the dataset.")
        return
    
    # === FILTERS ===
    st.markdown("### Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Conference**")
        include_all = st.checkbox("All Conferences", value=False, key='conf_all')
        if include_all:
            selected_conferences = all_conferences
        else:
            selected_conferences = st.multiselect(
                "Select conferences",
                all_conferences,
                default=[all_conferences[0]] if all_conferences else [],
                key='conf_select',
                label_visibility="collapsed"
            )
    
    with col2:
        st.markdown("**Time Window**")
        time_window = st.selectbox(
            "Time window",
            ["YTD", "Last Quarter", "Last 2 Quarters", "Last 3 Quarters", "Last 4 Quarters"],
            key='conf_time',
            label_visibility="collapsed"
        )
    
    with col3:
        st.markdown("**Category (Optional)**")
        all_categories_ma = set(ma_df['Category'].unique())
        all_categories_inv = set(inv_df['Category'].unique())
        all_categories = sorted(list(all_categories_ma.union(all_categories_inv) - {'Undisclosed'}))
        
        include_all_cats = st.checkbox("All Categories", value=True, key='conf_cat_all')
        if include_all_cats:
            selected_categories = all_categories
        else:
            selected_categories = st.multiselect(
                "Select categories",
                all_categories,
                default=all_categories,
                key='conf_cat_select',
                label_visibility="collapsed"
            )
    
    if not selected_conferences:
        st.warning("Please select at least one conference.")
        return
    
    st.markdown("---")
    
    # === FILTER DATA BY TIME WINDOW ===
    def filter_by_time_window(df, time_window):
        """Filter dataframe by time window based on Quarter"""
        if time_window == "YTD":
            # Include all 2025 quarters
            return df[df['Quarter'].str.contains('2025', na=False)]
        elif time_window == "Last Quarter":
            # Q3 2025 (most recent)
            return df[df['Quarter'] == 'Q3 2025']
        elif time_window == "Last 2 Quarters":
            # Q2 and Q3 2025
            return df[df['Quarter'].isin(['Q2 2025', 'Q3 2025'])]
        elif time_window == "Last 3 Quarters":
            # Q1, Q2, Q3 2025
            return df[df['Quarter'].isin(['Q1 2025', 'Q2 2025', 'Q3 2025'])]
        elif time_window == "Last 4 Quarters":
            # Q4 2024, Q1-Q3 2025
            return df[df['Quarter'].isin(['Q4 2024', 'Q1 2025', 'Q2 2025', 'Q3 2025'])]
        return df
    
    # Filter M&A data
    filtered_ma = ma_df[ma_df['Conference'].isin(selected_conferences)].copy()
    filtered_ma = filter_by_time_window(filtered_ma, time_window)
    if selected_categories:
        filtered_ma = filtered_ma[filtered_ma['Category'].isin(selected_categories)]
    
    # Filter Venture data
    filtered_inv = inv_df[inv_df['Conference'].isin(selected_conferences)].copy()
    filtered_inv = filter_by_time_window(filtered_inv, time_window)
    if selected_categories:
        filtered_inv = filtered_inv[filtered_inv['Category'].isin(selected_categories)]
    
    # === AGGREGATE BY COMPANY ===
    def parse_value_for_sorting(val):
        """Parse deal value to numeric for sorting"""
        if val == 'Undisclosed' or pd.isna(val):
            return 0
        val_str = str(val).replace('$', '').replace('B', '').replace('M', '').replace(',', '').strip()
        try:
            return float(val_str)
        except:
            return 0
    
    # Build company-level aggregation
    companies = {}
    
    # Process M&A deals
    for idx, row in filtered_ma.iterrows():
        company = row['Company']
        if company not in companies:
            companies[company] = {
                'ma_deals': [],
                'venture_deals': [],
                'categories': set()
            }
        
        deal_type = row['Deal Type (Merger / Acquisition)']
        acquirer = row['Acquirer']
        value = row['Deal Value']
        quarter = row['Quarter']
        category = row['Category']
        tech = row.get('Technology/Description', 'N/A')
        
        if category != 'Undisclosed':
            companies[company]['categories'].add(category)
        
        # Format deal text
        if deal_type == "Merger":
            deal_text = f"Merged with {acquirer}"
        else:
            deal_text = f"Acquired by {acquirer}"
        
        if value != 'Undisclosed':
            deal_text += f" (${parse_value_for_sorting(value):,.0f}, {quarter})"
        else:
            deal_text += f" (Undisclosed, {quarter})"
        
        # Add technology description if available
        if tech and tech != 'N/A' and tech != 'Undisclosed' and str(tech).strip():
            deal_text += f" - {tech}"
        
        companies[company]['ma_deals'].append({
            'text': deal_text,
            'value': parse_value_for_sorting(value),
            'quarter': quarter,
            'acquirer': acquirer,
            'deal_type': deal_type,
            'tech': tech,
            'raw_value': value
        })
    
    # Process Venture deals
    for idx, row in filtered_inv.iterrows():
        company = row['Company']
        if company not in companies:
            companies[company] = {
                'ma_deals': [],
                'venture_deals': [],
                'categories': set()
            }
        
        amount = row['Amount Raised']
        funding_type = row['Funding type (VC / PE)']
        lead_investors = row.get('Lead Investors', 'N/A')
        quarter = row['Quarter']
        category = row['Category']
        tech = row.get('Technology/Description', 'N/A')
        
        if category != 'Undisclosed':
            companies[company]['categories'].add(category)
        
        # Format deal text
        if amount != 'Undisclosed':
            deal_text = f"${parse_value_for_sorting(amount):,.0f} {funding_type}"
        else:
            deal_text = f"Undisclosed {funding_type}"
        
        if lead_investors != 'N/A' and lead_investors != 'Undisclosed':
            deal_text += f", Lead: {lead_investors}"
        
        deal_text += f" ({quarter})"
        
        # Add technology description if available
        if tech and tech != 'N/A' and tech != 'Undisclosed' and str(tech).strip():
            deal_text += f" - {tech}"
        
        companies[company]['venture_deals'].append({
            'text': deal_text,
            'value': parse_value_for_sorting(amount),
            'quarter': quarter,
            'funding_type': funding_type,
            'lead_investors': lead_investors,
            'tech': tech,
            'raw_value': amount
        })
    
    if not companies:
        st.info(f"No companies found with deal activity for the selected filters.")
        return
    
    # === PREPARE DISPLAY TABLE ===
    display_rows = []
    
    for company, data in companies.items():
        # Sort deals by value descending
        ma_sorted = sorted(data['ma_deals'], key=lambda x: x['value'], reverse=True)
        venture_sorted = sorted(data['venture_deals'], key=lambda x: x['value'], reverse=True)
        
        # Get company categories
        categories_text = " | ".join(sorted(data['categories'])) if data['categories'] else ""
        
        # Add each M&A deal as a separate row
        for deal in ma_sorted:
            deal_type = "M&A: " + ("Merger" if deal['deal_type'] == "Merger" else "Acquisition")
            if deal['deal_type'] == "Merger":
                deal_type += f" with {deal['acquirer']}"
            else:
                deal_type += f" by {deal['acquirer']}"
            
            # Format amount
            if deal['raw_value'] != 'Undisclosed':
                deal_amount = f"${deal['value']:,.0f}"
            else:
                deal_amount = "Undisclosed"
            
            # Add quarter to amount
            deal_amount += f" ({deal['quarter']})"
            
            # Technology description
            tech_desc = deal['tech'] if deal['tech'] and deal['tech'] != 'N/A' and deal['tech'] != 'Undisclosed' else ""
            
            display_rows.append({
                'Company': company,
                'Deal Type': deal_type,
                'Deal Amount': deal_amount,
                'Technology / Company Description': tech_desc,
                'Category': categories_text,
                '_sort_value': deal['value']
            })
        
        # Add each Venture deal as a separate row
        for deal in venture_sorted:
            deal_type = f"Venture: {deal['funding_type']}"
            if deal['lead_investors'] != 'N/A' and deal['lead_investors'] != 'Undisclosed':
                deal_type += f", Lead: {deal['lead_investors']}"
            
            # Format amount
            if deal['raw_value'] != 'Undisclosed':
                deal_amount = f"${deal['value']:,.0f}"
            else:
                deal_amount = "Undisclosed"
            
            # Add quarter to amount
            deal_amount += f" ({deal['quarter']})"
            
            # Technology description
            tech_desc = deal['tech'] if deal['tech'] and deal['tech'] != 'N/A' and deal['tech'] != 'Undisclosed' else ""
            
            display_rows.append({
                'Company': company,
                'Deal Type': deal_type,
                'Deal Amount': deal_amount,
                'Technology / Company Description': tech_desc,
                'Category': categories_text,
                '_sort_value': deal['value']
            })
    
    # Sort all rows by deal value descending
    display_rows = sorted(display_rows, key=lambda x: x['_sort_value'], reverse=True)
    
    # === DISPLAY METRICS ===
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Companies", len(companies))
    with col2:
        total_ma = sum(len(c['ma_deals']) for c in companies.values())
        st.metric("M&A Deals", total_ma)
    with col3:
        total_venture = sum(len(c['venture_deals']) for c in companies.values())
        st.metric("Venture Deals", total_venture)
    
    st.markdown("---")
    
    # === DISPLAY TABLE ===
    st.markdown("### Companies with Recent Deal Activity")
    st.markdown(f"*Showing {len(display_rows)} deals from {len(companies)} companies*")
    
    # Create display dataframe
    display_data = []
    for row in display_rows:
        display_data.append({
            'Company': row['Company'],
            'Deal Type': row['Deal Type'],
            'Deal Amount': row['Deal Amount'],
            'Technology / Company Description': row['Technology / Company Description'],
            'Category': row['Category']
        })
    
    display_df = pd.DataFrame(display_data)
    
    # Check if there's data to display
    if display_df.empty:
        st.info("No deal data to display for the selected filters.")
        return
    
    # Display table with column configuration
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Company": st.column_config.TextColumn("Company", width="medium"),
            "Deal Type": st.column_config.TextColumn("Deal Type", width="large"),
            "Deal Amount": st.column_config.TextColumn("Deal Amount", width="medium"),
            "Technology / Company Description": st.column_config.TextColumn("Technology / Company Description", width="large"),
            "Category": st.column_config.TextColumn("Category", width="medium")
        }
    )
    
    st.markdown("---")
    
    # === CSV EXPORT ===
    st.markdown("### Export to CSV")
    
    csv = display_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"conference_deals_{'-'.join(selected_conferences[:2]).replace(' ', '_')}_{time_window.replace(' ', '_')}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )

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
    
    # Undo section
    st.markdown("### ↩️ Undo Last Upload")
    
    # Initialize backup_available in session state if not exists
    if 'backup_available' not in st.session_state:
        st.session_state.backup_available = False
    
    if st.session_state.get('backup_available', False):
        # Show backup info
        last_backup = st.session_state.get('last_backup_time', None)
        if last_backup:
            st.info(f"📦 Backup available from: {last_backup.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("📦 Backup available")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("↩️ Undo", type="primary", help="Restore the previous version of the data"):
                with st.spinner("Restoring backup..."):
                    success, message = undo_last_upload()
                    if success:
                        st.success(f"✅ {message}")
                        # Clear the cache to force reload of restored data
                        st.cache_data.clear()
                        st.success("🔄 Data restored! The dashboard will refresh automatically.")
                        st.balloons()
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        with col2:
            st.caption("This will restore the data to its state before the last upload.")
    else:
        st.info("ℹ️ No backup available. Upload a file to create a backup.")
    
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
                        
                        # Clean data - use '--' for Conference, 'Undisclosed' for other columns
                        for col in new_ma.columns:
                            if col == 'Conference':
                                new_ma[col] = new_ma[col].fillna('--')
                            else:
                                new_ma[col] = new_ma[col].fillna('Undisclosed')
                        
                        for col in new_inv.columns:
                            if col == 'Conference':
                                new_inv[col] = new_inv[col].fillna('--')
                            else:
                                new_inv[col] = new_inv[col].fillna('Undisclosed')
                        
                        if not new_ipo.empty:
                            new_ipo = new_ipo.fillna('Undisclosed')
                        
                        # Remove unnamed columns
                        new_ma = new_ma.loc[:, ~new_ma.columns.str.contains('^Unnamed')]
                        new_inv = new_inv.loc[:, ~new_inv.columns.str.contains('^Unnamed')]
                        if not new_ipo.empty:
                            new_ipo = new_ipo.loc[:, ~new_ipo.columns.str.contains('^Unnamed')]
                        
                        # Rename Sector to Category for display
                        if 'Sector' in new_ma.columns:
                            new_ma = new_ma.rename(columns={'Sector': 'Category'})
                        if 'Sector' in new_inv.columns:
                            new_inv = new_inv.rename(columns={'Sector': 'Category'})
                        
                        # Keep year in Quarter column for context
                        if 'Quarter' in new_ma.columns:
                            new_ma['Quarter'] = new_ma['Quarter'].astype(str)
                            new_ma['Quarter'] = new_ma['Quarter'].fillna('Undisclosed')
                        
                        if 'Quarter' in new_inv.columns:
                            new_inv['Quarter'] = new_inv['Quarter'].astype(str)
                            new_inv['Quarter'] = new_inv['Quarter'].fillna('Undisclosed')
                        
                        if not new_ipo.empty and 'Quarter' in new_ipo.columns:
                            new_ipo['Quarter'] = new_ipo['Quarter'].astype(str)
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
                            # Clear the cache to force reload of new data
                            st.cache_data.clear()
                            st.balloons()
                            st.markdown("---")
                            st.markdown("### ✅ Data Updated! The dashboard will refresh automatically.")
                            st.markdown("Reloading in 2 seconds...")
                            import time
                            time.sleep(2)
                            st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error processing upload: {str(e)}")
                        st.info("Make sure your Excel file has the correct sheet names and column structure")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please ensure the file has 'YTD M&A Activity' and 'YTD Investment Activity' sheets")

if __name__ == "__main__":
    main()