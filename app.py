import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="MedTech M&A & Venture Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for muted colors and clean design
st.markdown("""
<style>
    .dataframe {
        width: 100% !important;
    }
    div[data-testid="stDataFrame"] > div {
        width: 100% !important;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Data loading function
@st.cache_data
def load_data():
    """Load data from Excel file"""
    try:
        excel_path = 'MedTech_Deals.xlsx'
        
        if not os.path.exists(excel_path):
            st.error(f"❌ Cannot find {excel_path}. Please ensure the file is in the same directory as app.py")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Load data
        ma_df = pd.read_excel(excel_path, sheet_name='YTD M&A Activity')
        inv_df = pd.read_excel(excel_path, sheet_name='YTD Investment Activity')
        ipo_df = pd.read_excel(excel_path, sheet_name='YTD IPO')
        
        # Clean data
        ma_df = ma_df.fillna('Undisclosed')
        inv_df = inv_df.fillna('Undisclosed')
        ipo_df = ipo_df.fillna('Undisclosed')
        
        return ma_df, inv_df, ipo_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def parse_deal_value(value):
    """Parse deal value to numeric"""
    if pd.isna(value) or value == 'Undisclosed':
        return 0
    try:
        value_str = str(value).replace('$', '').replace(',', '').strip()
        return float(value_str)
    except:
        return 0

def format_currency(value):
    """Format currency values"""
    if value == 0 or pd.isna(value):
        return 'Undisclosed'
    if value >= 1000000000:
        return f"${value/1000000000:.1f}B"
    elif value >= 1000000:
        return f"${value/1000000:.0f}M"
    else:
        return f"${value:,.0f}"

# Main app
def main():
    st.title("🏥 MedTech M&A, Venture & IPO Dashboard")
    
    # Load data
    ma_df, inv_df, ipo_df = load_data()
    
    # Sidebar filters
    st.sidebar.title("Filters")
    
    # Get unique values for filters
    all_quarters = sorted(set(list(ma_df['Quarter'].unique()) + list(inv_df['Quarter'].unique())))
    all_sectors = sorted(set(list(ma_df['Sector'].unique()) + list(inv_df['Sector'].unique())))
    
    # Time period filter
    quarters = st.sidebar.multiselect(
        "Quarter",
        options=all_quarters,
        default=all_quarters
    )
    
    # Sector filter
    sectors = st.sidebar.multiselect(
        "Sector",
        options=all_sectors,
        default=all_sectors
    )
    
    # Geography filter (if applicable - placeholder)
    # geography = st.sidebar.multiselect("Geography", options=["North America", "Europe", "Asia"], default=["North America", "Europe", "Asia"])
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home (Summary)", "📋 Deals (Tables)", "📊 JP Morgan", "🚀 IPO"])
    
    with tab1:
        show_home_summary(ma_df, inv_df, quarters, sectors)
    
    with tab2:
        show_deals_tables(ma_df, inv_df, quarters, sectors)
    
    with tab3:
        show_jp_morgan_summary()
    
    with tab4:
        show_ipo_tab(ipo_df, quarters, sectors)
    
    # Upload section at the bottom
    st.markdown("---")
    show_upload_section()

def show_home_summary(ma_df, inv_df, quarters, sectors):
    """Home page with split-screen M&A and Venture"""
    
    # Filter data
    ma_filtered = ma_df[ma_df['Quarter'].isin(quarters) & ma_df['Sector'].isin(sectors)]
    inv_filtered = inv_df[inv_df['Quarter'].isin(quarters) & inv_df['Sector'].isin(sectors)]
    
    # Create two columns
    col_ma, col_venture = st.columns(2)
    
    with col_ma:
        st.markdown("### M&A Activity")
        
        # KPI Cards
        ma_deals = len(ma_filtered)
        ma_value = ma_filtered['Deal Value'].apply(parse_deal_value).sum()
        ma_avg = ma_value / ma_deals if ma_deals > 0 else 0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("Total Deals YTD", f"{ma_deals}")
        with kpi2:
            st.metric("Total Value YTD", format_currency(ma_value))
        with kpi3:
            st.metric("Avg Deal Size", format_currency(ma_avg))
        
        # Top 3 M&A Deals
        st.markdown("#### 🏆 Top 3 M&A Deals")
        ma_sorted = ma_filtered.copy()
        ma_sorted['Deal_Value_Numeric'] = ma_sorted['Deal Value'].apply(parse_deal_value)
        top_ma = ma_sorted.nlargest(3, 'Deal_Value_Numeric')
        
        for idx, row in top_ma.iterrows():
            st.markdown(f"**{row['Acquirer']} acquired {row['Company']}**")
            st.markdown(f"<h3 style='color: #4A90E2;'>{format_currency(row['Deal_Value_Numeric'])}</h3>", unsafe_allow_html=True)
            st.markdown("---")
        
        # Top 3 Sectors by Deal Count
        st.markdown("#### 📊 Top 3 Sectors (Deal Count)")
        sector_counts = ma_filtered['Sector'].value_counts().head(3)
        for sector, count in sector_counts.items():
            st.write(f"• {sector}: {count} deals")
        
        # Charts
        st.markdown("#### Deal Value by Sector")
        sector_value = ma_filtered.groupby('Sector')['Deal Value'].apply(
            lambda x: x.apply(parse_deal_value).sum()
        ).sort_values(ascending=False)
        
        fig = go.Figure(data=[go.Bar(
            x=sector_value.values,
            y=sector_value.index,
            orientation='h',
            marker_color='#4A90E2'
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_venture:
        st.markdown("### Venture Investment Activity")
        
        # KPI Cards
        inv_deals = len(inv_filtered)
        inv_value = inv_filtered['Amount Raised'].apply(parse_deal_value).sum()
        
        kpi1, kpi2 = st.columns(2)
        with kpi1:
            st.metric("Total Deals YTD", f"{inv_deals}")
        with kpi2:
            st.metric("Total Value YTD", format_currency(inv_value))
        
        # Top 3 Venture Deals
        st.markdown("#### 🏆 Top 3 Venture Deals")
        inv_sorted = inv_filtered.copy()
        inv_sorted['Amount_Numeric'] = inv_sorted['Amount Raised'].apply(parse_deal_value)
        top_inv = inv_sorted.nlargest(3, 'Amount_Numeric')
        
        for idx, row in top_inv.iterrows():
            st.markdown(f"**{row['Company']}**")
            st.markdown(f"<h3 style='color: #FFA500;'>{format_currency(row['Amount_Numeric'])}</h3>", unsafe_allow_html=True)
            st.markdown("---")
        
        # Top 3 Sectors by Deal Count
        st.markdown("#### 📊 Top 3 Sectors (Deal Count)")
        sector_counts_inv = inv_filtered['Sector'].value_counts().head(3)
        for sector, count in sector_counts_inv.items():
            st.write(f"• {sector}: {count} deals")
        
        # Charts
        st.markdown("#### Deal Value by Sector")
        sector_value_inv = inv_filtered.groupby('Sector')['Amount Raised'].apply(
            lambda x: x.apply(parse_deal_value).sum()
        ).sort_values(ascending=False)
        
        fig = go.Figure(data=[go.Bar(
            x=sector_value_inv.values,
            y=sector_value_inv.index,
            orientation='h',
            marker_color='#FFA500'
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

def show_deals_tables(ma_df, inv_df, quarters, sectors):
    """Deals tables matching existing style"""
    
    # M&A Deals
    st.subheader("M&A Deals")
    
    # Filter data
    ma_filtered = ma_df[ma_df['Quarter'].isin(quarters) & ma_df['Sector'].isin(sectors)]
    
    # Sort by deal value
    ma_display = ma_filtered.copy()
    ma_display['_Deal_Value_Numeric'] = ma_display['Deal Value'].apply(parse_deal_value)
    ma_display = ma_display.sort_values('_Deal_Value_Numeric', ascending=False)
    
    display_cols = [col for col in ma_display.columns if not col.startswith('_')]
    st.dataframe(ma_display[display_cols], use_container_width=True, height=400)
    
    st.markdown("---")
    
    # Venture Deals
    st.subheader("Venture Investment Deals")
    
    # Filter data
    inv_filtered = inv_df[inv_df['Quarter'].isin(quarters) & inv_df['Sector'].isin(sectors)]
    
    # Sort by amount
    inv_display = inv_filtered.copy()
    inv_display['_Amount_Numeric'] = inv_display['Amount Raised'].apply(parse_deal_value)
    inv_display = inv_display.sort_values('_Amount_Numeric', ascending=False)
    
    # Format for display
    inv_display['Amount Raised'] = inv_display['_Amount_Numeric'].apply(format_currency)
    
    display_cols = [col for col in inv_display.columns if not col.startswith('_')]
    st.dataframe(inv_display[display_cols], use_container_width=True, height=400)

def show_jp_morgan_summary():
    """JP Morgan summary from PDFs"""
    st.header("JP Morgan MedTech Industry Report")
    
    st.markdown("### 2025 Q1-Q3 Activity")
    
    # Create 1x2 grid for charts
    col1, col2 = st.columns(2)
    
    # M&A Data from PDFs
    with col1:
        st.markdown("#### M&A Activity")
        
        quarters = ['Q1', 'Q2', 'Q3']
        ma_values = [9200, 2100, 21700]  # Millions
        ma_counts = [57, 43, 65]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=quarters,
            y=ma_values,
            name='Deal Value ($M)',
            marker_color='#4A90E2',
            text=[f"${v:,}M" for v in ma_values],
            textposition='outside',
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=quarters,
            y=ma_counts,
            name='Deal Count',
            mode='lines+markers+text',
            line=dict(color='#90EE90', width=3),
            marker=dict(size=10),
            text=ma_counts,
            textposition='top center',
            yaxis='y2'
        ))
        
        fig.update_layout(
            yaxis=dict(title='Deal Value (Millions USD)', side='left'),
            yaxis2=dict(title='Number of Deals', overlaying='y', side='right'),
            height=350,
            showlegend=True,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Venture Data from PDFs
    with col2:
        st.markdown("#### Venture Activity")
        
        vc_values = [3700, 2600, 2900]  # Millions
        vc_counts = [117, 90, 67]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=quarters,
            y=vc_values,
            name='Deal Value ($M)',
            marker_color='#FFA500',
            text=[f"${v:,}M" for v in vc_values],
            textposition='outside',
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=quarters,
            y=vc_counts,
            name='Deal Count',
            mode='lines+markers+text',
            line=dict(color='#90EE90', width=3),
            marker=dict(size=10),
            text=vc_counts,
            textposition='top center',
            yaxis='y2'
        ))
        
        fig.update_layout(
            yaxis=dict(title='Deal Value (Millions USD)', side='left'),
            yaxis2=dict(title='Number of Deals', overlaying='y', side='right'),
            height=350,
            showlegend=True,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Key Trends
    st.markdown("---")
    st.subheader("Key Market Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**M&A Activity**")
        st.markdown("• **Q1 2025**: 57 medtech M&A deals totaling $9.2B")
        st.markdown("• **Q2 2025**: 43 medtech M&A deals totaling $2.1B")
        st.markdown("• **Q3 2025**: 65 medtech M&A deals totaling $21.7B")
        st.markdown("**Trend**: Strategic consolidation driving large-scale transactions")
    
    with col2:
        st.markdown("**Venture Capital**")
        st.markdown("• **Q1 2025**: $3.7B across 117 rounds, exceeding Q1 2024")
        st.markdown("• **Q2 2025**: $2.6B across 90 rounds")
        st.markdown("• **Q3 2025**: $2.9B across 67 rounds")
        st.markdown("**Trend**: Late-stage rounds dominate; early-stage remains selective")
    
    # Signal Cards
    st.markdown("---")
    st.subheader("📡 Market Signals")
    
    signal1, signal2, signal3, signal4 = st.columns(4)
    
    with signal1:
        st.info("🤖 **Surgical Robotics Consolidation**\n\nIncreased M&A activity in robotic surgery platforms")
    
    with signal2:
        st.info("🧠 **AI-Driven Diagnostics Surge**\n\nVenture funding flowing to AI diagnostic companies")
    
    with signal3:
        st.info("💰 **Value-Based Care Adoption**\n\nGrowing investment in outcomes-focused solutions")
    
    with signal4:
        st.info("🏭 **Manufacturing Reshoring**\n\nSupply chain resilience driving domestic production")

def show_ipo_tab(ipo_df, quarters, sectors):
    """IPO tab"""
    st.header("IPO Activity")
    
    # Filter data
    ipo_filtered = ipo_df.copy()
    if 'Quarter' in ipo_df.columns:
        ipo_filtered = ipo_df[ipo_df['Quarter'].isin(quarters)]
    
    # KPI Cards
    ipo_count = len(ipo_filtered)
    ipo_value = ipo_filtered['Amount'].apply(parse_deal_value).sum()
    ipo_avg = ipo_value / ipo_count if ipo_count > 0 else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Total IPOs YTD", f"{ipo_count}")
    with kpi2:
        st.metric("Total Proceeds", format_currency(ipo_value))
    with kpi3:
        st.metric("Avg Proceeds", format_currency(ipo_avg))
    
    # Table
    st.markdown("### IPO Details")
    ipo_display = ipo_filtered.copy()
    ipo_display['_Amount_Numeric'] = ipo_display['Amount'].apply(parse_deal_value)
    ipo_display = ipo_display.sort_values('_Amount_Numeric', ascending=False)
    
    display_cols = [col for col in ipo_display.columns if not col.startswith('_')]
    st.dataframe(ipo_display[display_cols], use_container_width=True, height=400)

def show_upload_section():
    """Password-protected upload section"""
    st.subheader("🔒 Upload New Dataset")
    
    password = st.text_input("Enter Password", type="password", key="upload_password")
    
    if password == "BeaconOne":
        st.success("✅ Access granted")
        
        uploaded_file = st.file_uploader("Upload MedTech_Deals.xlsx", type=['xlsx'])
        
        if uploaded_file:
            upload_mode = st.radio("Upload Mode", ["Append New Deals", "Replace Entire File"])
            
            if st.button("Upload"):
                try:
                    if upload_mode == "Replace Entire File":
                        # Save uploaded file
                        with open('MedTech_Deals.xlsx', 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        st.success("✅ File replaced successfully! Please refresh the page.")
                    else:
                        # Append mode
                        new_ma = pd.read_excel(uploaded_file, sheet_name='YTD M&A Activity')
                        new_inv = pd.read_excel(uploaded_file, sheet_name='YTD Investment Activity')
                        new_ipo = pd.read_excel(uploaded_file, sheet_name='YTD IPO')
                        
                        existing_ma, existing_inv, existing_ipo = load_data()
                        
                        combined_ma = pd.concat([existing_ma, new_ma], ignore_index=True).drop_duplicates()
                        combined_inv = pd.concat([existing_inv, new_inv], ignore_index=True).drop_duplicates()
                        combined_ipo = pd.concat([existing_ipo, new_ipo], ignore_index=True).drop_duplicates()
                        
                        with pd.ExcelWriter('MedTech_Deals.xlsx', engine='openpyxl') as writer:
                            combined_ma.to_excel(writer, sheet_name='YTD M&A Activity', index=False)
                            combined_inv.to_excel(writer, sheet_name='YTD Investment Activity', index=False)
                            combined_ipo.to_excel(writer, sheet_name='YTD IPO', index=False)
                        
                        st.success("✅ Data appended successfully! Please refresh the page.")
                        st.cache_data.clear()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    elif password:
        st.error("❌ Incorrect password")

if __name__ == "__main__":
    main()
