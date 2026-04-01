import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Import local modules
from data_processor import (
    process_ambulance_data, get_missing_trucking, 
    process_master_fleet, get_fleet_analysis, extract_vehicle_id
)
from report_generator import generate_pdf, generate_excel_report

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Jharkhand 108 Monitoring System",
    page_icon="plus",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PROFESSIONAL COLOR PALETTE & THEMING ---
THEMES = {
    "dark": {
        'primary': '#00338D',      # KPMG Deep Blue
        'secondary': '#005EB8',    # Medium Blue
        'accent': '#0091DA',       # Bright Blue
        'light_blue': '#00A3E0',   # Light Blue
        'success': '#00A651',      # Green
        'warning': '#F5A623',      # Amber
        'danger': '#E74C3C',       # Red
        'info': '#48C9B0',         # Teal
        'dark': '#1A1A2E',         # Dark background ends
        'dark_grad': '#0F0F23',    # Dark background center
        'card_bg': '#16213E',      # Card background
        'card_border': '#0F3460',  # Card border
        'text': '#E8E8E8',         # Text
        'muted': '#8899AA',        # Muted text
        'grid': 'rgba(255,255,255,0.05)',
        'shadow': 'rgba(0,0,0,0.3)',
        'legend_bg': 'rgba(0,0,0,0.3)',
        'alert_bg': 'rgba(231,76,60,0.08)',
        'gauge_bg': 'rgba(0,0,0,0.2)',
        'gauge_danger': 'rgba(231,76,60,0.2)',
        'gauge_warning': 'rgba(245,166,35,0.2)',
        'gauge_success': 'rgba(0,166,81,0.2)',
        'empty_bg': 'rgba(0,145,218,0.1)',
        'empty_border': 'rgba(0,145,218,0.2)',
    },
    "light": {
        'primary': '#00338D',      
        'secondary': '#005EB8',    
        'accent': '#0091DA',       
        'light_blue': '#00A3E0',   
        'success': '#00A651',      
        'warning': '#DF7A00',      # Darker amber for visibility
        'danger': '#C0392B',       # Darker red
        'info': '#16A085',         
        'dark': '#F4F7F6',         # Light background ends
        'dark_grad': '#FFFFFF',    # Light background center
        'card_bg': '#FFFFFF',      # Card background
        'card_border': '#D1DCE5',  # Card border
        'text': '#111827',         # Dark text
        'muted': '#6B7A90',        # Muted text
        'grid': 'rgba(0,0,0,0.05)',
        'shadow': 'rgba(0,0,0,0.05)',
        'legend_bg': 'rgba(255,255,255,0.8)',
        'alert_bg': 'rgba(231,76,60,0.1)',
        'gauge_bg': 'rgba(0,0,0,0.05)',
        'gauge_danger': 'rgba(192,57,43,0.2)',
        'gauge_warning': 'rgba(223,122,0,0.2)',
        'gauge_success': 'rgba(0,166,81,0.2)',
        'empty_bg': 'rgba(0,145,218,0.05)',
        'empty_border': 'rgba(0,145,218,0.15)',
    }
}

# Sidebar matching for Theme (must be done before applying CSS)
theme_choice = st.sidebar.radio("Dashboard Theme", ["Dark", "Light"], index=0, horizontal=True)
COLORS = THEMES[theme_choice.lower()]

RISK_COLORS = {
    'High Risk': COLORS['danger'],
    'Medium Risk': COLORS['warning'],
    'Low Risk': COLORS['success'],
}

TYPE_COLORS = {
    'BLS': '#0091DA',
    'ALS': '#00338D',
    'NEO NATAL': '#E74C3C',
}

# Professional Chart Template
CHART_TEMPLATE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color=COLORS['text'], size=12),
    title_font=dict(size=16, color=COLORS['text']),
    legend=dict(
        bgcolor=COLORS['legend_bg'],
        bordercolor=COLORS['card_border'],
        borderwidth=1,
        font=dict(size=11)
    ),
    margin=dict(l=40, r=40, t=60, b=40),
    hoverlabel=dict(
        bgcolor=COLORS['card_bg'],
        font_size=12,
        font_color=COLORS['text']
    ),
)

# Shared CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {{
        --text-color: {COLORS['text']};
        --background-color: {COLORS['dark']};
        --secondary-background-color: {COLORS['card_bg']};
        --primary-color: {COLORS['accent']};
    }}

    .stApp {{
        background: linear-gradient(135deg, {COLORS['dark']} 0%, {COLORS['dark_grad']} 50%, {COLORS['dark']} 100%);
        color: {COLORS['text']};
        font-family: 'Inter', sans-serif;
    }}

    [data-testid="stSidebar"] {{
        background-color: {COLORS['card_bg']} !important;
    }}

    /* Force Streamlit native text elements to respect the theme text color */
    label, p, h1, h2, h3, h4, h5, h6, li, span, .stMarkdown p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-baseweb="tab"] p, [data-baseweb="radio"] div {{
        color: {COLORS['text']} !important;
    }}

    
    /* Professional KPI Cards */
    .kpi-card {{
        background: linear-gradient(145deg, {COLORS['card_bg']}cc, {COLORS['dark']}ee);
        border: 1px solid {COLORS['card_border']}80;
        border-radius: 16px;
        padding: 24px 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px {COLORS['shadow']}, inset 0 1px 0 {COLORS['grid']};
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 16px;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,51,141,0.2);
    }}
    .kpi-title {{
        font-size: 0.75rem;
        font-weight: 600;
        color: {COLORS['muted']};
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }}
    .kpi-value {{
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, {COLORS['accent']}, {COLORS['light_blue']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }}
    .kpi-value.danger {{ background: linear-gradient(135deg, #E74C3C, #FF6B6B); -webkit-background-clip: text; }}
    .kpi-value.warning {{ background: linear-gradient(135deg, #F5A623, #FFD93D); -webkit-background-clip: text; }}
    .kpi-value.success {{ background: linear-gradient(135deg, #00A651, #48C9B0); -webkit-background-clip: text; }}
    .kpi-subtitle {{
        font-size: 0.7rem;
        color: {COLORS['muted']};
        margin-top: 4px;
    }}
    
    /* Section Headers */
    .section-header {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {COLORS['text']};
        border-left: 4px solid {COLORS['accent']};
        padding-left: 12px;
        margin: 20px 0 16px 0;
    }}
    
    /* Status Badges */
    .status-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}
    .badge-danger {{ background: {COLORS['danger']}20; color: {COLORS['danger']}; border: 1px solid {COLORS['danger']}40; }}
    .badge-warning {{ background: {COLORS['warning']}20; color: {COLORS['warning']}; border: 1px solid {COLORS['warning']}40; }}
    .badge-success {{ background: {COLORS['success']}20; color: {COLORS['success']}; border: 1px solid {COLORS['success']}40; }}
    
    /* Alert Box */
    .alert-professional {{
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 12px;
        border-left: 4px solid {COLORS['danger']};
        background: {COLORS['alert_bg']};
        color: {COLORS['text']};
        font-size: 0.9rem;
    }}
    
    /* Dashboard Title */
    .dashboard-title {{
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, {COLORS['light_blue']}, {COLORS['accent']}, {COLORS['primary']});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }}
    .dashboard-subtitle {{
        font-size: 0.85rem;
        color: {COLORS['muted']};
        margin-bottom: 20px;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {COLORS['card_bg']}80;
        border-radius: 12px;
        padding: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    
    /* Dataframe styling */
    .stDataFrame {{ border-radius: 12px; overflow: hidden; }}
</style>
""", unsafe_allow_html=True)


# --- HELPER FUNCTIONS ---
def download_csv_button(df, filename, key):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name=filename,
        mime='text/csv',
        key=key,
        help="Download this table as a CSV file to copy or share.",
        use_container_width=True
    )

def kpi_card(title, value, subtitle="", style=""):
    return f"""<div class='kpi-card'>
        <div class='kpi-title'>{title}</div>
        <div class='kpi-value {style}'>{value}</div>
        <div class='kpi-subtitle'>{subtitle}</div>
    </div>"""

def apply_chart_style(fig, height=400):
    """Apply professional styling to any Plotly figure."""
    fig.update_layout(
        **CHART_TEMPLATE,
        height=height,
    )
    fig.update_xaxes(
        gridcolor=COLORS['grid'],
        linecolor=COLORS['card_border'],
        tickfont=dict(size=10),
    )
    fig.update_yaxes(
        gridcolor=COLORS['grid'],
        linecolor=COLORS['card_border'],
        tickfont=dict(size=10),
    )
    return fig


# --- CACHED DATA LOADING ---
@st.cache_data(ttl=600)
def load_and_cache_data(file_path):
    try:
        import os
        if not os.path.exists(file_path):
            return None, []
        df = pd.read_csv(file_path, skiprows=1)
        return process_ambulance_data(df)
    except Exception:
        return None, []


# --- SIDEBAR ---
st.sidebar.markdown(f"""
<div style='text-align:center; padding: 16px 0;'>
    <div style='font-size:2rem; font-weight:bold;'>108</div>
    <div style='font-size:1.1rem; font-weight:800; color:{COLORS["light_blue"]}; letter-spacing:1px;'>108 FLEET CONTROL</div>
    <div style='font-size:0.7rem; color:{COLORS["muted"]}; margin-top:4px;'>Jharkhand Ambulance Monitoring</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

status_file = st.sidebar.file_uploader(
    "Upload Status Report (CSV)", 
    type=['csv'], 
    key="status_uploader",
    help="Daily instrument status report from EMTs. Must contain 'VEHICLE DEITALS' and 'TYPE OF VEHICLE' columns."
)

master_file = st.sidebar.file_uploader(
    "Upload Master Fleet Data", 
    type=['csv', 'xlsx'], 
    key="master_uploader",
    help="Complete fleet list (542 vehicles). Use Check.xlsx MasterSheet or MasterData.csv for full analysis."
)

# Load Data
if status_file:
    raw_df = pd.read_csv(status_file, skiprows=1)
    df, inst_cols = process_ambulance_data(raw_df)
else:
    df, inst_cols = load_and_cache_data("latest_status.csv")

if df is None or df.empty:
    st.markdown("""
    <div style='text-align:center; padding:100px 40px;'>
        <div style='font-size:4rem; font-weight:bold;'>108</div>
        <div class='dashboard-title'>Jharkhand 108 Ambulance Monitoring</div>
        <div class='dashboard-subtitle'>Upload a Status CSV in the sidebar to begin fleet analysis</div>
        <div style='margin-top:30px; padding:20px; background:{COLORS["empty_bg"]}; border-radius:12px; border:1px solid {COLORS["empty_border"]}; display:inline-block;'>
            <div style='color:{COLORS["accent"]}; font-weight:600;'>Required File Format</div>
            <div style='color:{COLORS["muted"]}; font-size:0.85rem; margin-top:8px;'>CSV with columns: VEHICLE DEITALS, TYPE OF VEHICLE, DISTRICT, [Instrument Columns], EMT NAME / ID</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Load Master Data
master_df = None
fleet_analysis = None
missing_ids = []

if master_file:
    try:
        if master_file.name.endswith('.xlsx'):
            # Try reading the MasterSheet from Check.xlsx format
            try:
                master_df = pd.read_excel(master_file, sheet_name=1)  # MasterSheet
            except Exception:
                master_df = pd.read_excel(master_file, sheet_name=0)
        else:
            master_df = pd.read_csv(master_file)
            
    except Exception as e:
        st.sidebar.error(f"Error loading master data: {str(e)}")

# Filters
st.sidebar.markdown("---")
st.sidebar.markdown(f"<div style='font-weight:700; color:{COLORS['accent']}; margin-bottom:8px;'>FILTERS</div>", unsafe_allow_html=True)

dists = sorted(df['DISTRICT'].dropna().unique())
sel_dists = st.sidebar.multiselect("District", options=dists, key="dist_filter")

types = sorted(df['TYPE OF VEHICLE'].dropna().unique()) if 'TYPE OF VEHICLE' in df.columns else []
sel_types = st.sidebar.multiselect("Vehicle Type", options=types, key="type_filter")

df_filtered = df.copy()
master_filtered = None

if master_df is not None:
    # Process master once to standardise district and vehicle type columns before filtering
    master_filtered = process_master_fleet(master_df)

if sel_dists:
    df_filtered = df_filtered[df_filtered['DISTRICT'].isin(sel_dists)]
    if master_filtered is not None:
        master_filtered = master_filtered[master_filtered['DISTRICT'].isin(sel_dists)]

if sel_types:
    df_filtered = df_filtered[df_filtered['TYPE OF VEHICLE'].isin(sel_types)]
    if master_filtered is not None:
        master_filtered = master_filtered[master_filtered['VEHICLE_TYPE'].isin(sel_types)]

# Generate Fleet Analysis and Missing IDs *AFTER* filters are applied
if master_filtered is not None:
    fleet_analysis = get_fleet_analysis(master_filtered)
    missing_ids = get_missing_trucking(df_filtered, master_filtered)

# Quick Jump
st.sidebar.markdown("---")
high_risk_list = df_filtered[df_filtered['Risk Level'] == 'High Risk']['VEHICLE DEITALS'].unique()
if len(high_risk_list) > 0:
    st.sidebar.markdown(f"""
    <div class='alert-professional' style='border-left-color:{COLORS["danger"]}; padding:10px 14px;'>
        <strong>{len(high_risk_list)}</strong> High Risk ambulances found
    </div>
    """, unsafe_allow_html=True)

ambs = sorted(df_filtered['VEHICLE DEITALS'].dropna().unique())
mode = st.sidebar.selectbox("View Ambulance", options=["Full Fleet Dashboard"] + list(ambs))


# ==========================================================================
#  SINGLE AMBULANCE DETAILED VIEW
# ==========================================================================
if mode != "Full Fleet Dashboard":
    amb_row = df_filtered[df_filtered['VEHICLE DEITALS'] == mode].iloc[0]
    
    st.markdown(f"<div class='dashboard-title'> {mode}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='dashboard-subtitle'>{amb_row['DISTRICT']} | {amb_row.get('TYPE OF VEHICLE', 'N/A')} | EMT: {amb_row.get('EMT NAME / ID', 'N/A')}</div>", unsafe_allow_html=True)
    
    # KPIs
    risk_style = {'High Risk': 'danger', 'Medium Risk': 'warning', 'Low Risk': 'success'}[amb_row['Risk Level']]
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Health Score", f"{amb_row['Health %']}%", "Overall equipment health"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Risk Status", amb_row['Risk Level'], "Based on health threshold", risk_style), unsafe_allow_html=True)
    c3.markdown(kpi_card("Working", f"{int(amb_row['Working Count'])}/{int(amb_row['Total Applicable'])}", "Instruments operational"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Not Available", f"{int(amb_row.get('Not Available Count', 0))}", "Instruments not applicable"), unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1.5, 1])
    
    with col_l:
        st.markdown("<div class='section-header'>Equipment Status Matrix</div>", unsafe_allow_html=True)
        
        status_data = []
        for inst in inst_cols:
            val = str(amb_row[inst]).strip().upper()
            status_data.append({
                'Instrument': inst,
                'Status': val,
                'Indicator': 'OK' if val == 'WORKING' else ('FAIL' if val == 'NOT WORKING' else 'N/A')
            })
        status_df = pd.DataFrame(status_data)
        st.dataframe(
            status_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Instrument": st.column_config.TextColumn("Equipment", width="large"),
                "Status": st.column_config.TextColumn("Current Status"),
                "Indicator": st.column_config.TextColumn("", width="small"),
            }
        )
        download_csv_button(status_df, f"108_Equipment_Status_{mode}.csv", f"dl_amb_matrix_{mode}")
    
    with col_r:
        # Health Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=amb_row['Health %'],
            number={'suffix': '%', 'font': {'size': 40, 'color': COLORS['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': COLORS['muted']},
                'bar': {'color': COLORS['accent'], 'thickness': 0.3},
                'bgcolor': COLORS['gauge_bg'],
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 50], 'color': COLORS['gauge_danger']},
                    {'range': [50, 80], 'color': COLORS['gauge_warning']},
                    {'range': [80, 100], 'color': COLORS['gauge_success']},
                ],
                'threshold': {
                    'line': {'color': COLORS['danger'], 'width': 2},
                    'thickness': 0.8,
                    'value': 50
                }
            }
        ))
        apply_chart_style(fig_gauge, height=280)
        fig_gauge.update_layout(title="Health Gauge")
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Status breakdown pie
        working = int(amb_row['Working Count'])
        not_working = int(amb_row['Not Working Count'])
        not_avail = int(amb_row.get('Not Available Count', 0))
        
        fig_pie = go.Figure(go.Pie(
            labels=['Working', 'Not Working', 'Not Available'],
            values=[working, not_working, not_avail],
            hole=0.55,
            marker=dict(colors=[COLORS['success'], COLORS['danger'], COLORS['muted']]),
            textinfo='value+percent',
            textfont=dict(size=11),
        ))
        apply_chart_style(fig_pie, height=280)
        fig_pie.update_layout(title="Equipment Breakdown")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # PDF Report
        st.markdown("<div class='section-header'>Reports</div>", unsafe_allow_html=True)
        pdf_data = generate_pdf(amb_row, inst_cols)
        st.download_button(
            "Download PDF Report", 
            data=pdf_data, 
            file_name=f"108_Report_{mode}.pdf", 
            mime='application/pdf',
            use_container_width=True
        )

# ==========================================================================
#  FULL FLEET DASHBOARD
# ==========================================================================
else:
    # Title
    st.markdown("""
    <div class='dashboard-title'>Jharkhand 108 Operation Dashboard</div>
    <div class='dashboard-subtitle'>Real-time fleet monitoring & equipment health analytics | Instrument Status Analysis</div>
    """, unsafe_allow_html=True)
    
    # --- TOP KPI ROW ---
    total = len(df_filtered)
    avg_health = df_filtered['Health %'].mean()
    high_risk = len(df_filtered[df_filtered['Risk Level'] == 'High Risk'])
    medium_risk = len(df_filtered[df_filtered['Risk Level'] == 'Medium Risk'])
    low_risk = len(df_filtered[df_filtered['Risk Level'] == 'Low Risk'])
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.markdown(kpi_card("Reported Fleet", total, "Vehicles with status"), unsafe_allow_html=True)
    k2.markdown(kpi_card("Avg Health", f"{avg_health:.1f}%", "Fleet-wide average"), unsafe_allow_html=True)
    k3.markdown(kpi_card("High Risk", high_risk, "Health < 50%", "danger"), unsafe_allow_html=True)
    k4.markdown(kpi_card("Medium Risk", medium_risk, "Health 50-80%", "warning"), unsafe_allow_html=True)
    k5.markdown(kpi_card("Low Risk", low_risk, "Health > 80%", "success"), unsafe_allow_html=True)
    k6.markdown(kpi_card("Missing Units", len(missing_ids), "Not yet reported", "danger" if missing_ids else ""), unsafe_allow_html=True)
    
    # --- TABS ---
    tab_overview, tab_district, tab_types, tab_failures, tab_fleet, tab_reports = st.tabs([
        "Fleet Overview",
        "District Analysis", 
        "Vehicle Types (ALS/BLS/Neonatal)",
        "Equipment Failures",
        "Fleet Coverage & Missing",
        "Reports"
    ])
    
    # ============================
    #  TAB 1: FLEET OVERVIEW
    # ============================
    with tab_overview:
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.markdown("<div class='section-header'>Risk Distribution Overview</div>", unsafe_allow_html=True)
            
            risk_counts = df_filtered['Risk Level'].value_counts().reindex(['High Risk', 'Medium Risk', 'Low Risk']).fillna(0)
            
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Pie(
                labels=risk_counts.index,
                values=risk_counts.values,
                hole=0.6,
                marker=dict(
                    colors=[RISK_COLORS.get(r, '#888') for r in risk_counts.index],
                    line=dict(color=COLORS['dark'], width=3)
                ),
                textinfo='label+value+percent',
                textposition='outside',
                textfont=dict(size=12),
                pull=[0.05 if r == 'High Risk' else 0 for r in risk_counts.index],
            ))
            fig_risk.add_annotation(
                text=f"<b>{total}</b><br>Total",
                x=0.5, y=0.5, font_size=18, showarrow=False,
                font=dict(color=COLORS['text'])
            )
            apply_chart_style(fig_risk, height=380)
            fig_risk.update_layout(title="Fleet Risk Classification", showlegend=False)
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            st.markdown("<div class='section-header'>Health Score Distribution</div>", unsafe_allow_html=True)
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=df_filtered['Health %'],
                nbinsx=20,
                marker=dict(
                    color=COLORS['accent'],
                    line=dict(color=COLORS['primary'], width=1),
                ),
                opacity=0.85,
                hovertemplate='Health: %{x}%<br>Count: %{y}<extra></extra>'
            ))
            # Add median line
            median_health = df_filtered['Health %'].median()
            fig_hist.add_vline(x=median_health, line_dash="dash", line_color=COLORS['warning'],
                             annotation_text=f"Median: {median_health:.0f}%", 
                             annotation_position="top right",
                             annotation_font=dict(color=COLORS['warning']))
            apply_chart_style(fig_hist, height=380)
            fig_hist.update_layout(
                title="Health Score Distribution",
                xaxis_title="Health %",
                yaxis_title="Number of Vehicles",
                bargap=0.05,
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Audit Required Table
        st.markdown("<div class='section-header'>Vehicles Requiring Immediate Audit</div>", unsafe_allow_html=True)
        
        audit_df = df_filtered[df_filtered['Risk Level'] != 'Low Risk'][
            ['VEHICLE DEITALS', 'DISTRICT', 'TYPE OF VEHICLE', 'Risk Level', 'Health %', 'Working Count', 'Not Working Count']
        ].sort_values(by='Health %')
        
        if len(audit_df) > 0:
            st.dataframe(
                audit_df.head(30),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Health %": st.column_config.ProgressColumn(
                        "Health %", min_value=0, max_value=100, format="%d%%"
                    ),
                }
            )
            download_csv_button(audit_df, "Audit_Vehicles.csv", "dl_audit")
        else:
            st.success("All vehicles are in Low Risk category!")
    
    # ============================
    #  TAB 2: DISTRICT ANALYSIS
    # ============================
    with tab_district:
        st.markdown("<div class='section-header'>District-Wise Vehicle Comparison</div>", unsafe_allow_html=True)
        
        # District summary
        # Let's compute 'Working Vehicles' (vehicles with Health % >= 80, e.g. Low Risk)
        # OR functional vehicles defined as anything not 'High Risk'
        dist_summary = df_filtered.groupby('DISTRICT').agg(
            Total_Vehicles=('VEHICLE DEITALS', 'count'),
            Functional_Vehicles=('Risk Level', lambda x: (x == 'Low Risk').sum()),
            Avg_Health=('Health %', 'mean'),
            High_Risk=('Risk Level', lambda x: (x == 'High Risk').sum()),
            Medium_Risk=('Risk Level', lambda x: (x == 'Medium Risk').sum()),
            Low_Risk=('Risk Level', lambda x: (x == 'Low Risk').sum()),
            Working_Avg=('Working Count', 'mean'),
        ).sort_values('Total_Vehicles', ascending=False).reset_index()
        
        # Chart 0: Total Vehicles vs Working/Functional Vehicles
        st.markdown("<div class='section-header'>Total vs Working Vehicles by District</div>", unsafe_allow_html=True)
        fig_total_working = go.Figure()
        fig_total_working.add_trace(go.Bar(
            name='Total Reported Vehicles',
            x=dist_summary['DISTRICT'],
            y=dist_summary['Total_Vehicles'],
            marker_color=COLORS['primary'],
            text=dist_summary['Total_Vehicles'],
            textposition='outside',
            textfont=dict(size=10, color=COLORS['text']),
        ))
        fig_total_working.add_trace(go.Bar(
            name='Fully Functional Vehicles',
            x=dist_summary['DISTRICT'],
            y=dist_summary['Functional_Vehicles'],
            marker_color=COLORS['success'],
            text=dist_summary['Functional_Vehicles'],
            textposition='outside',
            textfont=dict(size=10, color=COLORS['text']),
        ))
        apply_chart_style(fig_total_working, height=450)
        fig_total_working.update_layout(
            barmode='group',
            xaxis_tickangle=-45,
            title="District-Wise Total vs Functional (Low Risk) Vehicles",
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        )
        st.plotly_chart(fig_total_working, use_container_width=True)

        
        # Chart 1: District-wise vehicle count comparison
        st.markdown("<div class='section-header'>District Average Health Comparison</div>", unsafe_allow_html=True)
        fig_dist_count = go.Figure()
        fig_dist_count.add_trace(go.Bar(
            x=dist_summary['DISTRICT'],
            y=dist_summary['Total_Vehicles'],
            marker=dict(
                color=dist_summary['Avg_Health'],
                colorscale=[[0, COLORS['danger']], [0.5, COLORS['warning']], [1, COLORS['success']]],
                colorbar=dict(title="Avg Health %", tickfont=dict(color=COLORS['text'])),
                line=dict(width=0),
            ),
            text=dist_summary['Total_Vehicles'],
            textposition='outside',
            textfont=dict(size=11, color=COLORS['text']),
            hovertemplate='<b>%{x}</b><br>Vehicles: %{y}<br>Avg Health: %{marker.color:.1f}%<extra></extra>',
        ))
        apply_chart_style(fig_dist_count, height=450)
        fig_dist_count.update_layout(
            title="District-Wise Total Vehicles Reported (Color = Health %)",
            xaxis_title="District",
            yaxis_title="Number of Vehicles",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig_dist_count, use_container_width=True)
        
        # Chart 2: District Risk Breakdown (Stacked)
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("<div class='section-header'>Risk Breakdown by District</div>", unsafe_allow_html=True)
            
            fig_stacked = go.Figure()
            for risk, color in [('Low Risk', COLORS['success']), ('Medium Risk', COLORS['warning']), ('High Risk', COLORS['danger'])]:
                fig_stacked.add_trace(go.Bar(
                    name=risk,
                    x=dist_summary['DISTRICT'],
                    y=dist_summary[risk.replace(' ', '_')],
                    marker_color=color,
                    text=dist_summary[risk.replace(' ', '_')],
                    textposition='auto',
                    textfont=dict(size=9),
                ))
            apply_chart_style(fig_stacked, height=400)
            fig_stacked.update_layout(
                barmode='stack',
                xaxis_tickangle=-45,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            )
            st.plotly_chart(fig_stacked, use_container_width=True)
        
        with col_b:
            st.markdown("<div class='section-header'>District Health Ranking</div>", unsafe_allow_html=True)
            
            dist_health = dist_summary.sort_values('Avg_Health', ascending=True)
            
            fig_health_bar = go.Figure()
            fig_health_bar.add_trace(go.Bar(
                y=dist_health['DISTRICT'],
                x=dist_health['Avg_Health'],
                orientation='h',
                marker=dict(
                    color=dist_health['Avg_Health'],
                    colorscale=[[0, COLORS['danger']], [0.5, COLORS['warning']], [1, COLORS['success']]],
                ),
                text=dist_health['Avg_Health'].round(1).astype(str) + '%',
                textposition='outside',
                textfont=dict(size=10, color=COLORS['text']),
                hovertemplate='<b>%{y}</b><br>Health: %{x:.1f}%<extra></extra>',
            ))
            apply_chart_style(fig_health_bar, height=400)
            fig_health_bar.update_layout(
                xaxis_title="Average Health %",
                xaxis_range=[0, 105],
            )
            st.plotly_chart(fig_health_bar, use_container_width=True)
        
        # If MasterData available — show Total Fleet vs Reported comparison
        if fleet_analysis:
            st.markdown("<div class='section-header'>Total Fleet vs Reported (MasterData Comparison)</div>", unsafe_allow_html=True)
            
            master_dist = fleet_analysis['processed_df'].groupby('DISTRICT').size().reset_index(name='Total_Fleet')
            reported_dist = df_filtered.groupby('DISTRICT').size().reset_index(name='Reported')
            
            compare_df = master_dist.merge(reported_dist, on='DISTRICT', how='outer').fillna(0)
            compare_df['Missing'] = compare_df['Total_Fleet'] - compare_df['Reported']
            compare_df = compare_df.sort_values('Total_Fleet', ascending=False)
            
            fig_compare = go.Figure()
            fig_compare.add_trace(go.Bar(
                name='Total Fleet (Master)',
                x=compare_df['DISTRICT'],
                y=compare_df['Total_Fleet'],
                marker_color=COLORS['primary'],
                text=compare_df['Total_Fleet'].astype(int),
                textposition='outside',
                textfont=dict(size=9),
            ))
            fig_compare.add_trace(go.Bar(
                name='Reported',
                x=compare_df['DISTRICT'],
                y=compare_df['Reported'],
                marker_color=COLORS['accent'],
                text=compare_df['Reported'].astype(int),
                textposition='outside',
                textfont=dict(size=9),
            ))
            fig_compare.add_trace(go.Bar(
                name='Missing / Not Reported',
                x=compare_df['DISTRICT'],
                y=compare_df['Missing'],
                marker_color=COLORS['danger'],
                text=compare_df['Missing'].astype(int),
                textposition='outside',
                textfont=dict(size=9),
            ))
            apply_chart_style(fig_compare, height=450)
            fig_compare.update_layout(
                barmode='group',
                xaxis_tickangle=-45,
                title="District Wise: Total Fleet vs Reported vs Missing",
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            )
            st.plotly_chart(fig_compare, use_container_width=True)
    
    # ============================
    #  TAB 3: VEHICLE TYPES
    # ============================
    with tab_types:
        st.markdown("<div class='section-header'>Vehicle Type Analysis - ALS / BLS / Neonatal</div>", unsafe_allow_html=True)
        
        if 'TYPE OF VEHICLE' in df_filtered.columns:
            type_summary = df_filtered.groupby('TYPE OF VEHICLE').agg(
                Count=('VEHICLE DEITALS', 'count'),
                Avg_Health=('Health %', 'mean'),
                Min_Health=('Health %', 'min'),
                Max_Health=('Health %', 'max'),
            ).reset_index()
            
            # KPI cards for each type
            type_cols = st.columns(len(type_summary))
            for idx, (_, row) in enumerate(type_summary.iterrows()):
                vtype = row['TYPE OF VEHICLE']
                type_cols[idx].markdown(kpi_card(
                    vtype,
                    f"{int(row['Count'])}",
                    f"Avg Health: {row['Avg_Health']:.1f}%"
                ), unsafe_allow_html=True)
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                # Donut chart of fleet composition
                fig_type_pie = go.Figure(go.Pie(
                    labels=type_summary['TYPE OF VEHICLE'],
                    values=type_summary['Count'],
                    hole=0.55,
                    marker=dict(
                        colors=[TYPE_COLORS.get(t, '#888') for t in type_summary['TYPE OF VEHICLE']],
                        line=dict(color=COLORS['dark'], width=3),
                    ),
                    textinfo='label+value+percent',
                    textfont=dict(size=12),
                ))
                fig_type_pie.add_annotation(
                    text="Fleet<br>Mix",
                    x=0.5, y=0.5, font_size=15, showarrow=False,
                    font=dict(color=COLORS['text'])
                )
                apply_chart_style(fig_type_pie, height=380)
                fig_type_pie.update_layout(title="Fleet Composition", showlegend=False)
                st.plotly_chart(fig_type_pie, use_container_width=True)
            
            with col_t2:
                # Health by type box plot
                fig_box = go.Figure()
                for vtype in type_summary['TYPE OF VEHICLE']:
                    type_data = df_filtered[df_filtered['TYPE OF VEHICLE'] == vtype]['Health %']
                    fig_box.add_trace(go.Box(
                        y=type_data,
                        name=vtype,
                        marker_color=TYPE_COLORS.get(vtype, '#888'),
                        boxmean='sd',
                    ))
                apply_chart_style(fig_box, height=380)
                fig_box.update_layout(title="Health Distribution by Vehicle Type", yaxis_title="Health %")
                st.plotly_chart(fig_box, use_container_width=True)
            
            # District-wise type breakdown (stacked bar)
            st.markdown("<div class='section-header'>District-Wise Vehicle Type Distribution</div>", unsafe_allow_html=True)
            
            type_dist = df_filtered.groupby(['DISTRICT', 'TYPE OF VEHICLE']).size().unstack(fill_value=0).reset_index()
            
            fig_type_dist = go.Figure()
            for vtype in [c for c in type_dist.columns if c != 'DISTRICT']:
                fig_type_dist.add_trace(go.Bar(
                    name=vtype,
                    x=type_dist['DISTRICT'],
                    y=type_dist[vtype],
                    marker_color=TYPE_COLORS.get(vtype, '#888'),
                    text=type_dist[vtype],
                    textposition='auto',
                    textfont=dict(size=9),
                ))
            apply_chart_style(fig_type_dist, height=450)
            fig_type_dist.update_layout(
                barmode='stack',
                title="District-Wise: ALS / BLS / Neonatal Breakdown",
                xaxis_tickangle=-45,
                xaxis_title="District",
                yaxis_title="Number of Vehicles",
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            )
            st.plotly_chart(fig_type_dist, use_container_width=True)
            
            # Expected Instruments per Vehicle Type Chart
            st.markdown("<div class='section-header'>Required Instruments per Vehicle Type</div>", unsafe_allow_html=True)
            req_inst = df_filtered.groupby('TYPE OF VEHICLE')['Total Applicable'].max().reset_index()
            req_inst.columns = ['TYPE OF VEHICLE', 'Required Instruments']
            
            fig_req = go.Figure()
            fig_req.add_trace(go.Bar(
                x=req_inst['TYPE OF VEHICLE'],
                y=req_inst['Required Instruments'],
                marker_color=[TYPE_COLORS.get(t, '#888') for t in req_inst['TYPE OF VEHICLE']],
                text=req_inst['Required Instruments'].astype(int),
                textposition='outside',
                textfont=dict(size=14, color=COLORS['text'])
            ))
            apply_chart_style(fig_req, height=350)
            fig_req.update_layout(
                title="Number of Standard Instruments Required",
                xaxis_title="Vehicle Type",
                yaxis_title="Total Instrument Count"
            )
            st.plotly_chart(fig_req, use_container_width=True)
            
            # --- STANDARD INSTRUMENT CONFIGURATION CHECKLIST ---
            st.markdown("<div class='section-header'>Standard Minimum Requirements (100% Configuration)</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:{COLORS['muted']}; font-size:0.9rem; margin-bottom:15px;'>Because a 100% score for ALS is different from BLS, here is the standard expected inventory for each vehicle type:</div>", unsafe_allow_html=True)
            
            # Categorizing Instruments based on typical 108 Ambulance norms
            bls_core = ['Auto Loader - Collapsible stretcher', 'Scoop Stretcher', 'Spine Board with Straps', 'D Type Oxygen Cylinder', 'B Type Oxygen Cylinder', 'Portable Oxygen Cylinder', 'Flowmeter', 'Humidifier Bottel', 'Aneroid B.P Appratus with Pediatric Cuff-Size', 'Pneumatic Splints', 'Guaze Cutter', 'Thermometer (Digital)', 'Wheel Chair', 'Needle cum Syringe Destroyer']
            als_core = bls_core + ['Nebulizer Machine', 'Suction Machine (Electric)', 'Suction Machine (Hand Held)', 'Pulse Oximeter', 'Glucometer', 'Margils Forcep', 'Artificial Manual Breathing unit (Adult, Child+Neonatal)']
            neo_core = bls_core + ['Stethoscope (Pediatric+Neonatal)', 'Cervical Collar- Paediatric', 'Double Head Immobilizer (Pediatric+Neonatal)', 'Artificial Manual Breathing unit (Adult, Child+Neonatal)', 'Nebulizer Machine', 'Suction Machine (Electric)', 'Suction Machine (Hand Held)', 'Pulse Oximeter']
            
            req_data = pd.DataFrame({
                "Equipment / Instrument Name": inst_cols,
                "BLS": ["✅" if i in bls_core else "❌" for i in inst_cols],
                "ALS": ["✅" if i in als_core else "❌" for i in inst_cols],
                "NEO NATAL": ["✅" if i in neo_core else "❌" for i in inst_cols],
            })
            
            st.dataframe(req_data, use_container_width=True, hide_index=True)
            download_csv_button(req_data, "Ambulance_Expected_Configuration.csv", "dl_config_matrix")
    
    # ============================
    #  TAB 4: EQUIPMENT FAILURES
    # ============================
    with tab_failures:
        st.markdown("<div class='section-header'>Equipment Failure Analysis</div>", unsafe_allow_html=True)
        
        # Top failures
        f_counts = []
        for i in inst_cols:
            not_working = (df_filtered[i] == 'NOT WORKING').sum()
            working = (df_filtered[i] == 'WORKING').sum()
            total_applicable = not_working + working
            fail_rate = (not_working / total_applicable * 100) if total_applicable > 0 else 0
            f_counts.append({
                "Instrument": i,
                "Not Working": not_working,
                "Working": working,
                "Failure Rate %": round(fail_rate, 1),
            })
        
        f_df = pd.DataFrame(f_counts).sort_values(by="Not Working", ascending=False)
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            # Top 15 failure bar chart
            top_fails = f_df.head(15)
            fig_fail = go.Figure()
            fig_fail.add_trace(go.Bar(
                y=top_fails['Instrument'],
                x=top_fails['Not Working'],
                orientation='h',
                marker=dict(
                    color=top_fails['Failure Rate %'],
                    colorscale=[[0, COLORS['warning']], [1, COLORS['danger']]],
                    colorbar=dict(title="Fail %"),
                ),
                text=top_fails.apply(lambda r: f"{int(r['Not Working'])} ({r['Failure Rate %']}%)", axis=1),
                textposition='outside',
                textfont=dict(size=10, color=COLORS['text']),
                hovertemplate='<b>%{y}</b><br>Not Working: %{x}<extra></extra>',
            ))
            apply_chart_style(fig_fail, height=500)
            fig_fail.update_layout(
                title="Top 15 Equipment Failures",
                xaxis_title="Number of Failures",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_fail, use_container_width=True)
        
        with col_f2:
            # Working vs Not Working comparison for top items
            top10 = f_df.head(10)
            fig_compare_eq = go.Figure()
            fig_compare_eq.add_trace(go.Bar(
                name='Working',
                y=top10['Instrument'],
                x=top10['Working'],
                orientation='h',
                marker_color=COLORS['success'],
            ))
            fig_compare_eq.add_trace(go.Bar(
                name='Not Working',
                y=top10['Instrument'],
                x=top10['Not Working'],
                orientation='h',
                marker_color=COLORS['danger'],
            ))
            apply_chart_style(fig_compare_eq, height=500)
            fig_compare_eq.update_layout(
                barmode='group',
                title="Working vs Not Working (Top 10)",
                xaxis_title="Count",
                yaxis=dict(autorange="reversed"),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            )
            st.plotly_chart(fig_compare_eq, use_container_width=True)
        
        # Full failure table
        st.markdown("<div class='section-header'>Complete Equipment Status Matrix</div>", unsafe_allow_html=True)
        st.dataframe(
            f_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Failure Rate %": st.column_config.ProgressColumn(
                    "Failure Rate %", min_value=0, max_value=100, format="%d%%"
                ),
            }
        )
        download_csv_button(f_df, "Equipment_Failures.csv", "dl_failures")
    
    # ============================
    #  TAB 5: FLEET COVERAGE
    # ============================
    with tab_fleet:
        st.markdown("<div class='section-header'>Fleet Coverage & Tracking</div>", unsafe_allow_html=True)
        
        if fleet_analysis:
            # Fleet Status KPIs
            fs = fleet_analysis['by_status']
            fc1, fc2, fc3, fc4 = st.columns(4)
            fc1.markdown(kpi_card("Total Fleet", fleet_analysis['total_fleet'], "All registered ambulances"), unsafe_allow_html=True)
            fc2.markdown(kpi_card("On-Road (HOTO)", fs.get('On-Road (HOTO Done)', 0), "Active & operational", "success"), unsafe_allow_html=True)
            fc3.markdown(kpi_card("Under CS Repair", fs.get('Under CS Repair', 0), "In repair workshop", "warning"), unsafe_allow_html=True)
            fc4.markdown(kpi_card("Pending from EMRI", fs.get('Pending from EMRI', 0), "Awaiting EMRI handover", "danger"), unsafe_allow_html=True)
            
            # Fleet Status Pie
            col_fs1, col_fs2 = st.columns(2)
            
            with col_fs1:
                status_labels = list(fs.keys())
                status_vals = list(fs.values())
                status_colors = {
                    'On-Road (HOTO Done)': COLORS['success'],
                    'Under CS Repair': COLORS['warning'],
                    'Pending from EMRI': COLORS['danger'],
                    'HOTO Pending': '#8B5CF6',
                    'Unknown': COLORS['muted'],
                }
                
                fig_fleet_pie = go.Figure(go.Pie(
                    labels=status_labels,
                    values=status_vals,
                    hole=0.55,
                    marker=dict(
                        colors=[status_colors.get(s, '#888') for s in status_labels],
                        line=dict(color=COLORS['dark'], width=2),
                    ),
                    textinfo='label+value+percent',
                    textfont=dict(size=11),  
                ))
                apply_chart_style(fig_fleet_pie, height=380)
                fig_fleet_pie.update_layout(title="Fleet Status Distribution", showlegend=False)
                st.plotly_chart(fig_fleet_pie, use_container_width=True)
            
            with col_fs2:
                # Under CS Repair vehicles
                repair_df = fleet_analysis['under_repair']
                if len(repair_df) > 0:
                    st.markdown("<div class='section-header'>Under CS Repair</div>", unsafe_allow_html=True)
                    display_cols = ['VEHICLE_ID', 'DISTRICT']
                    if 'BASE LOCATION' in repair_df.columns:
                        display_cols.append('BASE LOCATION')
                    if 'VEHICLE_TYPE' in repair_df.columns:
                        display_cols.append('VEHICLE_TYPE')
                    st.dataframe(repair_df[display_cols], use_container_width=True, hide_index=True)
                    download_csv_button(repair_df[display_cols], "Under_CS_Repair.csv", "dl_repair")
                
                # HOTO Pending
                hoto_df = fleet_analysis['hoto_pending']
                if len(hoto_df) > 0:
                    st.markdown("<div class='section-header'>HOTO Pending</div>", unsafe_allow_html=True)
                    display_cols2 = ['VEHICLE_ID', 'DISTRICT']
                    if 'BASE LOCATION' in hoto_df.columns:
                        display_cols2.append('BASE LOCATION')
                    st.dataframe(hoto_df[display_cols2], use_container_width=True, hide_index=True)
                    download_csv_button(hoto_df[display_cols2], "HOTO_Pending.csv", "dl_hoto")
            
            # Missing vehicles
            if missing_ids:
                st.markdown(f"<div class='section-header'>Missing Status Reports ({len(missing_ids)} vehicles)</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class='alert-professional'>
                    <strong>{len(missing_ids)}</strong> ambulances from the master fleet have NOT submitted their instrument status report.
                </div>
                """, unsafe_allow_html=True)
                
                missing_display = pd.DataFrame(missing_ids, columns=["Vehicle ID"])
                # Try to enrich with master data
                if fleet_analysis:
                    master_proc = fleet_analysis['processed_df']
                    missing_enriched = master_proc[master_proc['VEHICLE_ID'].str.upper().isin([m.upper() for m in missing_ids])]
                    if len(missing_enriched) > 0:
                        display_cols3 = ['VEHICLE_ID', 'DISTRICT', 'Fleet Status']
                        if 'VEHICLE_TYPE' in missing_enriched.columns:
                            display_cols3.append('VEHICLE_TYPE')
                        if 'BASE LOCATION' in missing_enriched.columns:
                            display_cols3.append('BASE LOCATION')
                        st.dataframe(missing_enriched[display_cols3], use_container_width=True, hide_index=True)
                        download_csv_button(missing_enriched[display_cols3], "Missing_Reports_Enriched.csv", "dl_miss_e")
                    else:
                        st.dataframe(missing_display, use_container_width=True, hide_index=True)
                        download_csv_button(missing_display, "Missing_Reports.csv", "dl_miss_b1")
                else:
                    st.dataframe(missing_display, use_container_width=True, hide_index=True)
                    download_csv_button(missing_display, "Missing_Reports.csv", "dl_miss_b2")
            else:
                st.success("100% Reporting Compliance - All fleet vehicles have submitted status!")
        else:
            st.info("Upload Master Fleet Data (CSV/XLSX) in the sidebar to enable fleet tracking, missing vehicle detection, and repair status analysis.")
    
    # ============================
    #  TAB 6: REPORTS
    # ============================
    with tab_reports:
        st.markdown("<div class='section-header'>Executive Report Generation</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='kpi-card'>
            <div style='font-size:2rem; margin-bottom:8px;'>Report Download</div>
            <div style='font-weight:700; color:{COLORS["accent"]}; margin-bottom:4px;'>Executive Excel Report</div>
            <div style='color:{COLORS["muted"]}; font-size:0.8rem;'>Multi-sheet report with charts, summaries, fleet overview, district analysis, vehicle type breakdown, failure reports, and missing vehicle tracking.</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Decide dynamic filename based on filters
        if len(sel_dists) == 1:
            report_name = f"Jharkhand_108_{sel_dists[0]}_Report.xlsx"
        elif len(sel_dists) > 1:
            report_name = "Jharkhand_108_MultiDistrict_Report.xlsx"
        else:
            report_name = "Jharkhand_108_State_Report.xlsx"
        
        # Pass everything to report generator to generate the exhaustive report
        if st.button("Generate Excel Report", use_container_width=True):
            excel_bin = generate_excel_report(
                df_filtered=df_filtered, 
                missing_ids=missing_ids, 
                fleet_analysis=fleet_analysis,
                dist_summary=dist_summary,
                type_summary=type_summary if 'TYPE OF VEHICLE' in df_filtered.columns else None,
                equipment_failures=f_df,
                inst_cols=inst_cols,
                master=master_df
            )
            st.download_button(
                "Download Executive Report",
                data=excel_bin,
                file_name=report_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
