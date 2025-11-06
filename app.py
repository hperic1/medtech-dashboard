import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Page configuration
st.set_page_config(
    page_title="MedTech M&A & Venture Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .dataframe {
        width: 100% !important;
    }
    div[data-testid="stDataFrame"] > div {
        width: 100% !important;
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
        
        # Clean data and remove unnamed columns
        ma_df = ma_df.fillna('Undisclosed')
        inv_df = inv_df.fillna('Undisclosed')
        ipo_df = ipo_df.fillna('Undisclosed')
        
        # Drop unnamed columns
        ma_df = ma_df.loc[:, ~ma_df.columns.str.contains('^Unnamed')]
        inv_df = inv_df.loc[:, ~inv_df.columns.str.contains('^Unnamed')]
        ipo_df = ipo_df.loc[:, ~ipo_df.columns.str.contains('^Unnamed')]
        
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
    """Format currency values with full dollar amounts"""
    if value == 0 or pd.isna(value):
        return 'Undisclosed'
    return f"${value:,.0f}"

def format_currency_short(value):
    """Format currency values for display"""
    if value == 0 or pd.isna(value):
        return 'Undisclosed'
    if value >= 1000000000:
        return f"${value/1000000000:.1f}B"
    elif value >= 1000000:
        return f"${value/1000000:.0f}M"
    else:
        return f"${value:,.0f}"

def create_deal_chart(df, value_col, title, color, quarters_filter=None, sectors_filter=None):
    """Create chart with deal value bars and deal count line"""
    # Filter data
    filtered_df = df.copy()
    if quarters_filter:
        filtered_df = filtered_df[filtered_df['Quarter'].isin(quarters_filter)]
    if sectors_filter:
        filtered_df = filtered_df[filtered_df['Sector'].isin(sectors_filter)]
    
    # Group by quarter
    quarterly_data = filtered_df.groupby('Quarter').agg({
        value_col: lambda x: sum([parse_deal_value(v) for v in x]),
        'Company': 'count'
    }).reset_index()
    quarterly_data.columns = ['Quarter', 'Total_Value', 'Deal_Count']
    
    # Sort quarters
    quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
    quarterly_data['Quarter'] = pd.Categorical(quarterly_data['Quarter'], categories=quarter_order, ordered=True)
    quarterly_data = quarterly_data.sort_values('Quarter')
    
    # Create figure
    fig = go.Figure()
    
    # Add bar chart for deal values
    fig.add_trace(go.Bar(
        x=quarterly_data['Quarter'],
        y=quarterly_data['Total_Value'],
        name='Deal Value',
        marker_color=color,
        text=[format_currency(v) for v in quarterly_data['Total_Value']],
        textposition='outside',
        yaxis='y',
        hovertemplate='<b>%{x}</b><br>Deal Value: %{text}<br><extra></extra>'
    ))
    
    # Add line chart for deal count
    fig.add_trace(go.Scatter(
        x=quarterly_data['Quarter'],
        y=quarterly_data['Deal_Count'],
        name='Deal Count',
        mode='lines+markers+text',
        line=dict(color='#90EE90', width=3),
        marker=dict(size=10),
        text=quarterly_data['Deal_Count'],
        textposition='top center',
        yaxis='y2',
        hovertemplate='<b>%{x}</b><br>Deal Count: %{y}<br><extra></extra>'
    ))
    
    # Update layout - remove gridlines and adjust axes
    max_value = max(quarterly_data['Total_Value']) if len(quarterly_data) > 0 else 100
    max_count = max(quarterly_data['Deal_Count']) if len(quarterly_data) > 0 else 10
    
    fig.update_layout(
        title=title,
        xaxis=dict(title='Quarter', showgrid=False),
        yaxis=dict(
            title='Total Deal Value (USD)',
            side='left',
            showgrid=False,
            range=[0, max_value * 1.3]
        ),
        yaxis2=dict(
            title='Number of Deals',
            overlaying='y',
            side='right',
            showgrid=False,
            range=[0, max_count * 1.4]
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
        margin=dict(t=80, b=50, l=80, r=80)
    )
    
    return fig

# Main app
def main():
    st.title("🏥 MedTech M&A, Venture & IPO Dashboard")
    
    # Load data
    ma_df, inv_df, ipo_df = load_data()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home (Summary)", "📋 Deals (Tables)", "📊 JP Morgan", "🚀 IPO", "📤 Upload"])
    
    with tab1:
        show_home_summary(ma_df, inv_df)
    
    with tab2:
        show_deals_tables(ma_df, inv_df)
    
    with tab3:
        show_jp_morgan_summary()
    
    with tab4:
        show_ipo_tab(ipo_df)
    
    with tab5:
        show_upload_section()

def show_home_summary(ma_df, inv_df):
    """Home page with charts at top and split-screen summary"""
    
    # Get all quarters and sectors for default filters
    all_quarters = sorted(set(list(ma_df['Quarter'].unique()) + list(inv_df['Quarter'].unique())))
    all_sectors = sorted(set(list(ma_df['Sector'].unique()) + list(inv_df['Sector'].unique())))
    
    # Filters at top
    st.markdown("### 🔍 Filters")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        quarters_filter = st.multiselect("Quarter", options=all_quarters, default=all_quarters, key="home_quarters")
    with col_f2:
        sectors_filter = st.multiselect("Sector", options=all_sectors, default=all_sectors, key="home_sectors")
    
    st.markdown("---")
    
    # Charts at top - side by side
    st.markdown("### 📊 YTD Activity Overview")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        fig_ma = create_deal_chart(ma_df, 'Deal Value', 'M&A Activity by Quarter', '#4A90E2', quarters_filter, sectors_filter)
        st.plotly_chart(fig_ma, use_container_width=True)
    
    with chart_col2:
        fig_inv = create_deal_chart(inv_df, 'Amount Raised', 'Venture Investment by Quarter', '#FFA500', quarters_filter, sectors_filter)
        st.plotly_chart(fig_inv, use_container_width=True)
    
    st.markdown("---")
    
    # Filter data for cards below
    ma_filtered = ma_df[ma_df['Quarter'].isin(quarters_filter) & ma_df['Sector'].isin(sectors_filter)]
    inv_filtered = inv_df[inv_df['Quarter'].isin(quarters_filter) & inv_df['Sector'].isin(sectors_filter)]
    
    # Split-screen summary cards
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
            st.metric("Total Value YTD", format_currency_short(ma_value))
        with kpi3:
            st.metric("Avg Deal Size", format_currency_short(ma_avg))
        
        # Top 3 M&A Deals
        st.markdown("#### 🏆 Top 3 M&A Deals")
        ma_sorted = ma_filtered.copy()
        ma_sorted['Deal_Value_Numeric'] = ma_sorted['Deal Value'].apply(parse_deal_value)
        top_ma = ma_sorted.nlargest(3, 'Deal_Value_Numeric')
        
        for idx, row in top_ma.iterrows():
            st.markdown(f"**{row['Acquirer']} acquired {row['Company']}**")
            st.markdown(f"<h3 style='color: #4A90E2;'>{format_currency_short(row['Deal_Value_Numeric'])}</h3>", unsafe_allow_html=True)
            st.markdown("---")
        
        # Top 3 Sectors by Deal Count
        st.markdown("#### 📊 Top 3 Sectors (Deal Count)")
        sector_counts = ma_filtered['Sector'].value_counts().head(3)
        for sector, count in sector_counts.items():
            st.write(f"• {sector}: {count} deals")
        
        # Sector chart
        st.markdown("#### Deal Value by Sector")
        sector_value = ma_filtered.groupby('Sector')['Deal Value'].apply(
            lambda x: x.apply(parse_deal_value).sum()
        ).sort_values(ascending=False)
        
        fig = go.Figure(data=[go.Bar(
            x=sector_value.values,
            y=sector_value.index,
            orientation='h',
            marker_color='#4A90E2',
            text=[format_currency_short(v) for v in sector_value.values],
            textposition='outside'
        )])
        fig.update_layout(
            height=300, 
            margin=dict(l=0, r=80, t=0, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
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
            st.metric("Total Value YTD", format_currency_short(inv_value))
        
        # Top 3 Venture Deals
        st.markdown("#### 🏆 Top 3 Venture Deals")
        inv_sorted = inv_filtered.copy()
        inv_sorted['Amount_Numeric'] = inv_sorted['Amount Raised'].apply(parse_deal_value)
        top_inv = inv_sorted.nlargest(3, 'Amount_Numeric')
        
        for idx, row in top_inv.iterrows():
            st.markdown(f"**{row['Company']}**")
            st.markdown(f"<h3 style='color: #FFA500;'>{format_currency_short(row['Amount_Numeric'])}</h3>", unsafe_allow_html=True)
            st.markdown("---")
        
        # Top 3 Sectors by Deal Count
        st.markdown("#### 📊 Top 3 Sectors (Deal Count)")
        sector_counts_inv = inv_filtered['Sector'].value_counts().head(3)
        for sector, count in sector_counts_inv.items():
            st.write(f"• {sector}: {count} deals")
        
        # Sector chart
        st.markdown("#### Deal Value by Sector")
        sector_value_inv = inv_filtered.groupby('Sector')['Amount Raised'].apply(
            lambda x: x.apply(parse_deal_value).sum()
        ).sort_values(ascending=False)
        
        fig = go.Figure(data=[go.Bar(
            x=sector_value_inv.values,
            y=sector_value_inv.index,
            orientation='h',
            marker_color='#FFA500',
            text=[format_currency_short(v) for v in sector_value_inv.values],
            textposition='outside'
        )])
        fig.update_layout(
            height=300, 
            margin=dict(l=0, r=80, t=0, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)

def show_deals_tables(ma_df, inv_df):
    """Deals tables with filters"""
    
    # Get all quarters and sectors
    all_quarters = sorted(set(list(ma_df['Quarter'].unique()) + list(inv_df['Quarter'].unique())))
    all_sectors = sorted(set(list(ma_df['Sector'].unique()) + list(inv_df['Sector'].unique())))
    
    # M&A Deals
    st.subheader("M&A Deals")
    
    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        quarters_ma = st.multiselect("Quarter", options=all_quarters, default=all_quarters, key="ma_quarters")
    with col_f2:
        sectors_ma = st.multiselect("Sector", options=all_sectors, default=all_sectors, key="ma_sectors")
    
    # Filter data
    ma_filtered = ma_df[ma_df['Quarter'].isin(quarters_ma) & ma_df['Sector'].isin(sectors_ma)]
    
    # Sort by deal value
    ma_display = ma_filtered.copy()
    ma_display['_Deal_Value_Numeric'] = ma_display['Deal Value'].apply(parse_deal_value)
    ma_display = ma_display.sort_values('_Deal_Value_Numeric', ascending=False)
    
    display_cols = [col for col in ma_display.columns if not col.startswith('_')]
    st.dataframe(ma_display[display_cols], use_container_width=True, height=400)
    
    st.markdown("---")
    
    # Venture Deals
    st.subheader("Venture Investment Deals")
    
    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        quarters_inv = st.multiselect("Quarter", options=all_quarters, default=all_quarters, key="inv_quarters")
    with col_f2:
        sectors_inv = st.multiselect("Sector", options=all_sectors, default=all_sectors, key="inv_sectors")
    
    # Filter data
    inv_filtered = inv_df[inv_df['Quarter'].isin(quarters_inv) & inv_df['Sector'].isin(sectors_inv)]
    
    # Sort by amount
    inv_display = inv_filtered.copy()
    inv_display['_Amount_Numeric'] = inv_display['Amount Raised'].apply(parse_deal_value)
    inv_display = inv_display.sort_values('_Amount_Numeric', ascending=False)
    
    # Format for display
    inv_display_formatted = inv_display.copy()
    inv_display_formatted['Amount Raised'] = inv_display_formatted['_Amount_Numeric'].apply(format_currency_short)
    
    display_cols = [col for col in inv_display_formatted.columns if not col.startswith('_')]
    st.dataframe(inv_display_formatted[display_cols], use_container_width=True, height=400)

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
        ma_values = [9200000000, 2100000000, 21700000000]  # Full amounts
        ma_counts = [57, 43, 65]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=quarters,
            y=ma_values,
            name='Deal Value',
            marker_color='#4A90E2',
            text=[format_currency(v) for v in ma_values],
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
            yaxis=dict(title='Deal Value (USD)', side='left', showgrid=False, range=[0, max(ma_values) * 1.3]),
            yaxis2=dict(title='Number of Deals', overlaying='y', side='right', showgrid=False, range=[0, max(ma_counts) * 1.4]),
            xaxis=dict(showgrid=False),
            height=400,
            showlegend=True,
            hovermode='x unified',
            margin=dict(t=50, b=50, l=80, r=80)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Venture Data from PDFs
    with col2:
        st.markdown("#### Venture Activity")
        
        vc_values = [3700000000, 2600000000, 2900000000]  # Full amounts
        vc_counts = [117, 90, 67]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=quarters,
            y=vc_values,
            name='Deal Value',
            marker_color='#FFA500',
            text=[format_currency(v) for v in vc_values],
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
            yaxis=dict(title='Deal Value (USD)', side='left', showgrid=False, range=[0, max(vc_values) * 1.3]),
            yaxis2=dict(title='Number of Deals', overlaying='y', side='right', showgrid=False, range=[0, max(vc_counts) * 1.4]),
            xaxis=dict(showgrid=False),
            height=400,
            showlegend=True,
            hovermode='x unified',
            margin=dict(t=50, b=50, l=80, r=80)
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

def show_ipo_tab(ipo_df):
    """IPO tab with filters"""
    st.header("IPO Activity")
    
    # Get quarters if available
    if 'Quarter' in ipo_df.columns:
        all_quarters = sorted(ipo_df['Quarter'].unique())
        quarters_filter = st.multiselect("Quarter", options=all_quarters, default=all_quarters, key="ipo_quarters")
        ipo_filtered = ipo_df[ipo_df['Quarter'].isin(quarters_filter)]
    else:
        ipo_filtered = ipo_df.copy()
    
    # KPI Cards
    ipo_count = len(ipo_filtered)
    ipo_value = ipo_filtered['Amount'].apply(parse_deal_value).sum()
    ipo_avg = ipo_value / ipo_count if ipo_count > 0 else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.metric("Total IPOs YTD", f"{ipo_count}")
    with kpi2:
        st.metric("Total Proceeds", format_currency_short(ipo_value))
    with kpi3:
        st.metric("Avg Proceeds", format_currency_short(ipo_avg))
    
    # Table
    st.markdown("### IPO Details")
    ipo_display = ipo_filtered.copy()
    ipo_display['_Amount_Numeric'] = ipo_display['Amount'].apply(parse_deal_value)
    ipo_display = ipo_display.sort_values('_Amount_Numeric', ascending=False)
    
    display_cols = [col for col in ipo_display.columns if not col.startswith('_')]
    st.dataframe(ipo_display[display_cols], use_container_width=True, height=400)

def show_upload_section():
    """Password-protected upload section as separate tab"""
    st.header("🔒 Upload New Dataset")
    
    st.info("Upload a new Excel file to update the dashboard data. You can either append new deals or replace the entire dataset.")
    
    password = st.text_input("Enter Password", type="password", key="upload_password")
    
    if password == "BeaconOne":
        st.success("✅ Access granted")
        
        uploaded_file = st.file_uploader("Upload MedTech_Deals.xlsx", type=['xlsx'], key="file_uploader")
        
        if uploaded_file:
            upload_mode = st.radio("Upload Mode", ["Append New Deals", "Replace Entire File"])
            
            if st.button("Upload and Update Dashboard"):
                try:
                    if upload_mode == "Replace Entire File":
                        # Save uploaded file
                        with open('MedTech_Deals.xlsx', 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        st.success("✅ File replaced successfully! Refreshing dashboard...")
                        st.cache_data.clear()
                        st.rerun()
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
                        
                        st.success("✅ Data appended successfully! Refreshing dashboard...")
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    elif password:
        st.error("❌ Incorrect password")
    else:
        st.warning("⚠️ Enter password to upload data")

if __name__ == "__main__":
    main()