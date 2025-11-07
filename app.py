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
            st.session_state.backup_path = backup_path
            st.session_state.excel_path = excel_path
        
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
    """Restore data from backup file"""
    try:
        if 'backup_path' not in st.session_state or 'excel_path' not in st.session_state:
            st.error("❌ No backup found to restore from")
            return False
        
        backup_path = st.session_state.backup_path
        excel_path = st.session_state.excel_path
        
        if not os.path.exists(backup_path):
            st.error("❌ Backup file not found")
            return False
        
        # Restore from backup
        import shutil
        shutil.copy2(backup_path, excel_path)
        
        # Clear the undo flag
        st.session_state.can_undo_upload = False
        st.session_state.upload_just_completed = False
        
        # Clear cache to reload data
        st.cache_data.clear()
        
        return True
    except Exception as e:
        st.error(f"❌ Error restoring backup: {str(e)}")
        return False

def create_filter_section(df, section_key, show_conference=True):
    """Create filter section with checkboxes for quarters, subsectors, and deal values"""
    
    # Initialize session state for this section if not exists
    if f'{section_key}_filters_initialized' not in st.session_state:
        st.session_state[f'{section_key}_quarters'] = []
        st.session_state[f'{section_key}_subsectors'] = []
        st.session_state[f'{section_key}_deal_values'] = []
        st.session_state[f'{section_key}_conferences'] = []
        st.session_state[f'{section_key}_filters_initialized'] = True
    
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3) if not show_conference else st.columns(4)
        
        # Quarter filter
        with col1:
            st.markdown("**Quarter**")
            quarters = sorted([q for q in df['Quarter'].unique() if q != 'Undisclosed'])
            quarters = [q for q in ['Q1', 'Q2', 'Q3', 'Q4'] if q in quarters]
            
            for quarter in quarters:
                key = f"{section_key}_quarter_{quarter}"
                if st.checkbox(quarter, key=key):
                    if quarter not in st.session_state[f'{section_key}_quarters']:
                        st.session_state[f'{section_key}_quarters'].append(quarter)
                else:
                    if quarter in st.session_state[f'{section_key}_quarters']:
                        st.session_state[f'{section_key}_quarters'].remove(quarter)
        
        # Subsector filter
        with col2:
            st.markdown("**Subsector**")
            subsectors = sorted([s for s in df['Subsector'].unique() if s != 'Undisclosed'])
            
            for subsector in subsectors[:10]:  # Show first 10
                key = f"{section_key}_subsector_{subsector}"
                if st.checkbox(subsector, key=key):
                    if subsector not in st.session_state[f'{section_key}_subsectors']:
                        st.session_state[f'{section_key}_subsectors'].append(subsector)
                else:
                    if subsector in st.session_state[f'{section_key}_subsectors']:
                        st.session_state[f'{section_key}_subsectors'].remove(subsector)
        
        # Deal value filter (conditional based on column availability)
        with col3:
            value_column = 'Deal Value' if 'Deal Value' in df.columns else 'Amount Raised'
            st.markdown(f"**{value_column}**")
            
            # Create value ranges
            value_ranges = [
                ("< $50M", 0, 50),
                ("$50M - $100M", 50, 100),
                ("$100M - $500M", 100, 500),
                ("> $500M", 500, float('inf'))
            ]
            
            for label, min_val, max_val in value_ranges:
                key = f"{section_key}_value_{label}"
                if st.checkbox(label, key=key):
                    if label not in st.session_state[f'{section_key}_deal_values']:
                        st.session_state[f'{section_key}_deal_values'].append(label)
                else:
                    if label in st.session_state[f'{section_key}_deal_values']:
                        st.session_state[f'{section_key}_deal_values'].remove(label)
        
        # Conference filter (if show_conference is True)
        if show_conference and len(st.columns(4)) == 4:
            with st.columns(4)[3]:
                st.markdown("**Conference**")
                if 'Conference' in df.columns:
                    conferences = sorted([c for c in df['Conference'].unique() if c != 'Undisclosed'])
                    
                    for conference in conferences[:10]:  # Show first 10
                        key = f"{section_key}_conference_{conference}"
                        if st.checkbox(conference, key=key):
                            if conference not in st.session_state[f'{section_key}_conferences']:
                                st.session_state[f'{section_key}_conferences'].append(conference)
                        else:
                            if conference in st.session_state[f'{section_key}_conferences']:
                                st.session_state[f'{section_key}_conferences'].remove(conference)
        
        # Clear filters button
        if st.button("Clear All Filters", key=f"{section_key}_clear"):
            st.session_state[f'{section_key}_quarters'] = []
            st.session_state[f'{section_key}_subsectors'] = []
            st.session_state[f'{section_key}_deal_values'] = []
            st.session_state[f'{section_key}_conferences'] = []
            st.rerun()
    
    return (
        st.session_state[f'{section_key}_quarters'],
        st.session_state[f'{section_key}_subsectors'],
        st.session_state[f'{section_key}_deal_values'],
        st.session_state[f'{section_key}_conferences'] if show_conference else []
    )

def apply_filters(df, quarters, subsectors, deal_values, conferences=None, value_column='Deal Value'):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    # Apply quarter filter
    if quarters:
        filtered_df = filtered_df[filtered_df['Quarter'].isin(quarters)]
    
    # Apply subsector filter
    if subsectors:
        filtered_df = filtered_df[filtered_df['Subsector'].isin(subsectors)]
    
    # Apply deal value filter
    if deal_values:
        value_masks = []
        for label in deal_values:
            if label == "< $50M":
                mask = (filtered_df[value_column] != 'Undisclosed') & (pd.to_numeric(filtered_df[value_column], errors='coerce') < 50)
            elif label == "$50M - $100M":
                mask = (filtered_df[value_column] != 'Undisclosed') & (pd.to_numeric(filtered_df[value_column], errors='coerce') >= 50) & (pd.to_numeric(filtered_df[value_column], errors='coerce') <= 100)
            elif label == "$100M - $500M":
                mask = (filtered_df[value_column] != 'Undisclosed') & (pd.to_numeric(filtered_df[value_column], errors='coerce') > 100) & (pd.to_numeric(filtered_df[value_column], errors='coerce') <= 500)
            elif label == "> $500M":
                mask = (filtered_df[value_column] != 'Undisclosed') & (pd.to_numeric(filtered_df[value_column], errors='coerce') > 500)
            value_masks.append(mask)
        
        if value_masks:
            combined_mask = value_masks[0]
            for mask in value_masks[1:]:
                combined_mask = combined_mask | mask
            filtered_df = filtered_df[combined_mask]
    
    # Apply conference filter
    if conferences and 'Conference' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Conference'].isin(conferences)]
    
    return filtered_df

def show_ma_activity(ma_df):
    """Display M&A Activity page"""
    st.header("📊 M&A Activity")
    
    # Create filter section
    quarters, subsectors, deal_values, conferences = create_filter_section(ma_df, 'ma', show_conference=True)
    
    # Apply filters
    filtered_df = apply_filters(ma_df, quarters, subsectors, deal_values, conferences, 'Deal Value')
    
    # Summary metrics in cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_deals = len(filtered_df)
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color:#333;">Total M&A Deals</h3>
            <h1 style="margin:10px 0; color:#7FA8C9;">{total_deals}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        disclosed_values = filtered_df[filtered_df['Deal Value'] != 'Undisclosed']['Deal Value']
        if len(disclosed_values) > 0:
            total_value = pd.to_numeric(disclosed_values, errors='coerce').sum()
            avg_value = total_value / len(disclosed_values) if len(disclosed_values) > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:#333;">Total Deal Value</h3>
                <h1 style="margin:10px 0; color:#7FA8C9;">${total_value:,.0f}M</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:#333;">Total Deal Value</h3>
                <h1 style="margin:10px 0; color:#7FA8C9;">Undisclosed</h1>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        disclosed_values = filtered_df[filtered_df['Deal Value'] != 'Undisclosed']['Deal Value']
        if len(disclosed_values) > 0:
            avg_value = pd.to_numeric(disclosed_values, errors='coerce').mean()
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:#333;">Average Deal Value</h3>
                <h1 style="margin:10px 0; color:#7FA8C9;">${avg_value:,.0f}M</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; color:#333;">Average Deal Value</h3>
                <h1 style="margin:10px 0; color:#7FA8C9;">N/A</h1>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quarterly trend chart
    st.subheader("📈 Quarterly M&A Trend")
    chart = create_ma_quarterly_chart(filtered_df)
    if chart:
        st.plotly_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed table
    st.subheader("📋 Detailed M&A Transactions")
    
    # Display options
    col1, col2 = st.columns([3, 1])
    with col2:
        show_all = st.checkbox("Show all columns", value=False, key="ma_show_all")
    
    if show_all:
        display_df = filtered_df
    else:
        # Select key columns to display
        key_columns = ['Company', 'Acquirer', 'Deal Value', 'Quarter', 'Subsector']
        display_df = filtered_df[key_columns]
    
    # Display dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Export option
    if st.button("📥 Export to CSV", key="ma_export"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"ma_activity_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def show_venture_activity(inv_df):
    """Display Venture/Investment Activity page"""
    st.header("💰 Venture Investment Activity")
    
    # Create filter section
    quarters, subsectors, deal_values, _ = create_filter_section(inv_df, 'venture', show_conference=False)
    
    # Apply filters
    filtered_df = apply_filters(inv_df, quarters, subsectors, deal_values, value_column='Amount Raised')
    
    # Summary metrics in cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_deals = len(filtered_df)
        st.markdown(f"""
        <div class="metric-card metric-card-venture">
            <h3 style="margin:0; color:#333;">Total Investments</h3>
            <h1 style="margin:10px 0; color:#C9A77F;">{total_deals}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        disclosed_values = filtered_df[filtered_df['Amount Raised'] != 'Undisclosed']['Amount Raised']
        if len(disclosed_values) > 0:
            total_value = pd.to_numeric(disclosed_values, errors='coerce').sum()
            st.markdown(f"""
            <div class="metric-card metric-card-venture">
                <h3 style="margin:0; color:#333;">Total Capital Raised</h3>
                <h1 style="margin:10px 0; color:#C9A77F;">${total_value:,.0f}M</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card metric-card-venture">
                <h3 style="margin:0; color:#333;">Total Capital Raised</h3>
                <h1 style="margin:10px 0; color:#C9A77F;">Undisclosed</h1>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        disclosed_values = filtered_df[filtered_df['Amount Raised'] != 'Undisclosed']['Amount Raised']
        if len(disclosed_values) > 0:
            avg_value = pd.to_numeric(disclosed_values, errors='coerce').mean()
            st.markdown(f"""
            <div class="metric-card metric-card-venture">
                <h3 style="margin:0; color:#333;">Average Deal Size</h3>
                <h1 style="margin:10px 0; color:#C9A77F;">${avg_value:,.0f}M</h1>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card metric-card-venture">
                <h3 style="margin:0; color:#333;">Average Deal Size</h3>
                <h1 style="margin:10px 0; color:#C9A77F;">N/A</h1>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quarterly trend chart
    st.subheader("📈 Quarterly Investment Trend")
    chart = create_investment_quarterly_chart(filtered_df)
    if chart:
        st.plotly_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed table
    st.subheader("📋 Detailed Investment Transactions")
    
    # Display options
    col1, col2 = st.columns([3, 1])
    with col2:
        show_all = st.checkbox("Show all columns", value=False, key="venture_show_all")
    
    if show_all:
        display_df = filtered_df
    else:
        # Select key columns to display
        key_columns = ['Company', 'Amount Raised', 'Round', 'Quarter', 'Subsector']
        available_columns = [col for col in key_columns if col in filtered_df.columns]
        display_df = filtered_df[available_columns]
    
    # Display dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Export option
    if st.button("📥 Export to CSV", key="venture_export"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"venture_activity_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def show_jp_morgan_summary(ma_df, inv_df):
    """Display JP Morgan-style summary page"""
    st.header("📊 JP Morgan Healthcare Summary")
    
    st.markdown("""
    This page provides a comprehensive overview of MedTech M&A and Venture Capital activity,
    formatted in the style of JP Morgan's quarterly healthcare reports.
    """)
    
    # Create two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤝 M&A Activity")
        
        # M&A metrics
        total_ma = len(ma_df)
        disclosed_ma = ma_df[ma_df['Deal Value'] != 'Undisclosed']
        total_ma_value = pd.to_numeric(disclosed_ma['Deal Value'], errors='coerce').sum() if len(disclosed_ma) > 0 else 0
        
        st.metric("Total M&A Deals", total_ma)
        st.metric("Total Deal Value", f"${total_ma_value:,.0f}M")
        
        # M&A by quarter
        if 'Quarter' in ma_df.columns:
            ma_by_quarter = ma_df.groupby('Quarter').size().reset_index(name='Count')
            ma_by_quarter = ma_by_quarter[ma_by_quarter['Quarter'] != 'Undisclosed']
            ma_by_quarter = ma_by_quarter.sort_values('Quarter')
            
            st.markdown("**M&A Deals by Quarter**")
            st.dataframe(ma_by_quarter, hide_index=True, use_container_width=True)
        
        # Top subsectors
        if 'Subsector' in ma_df.columns:
            top_subsectors = ma_df['Subsector'].value_counts().head(5).reset_index()
            top_subsectors.columns = ['Subsector', 'Count']
            
            st.markdown("**Top 5 M&A Subsectors**")
            st.dataframe(top_subsectors, hide_index=True, use_container_width=True)
    
    with col2:
        st.subheader("💰 Venture Capital Activity")
        
        # VC metrics
        total_vc = len(inv_df)
        disclosed_vc = inv_df[inv_df['Amount Raised'] != 'Undisclosed']
        total_vc_value = pd.to_numeric(disclosed_vc['Amount Raised'], errors='coerce').sum() if len(disclosed_vc) > 0 else 0
        
        st.metric("Total VC Deals", total_vc)
        st.metric("Total Capital Raised", f"${total_vc_value:,.0f}M")
        
        # VC by quarter
        if 'Quarter' in inv_df.columns:
            vc_by_quarter = inv_df.groupby('Quarter').size().reset_index(name='Count')
            vc_by_quarter = vc_by_quarter[vc_by_quarter['Quarter'] != 'Undisclosed']
            vc_by_quarter = vc_by_quarter.sort_values('Quarter')
            
            st.markdown("**VC Deals by Quarter**")
            st.dataframe(vc_by_quarter, hide_index=True, use_container_width=True)
        
        # Top subsectors
        if 'Subsector' in inv_df.columns:
            top_subsectors = inv_df['Subsector'].value_counts().head(5).reset_index()
            top_subsectors.columns = ['Subsector', 'Count']
            
            st.markdown("**Top 5 VC Subsectors**")
            st.dataframe(top_subsectors, hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # Combined quarterly view
    st.subheader("📈 Combined Quarterly Activity")
    
    # Prepare quarterly data
    ma_quarterly = ma_df[ma_df['Quarter'] != 'Undisclosed'].groupby('Quarter').size().reset_index(name='M&A Deals')
    vc_quarterly = inv_df[inv_df['Quarter'] != 'Undisclosed'].groupby('Quarter').size().reset_index(name='VC Deals')
    
    combined_quarterly = pd.merge(ma_quarterly, vc_quarterly, on='Quarter', how='outer').fillna(0)
    combined_quarterly = combined_quarterly.sort_values('Quarter')
    
    # Create combined chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=combined_quarterly['Quarter'],
        y=combined_quarterly['M&A Deals'],
        name='M&A Deals',
        marker_color=COLORS['ma_primary']
    ))
    
    fig.add_trace(go.Bar(
        x=combined_quarterly['Quarter'],
        y=combined_quarterly['VC Deals'],
        name='VC Deals',
        marker_color=COLORS['venture_primary']
    ))
    
    fig.update_layout(
        barmode='group',
        title='M&A vs Venture Capital Activity by Quarter',
        xaxis_title='Quarter',
        yaxis_title='Number of Deals',
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_ipo_activity(ipo_df):
    """Display IPO Activity page"""
    st.header("🚀 IPO Activity")
    
    if ipo_df.empty:
        st.info("📊 No IPO data available")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_ipos = len(ipo_df)
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color:#333;">Total IPOs</h3>
            <h1 style="margin:10px 0; color:#7FA8C9;">{total_ipos}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if 'IPO Value' in ipo_df.columns:
            disclosed_values = ipo_df[ipo_df['IPO Value'] != 'Undisclosed']['IPO Value']
            if len(disclosed_values) > 0:
                total_value = pd.to_numeric(disclosed_values, errors='coerce').sum()
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color:#333;">Total IPO Value</h3>
                    <h1 style="margin:10px 0; color:#7FA8C9;">${total_value:,.0f}M</h1>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color:#333;">Total IPO Value</h3>
                    <h1 style="margin:10px 0; color:#7FA8C9;">Undisclosed</h1>
                </div>
                """, unsafe_allow_html=True)
    
    with col3:
        if 'IPO Value' in ipo_df.columns:
            disclosed_values = ipo_df[ipo_df['IPO Value'] != 'Undisclosed']['IPO Value']
            if len(disclosed_values) > 0:
                avg_value = pd.to_numeric(disclosed_values, errors='coerce').mean()
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color:#333;">Average IPO Value</h3>
                    <h1 style="margin:10px 0; color:#7FA8C9;">${avg_value:,.0f}M</h1>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color:#333;">Average IPO Value</h3>
                    <h1 style="margin:10px 0; color:#7FA8C9;">N/A</h1>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quarterly chart
    st.subheader("📈 Quarterly IPO Trend")
    chart = create_ipo_quarterly_chart(ipo_df)
    if chart:
        st.plotly_chart(chart, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed table
    st.subheader("📋 IPO Details")
    st.dataframe(ipo_df, use_container_width=True, hide_index=True, height=400)

def create_ma_quarterly_chart(df):
    """Create M&A quarterly chart with both value and count"""
    try:
        # Filter out undisclosed quarters
        df_filtered = df[df['Quarter'] != 'Undisclosed'].copy()
        
        if len(df_filtered) == 0:
            st.info("No quarterly data available")
            return None
        
        # Group by quarter
        quarterly_data = df_filtered.groupby('Quarter').agg({
            'Deal Value': lambda x: pd.to_numeric(x[x != 'Undisclosed'], errors='coerce').sum()
        }).reset_index()
        
        # Add deal count
        deal_counts = df_filtered.groupby('Quarter').size().reset_index(name='Deal_Count')
        quarterly_data = quarterly_data.merge(deal_counts, on='Quarter')
        
        # Sort by quarter
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarterly_data['Quarter'] = pd.Categorical(quarterly_data['Quarter'], categories=quarter_order, ordered=True)
        quarterly_data = quarterly_data.sort_values('Quarter')
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add bar chart for deal values
        fig.add_trace(go.Bar(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Deal Value'],
            name='Deal Value (USD)',
            marker_color=COLORS['ma_primary'],
            text=quarterly_data['Deal Value'].apply(lambda x: f'${x:,.0f}M' if x > 0 else ''),
            textposition='outside',
            textfont=dict(size=13, color='#333'),
            hovertemplate='<b>%{x}</b><br>Deal Value: $%{y:,.0f}M<extra></extra>',
            yaxis='y'
        ))
        
        # Add line chart for deal count on secondary axis
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Deal_Count'],
            name='Number of Deals',
            mode='lines+markers+text',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line'], line=dict(width=2, color='white')),
            text=quarterly_data['Deal_Count'],
            textposition='top center',
            textfont=dict(size=13, color='#333', family='Arial Black, sans-serif'),
            hovertemplate='<b>%{x}</b><br>Number of Deals: %{y}<extra></extra>',
            yaxis='y2'
        ))
        
        # Update layout with modern styling
        fig.update_layout(
            title=dict(text='M&A Activity by Quarter', font=dict(size=20, color='#333', family='Arial, sans-serif')),
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),
                showgrid=False,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(text='Total Deal Value (USD)', font=dict(size=16)),
                side='left',
                showgrid=False,
                range=[0, max(quarterly_data['Deal Value']) * 1.35] if len(quarterly_data) > 0 else [0, 1000],
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
        st.error(f"Error creating M&A chart: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def create_investment_quarterly_chart(df):
    """Create Investment quarterly chart with both value and count"""
    try:
        # Filter out undisclosed quarters
        df_filtered = df[df['Quarter'] != 'Undisclosed'].copy()
        
        if len(df_filtered) == 0:
            st.info("No quarterly data available")
            return None
        
        # Group by quarter
        quarterly_data = df_filtered.groupby('Quarter').agg({
            'Amount Raised': lambda x: pd.to_numeric(x[x != 'Undisclosed'], errors='coerce').sum()
        }).reset_index()
        
        # Rename for consistency
        quarterly_data.columns = ['Quarter', 'Total_Amount']
        
        # Add deal count
        deal_counts = df_filtered.groupby('Quarter').size().reset_index(name='Investment_Count')
        quarterly_data = quarterly_data.merge(deal_counts, on='Quarter')
        
        # Sort by quarter
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarterly_data['Quarter'] = pd.Categorical(quarterly_data['Quarter'], categories=quarter_order, ordered=True)
        quarterly_data = quarterly_data.sort_values('Quarter')
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add bar chart for investment amounts
        fig.add_trace(go.Bar(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Total_Amount'],
            name='Capital Raised (USD)',
            marker_color=COLORS['venture_primary'],
            text=quarterly_data['Total_Amount'].apply(lambda x: f'${x:,.0f}M' if x > 0 else ''),
            textposition='outside',
            textfont=dict(size=13, color='#333'),
            hovertemplate='<b>%{x}</b><br>Capital Raised: $%{y:,.0f}M<extra></extra>',
            yaxis='y'
        ))
        
        # Add line chart for investment count on secondary axis
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Investment_Count'],
            name='Number of Investments',
            mode='lines+markers+text',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line'], line=dict(width=2, color='white')),
            text=quarterly_data['Investment_Count'],
            textposition='top center',
            textfont=dict(size=13, color='#333', family='Arial Black, sans-serif'),
            hovertemplate='<b>%{x}</b><br>Number of Investments: %{y}<extra></extra>',
            yaxis='y2'
        ))
        
        # Update layout with modern styling
        fig.update_layout(
            title=dict(text='Investment Activity by Quarter', font=dict(size=20, color='#333', family='Arial, sans-serif')),
            xaxis=dict(
                title=dict(text='Quarter', font=dict(size=16)),
                showgrid=False,
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                title=dict(text='Total Capital Raised (USD)', font=dict(size=16)),
                side='left',
                showgrid=False,
                range=[0, max(quarterly_data['Total_Amount']) * 1.35] if len(quarterly_data) > 0 else [0, 1000],
                tickfont=dict(size=13)
            ),
            yaxis2=dict(
                title=dict(text='Number of Investments', font=dict(size=16)),
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(quarterly_data['Investment_Count']) * 1.5] if len(quarterly_data) > 0 else [0, 10],
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
        st.error(f"Error creating Investment chart: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def create_ipo_quarterly_chart(df):
    """Create IPO quarterly chart"""
    try:
        # Filter out undisclosed quarters
        df_filtered = df[df['Quarter'] != 'Undisclosed'].copy()
        
        if len(df_filtered) == 0:
            st.info("No quarterly data available")
            return None
        
        # Determine value column
        value_col = 'IPO Value' if 'IPO Value' in df_filtered.columns else 'Amount Raised'
        
        # Group by quarter
        quarterly_data = df_filtered.groupby('Quarter').agg({
            value_col: lambda x: pd.to_numeric(x[x != 'Undisclosed'], errors='coerce').sum()
        }).reset_index()
        
        quarterly_data.columns = ['Quarter', 'Total_Amount']
        
        # Add IPO count
        ipo_counts = df_filtered.groupby('Quarter').size().reset_index(name='IPO_Count')
        quarterly_data = quarterly_data.merge(ipo_counts, on='Quarter')
        
        # Sort by quarter
        quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarterly_data['Quarter'] = pd.Categorical(quarterly_data['Quarter'], categories=quarter_order, ordered=True)
        quarterly_data = quarterly_data.sort_values('Quarter')
        
        # Create figure
        fig = go.Figure()
        
        # Add bar chart for IPO values
        fig.add_trace(go.Bar(
            x=quarterly_data['Quarter'],
            y=quarterly_data['Total_Amount'],
            name='IPO Value (USD)',
            marker_color=COLORS['ma_primary'],
            text=quarterly_data['Total_Amount'].apply(lambda x: f'${x:,.0f}M' if x > 0 else ''),
            textposition='outside',
            textfont=dict(size=13, color='#333'),
            hovertemplate='<b>%{x}</b><br>IPO Value: $%{y:,.0f}M<extra></extra>',
            yaxis='y'
        ))
        
        # Add line for count
        fig.add_trace(go.Scatter(
            x=quarterly_data['Quarter'],
            y=quarterly_data['IPO_Count'],
            name='Number of IPOs',
            mode='lines+markers+text',
            line=dict(color=COLORS['count_line'], width=3),
            marker=dict(size=10, color=COLORS['count_line']),
            text=quarterly_data['IPO_Count'],
            textposition='top center',
            textfont=dict(size=13, color='#333'),
            yaxis='y2'
        ))
        
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
                range=[0, max(quarterly_data['Total_Amount']) * 1.35] if len(quarterly_data) > 0 else [0, 1000],  # Increased for label space
                tickfont=dict(size=13)
            ),
            yaxis2=dict(
                title=dict(text='Number of IPOs', font=dict(size=16)),  # Modern syntax
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(quarterly_data['IPO_Count']) * 1.5] if len(quarterly_data) > 0 else [0, 10],  # Increased for label space
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
    """Password-protected data upload page with undo functionality"""
    st.header("📤 Upload New Dataset")
    
    # Initialize session state for undo functionality
    if 'can_undo_upload' not in st.session_state:
        st.session_state.can_undo_upload = False
    if 'upload_just_completed' not in st.session_state:
        st.session_state.upload_just_completed = False
    
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
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # Show undo button if upload just completed
        if st.session_state.can_undo_upload:
            st.warning("⚠️ You just uploaded a dataset. You can undo this action.")
            if st.button("↩️ Undo Last Upload", type="secondary", use_container_width=True):
                with st.spinner("Restoring previous data..."):
                    if undo_last_upload():
                        st.success("✅ Upload undone successfully! Previous data restored.")
                        st.balloons()
                        st.info("🔄 Please refresh the page to see the restored data.")
                        time.sleep(2)
                        st.rerun()
    
    with col2:
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
    4. Use **Undo** if you need to revert the upload
    5. **Refresh the page** to see updated data
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
                            
                            # Enable undo for this session
                            st.session_state.can_undo_upload = True
                            st.session_state.upload_just_completed = True
                            
                            st.markdown("---")
                            st.markdown("### ✅ Upload Complete")
                            st.markdown("- ↩️ Click **Undo Last Upload** above if you need to revert")
                            st.markdown("- 🔄 **Refresh the page** to see updated data")
                            st.markdown("- 💾 Changes are saved and will persist after refresh")
                        
                    except Exception as e:
                        st.error(f"❌ Error processing upload: {str(e)}")
                        st.info("Make sure your Excel file has the correct sheet names and column structure")
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            st.info("Please ensure the file has 'YTD M&A Activity' and 'YTD Investment Activity' sheets")

def main():
    """Main application"""
    
    # Load data
    ma_df, inv_df, ipo_df = load_data()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Create navigation with radio buttons
    page = st.sidebar.radio(
        "Select a page:",
        ["📊 Deal Activity", "📋 JP Morgan Summary", "🏛️ IPO Activity", "📤 Upload New Dataset"],
        label_visibility="collapsed"
    )
    
    # Show selected page
    if page == "📊 Deal Activity":
        # Sub-navigation for Deal Activity
        deal_type = st.sidebar.radio(
            "Deal Type:",
            ["M&A Activity", "Venture Investment"],
            key="deal_type_radio"
        )
        
        if deal_type == "M&A Activity":
            show_ma_activity(ma_df)
        else:
            show_venture_activity(inv_df)
    
    elif page == "📋 JP Morgan Summary":
        show_jp_morgan_summary(ma_df, inv_df)
    
    elif page == "🏛️ IPO Activity":
        show_ipo_activity(ipo_df)
    
    elif page == "📤 Upload New Dataset":
        show_upload_dataset(ma_df, inv_df, ipo_df)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "MedTech M&A & Venture Dashboard\n\n"
        "Track and analyze medical technology deals, investments, and IPOs."
    )

if __name__ == "__main__":
    main()