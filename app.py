import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import local modules
from data_processor import process_ambulance_data, get_missing_trucking
from report_generator import generate_pdf, generate_excel_report

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Jharkhand 108 Monitoring System",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Shared CSS
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-title { font-size: 0.9rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #58a6ff; }
    .alert-box {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid #f85149;
        background: rgba(248, 81, 73, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- CACHED DATA LOADING ---
@st.cache_data(ttl=600)
def load_and_cache_data(file_path):
    try:
        import os
        if not os.path.exists(file_path):
            return None, []
        df = pd.read_csv(file_path, skiprows=1)
        return process_ambulance_data(df)
    except Exception as e:
        return None, []

# --- SIDEBAR & GLOBAL STATE ---
st.sidebar.title("108 Fleet Control")

# Tooltips added for clarity
status_file = st.sidebar.file_uploader(
    "Upload New Status Batch (CSV)", 
    type=['csv'], 
    key="status_uploader",
    help="Latest report of instrument status across ambulances. Columns must include 'VEHICLE DEITALS' and 'TYPE OF VEHICLE'."
)
master_file = st.sidebar.file_uploader(
    "Master Fleet List (Optional)", 
    type=['csv'], 
    key="master_uploader",
    help="A complete list of all 542 IDs in Jharkhand. Use this to find which ambulances haven't submitted their status yet."
)

# Persistent dataset
if status_file:
    raw_df = pd.read_csv(status_file, skiprows=1)
    df, inst_cols = process_ambulance_data(raw_df)
else:
    # Try to load a default fallback file if it exists, otherwise df remains None
    df, inst_cols = load_and_cache_data("latest_status.csv")

if df is None or df.empty:
    st.info("👋 Welcome! Please upload a **Status CSV** in the sidebar to begin monitoring.")
    st.stop()

# Master fleet matching
master_df = None
missing_ids = []
if master_file:
    master_df = pd.read_csv(master_file)
    missing_ids = get_missing_trucking(df, master_df)

# Logic Filters
st.sidebar.markdown("---")
dists = sorted(df['DISTRICT'].dropna().unique())
sel_dists = st.sidebar.multiselect("Filter by Districts", options=dists)

df_filtered = df.copy()
if sel_dists:
    df_filtered = df_filtered[df_filtered['DISTRICT'].isin(sel_dists)]

# High Risk Quick Filters
high_risk_list = df_filtered[df_filtered['Risk Level'] == 'High Risk']['VEHICLE DEITALS'].unique()
if len(high_risk_list) > 0:
    st.sidebar.warning(f"Found {len(high_risk_list)} High Risk units!")
    quick_select = st.sidebar.selectbox("Jump to High Risk Unit", options=["-- Select --"] + list(high_risk_list))
    if quick_select != "-- Select --":
        selected_mode = quick_select
    else:
        selected_mode = None
else:
    selected_mode = None

ambs = sorted(df_filtered['VEHICLE DEITALS'].dropna().unique())
if selected_mode:
    mode = st.sidebar.selectbox("Dashboard Mode", options=["Full Fleet Overview"] + list(ambs), index=list(ambs).index(selected_mode) + 1)
else:
    mode = st.sidebar.selectbox("Dashboard Mode", options=["Full Fleet Overview"] + list(ambs))

# --- UI LAYOUT ---

if mode != "Full Fleet Overview":
    # SINGLE AMBULANCE (DETAILED VIEW)
    amb_row = df_filtered[df_filtered['VEHICLE DEITALS'] == mode].iloc[0]
    st.title(f"Ambulance Analysis: {mode}")
    
    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><div class='metric-title'>Health Score</div><div class='metric-value'>{amb_row['Health %']}%</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-title'>Risk Status</div><div class='metric-value' style='color:#f85149;'>{amb_row['Risk Level']}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><div class='metric-title'>District</div><div class='metric-value'>{amb_row['DISTRICT']}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><div class='metric-title'>EMT ID</div><div class='metric-value' style='font-size:1.2rem;'>{amb_row.get('EMT NAME / ID', 'N/A')}</div></div>", unsafe_allow_html=True)
    
    l_col, r_col = st.columns([1.5, 1])
    with l_col:
        st.subheader("Equipment Status Log")
        st.table(pd.DataFrame([{"Instrument": i, "Current State": amb_row[i]} for i in inst_cols]))
    with r_col:
        st.subheader("Report Center")
        pdf_data = generate_pdf(amb_row, inst_cols)
        st.download_button(f"Download PDF Report", data=pdf_data, file_name=f"108_Report_{mode}.pdf", mime='application/pdf')
        
        # Gauge for visual polish
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = amb_row['Health %'],
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#58a6ff"},
                     'steps': [{'range': [0, 50], 'color': "#f85149"}, {'range': [50, 80], 'color': "#d29922"}]}))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig, use_container_width=True)

else:
    # FLEET DASHBOARD
    st.title("Jharkhand 108 Operation Dashboard")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"<div class='metric-card'><div class='metric-title'>Reported Fleet</div><div class='metric-value'>{len(df_filtered)}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><div class='metric-title'>Average Health</div><div class='metric-value'>{df_filtered['Health %'].mean():.1f}%</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='metric-card'><div class='metric-title'>Audit Required</div><div class='metric-value' style='color:#f1c40f;'>{len(df_filtered[df_filtered['Risk Level'] != 'Low Risk'])}</div></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='metric-card'><div class='metric-title'>Missing Units</div><div class='metric-value' style='color:#f85149;'>{len(missing_ids)}</div></div>", unsafe_allow_html=True)

    tab_p, tab_f, tab_m, tab_x = st.tabs(["Performance", "Failure Matrix", "Fleet Coverage Tracker", "Executive Reports"])
    
    with tab_p:
        st.subheader("Regional Health Performance")
        v_l, v_r = st.columns([1, 1.5])
        with v_l:
            # Audit Required vehicle listing
            audit_df = df_filtered[df_filtered['Risk Level'] != 'Low Risk'][['VEHICLE DEITALS', 'DISTRICT', 'Risk Level', 'Health %']].sort_values(by='Health %')
            st.markdown("#### Audit Required List (High/Medium Risk)")
            st.write("These vehicles need immediate attention. Copy the ID below to view details.")
            st.dataframe(audit_df, use_container_width=True, hide_index=True)
            
        with v_r:
            dist_perf = df_filtered.groupby('DISTRICT')['Health %'].mean().sort_values(ascending=False).reset_index()
            # Dynamic chart resizing or metric addition for small selections
            if len(dist_perf) <= 3:
                st.markdown("#### District Health Metrics")
                for _, row in dist_perf.iterrows():
                    st.write(f"**{row['DISTRICT']}**: {row['Health %']:.2f}% Health")
            
            fig_bar = px.bar(dist_perf, x='DISTRICT', y='Health %', color='Health %', color_continuous_scale='Blues')
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', bargap=0.4)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab_f:
        st.subheader("Equipment Failure Rankings")
        f_counts = [{"Instrument": i, "Fails": (df_filtered[i] == 'NOT WORKING').sum()} for i in inst_cols]
        f_df = pd.DataFrame(f_counts).sort_values(by="Fails", ascending=False).head(12)
        fig_fail = px.bar(f_df, x="Fails", y="Instrument", orientation='h', color="Fails", color_continuous_scale='Reds')
        fig_fail.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white', bargap=0.3)
        st.plotly_chart(fig_fail, use_container_width=True)

    with tab_m:
        st.subheader("Missing Fleet Report Tracking")
        st.info("Goal: Cross-reference reported statuses against your Master Fleet List (542 IDs).")
        if master_file:
            if missing_ids:
                st.error(f"ATTENTION: {len(missing_ids)} Ambulances are PENDING submission.")
                st.dataframe(pd.DataFrame(missing_ids, columns=["Vehicle ID - Missing Status"]), use_container_width=True)
            else:
                st.success("100% Reporting Compliance Achieved!")
        else:
            st.info("Please upload a Master Fleet List CSV in the sidebar to use tracking.")

    with tab_x:
        st.subheader("Executive Excel Generation")
        if st.button("Generate Executive Excel Report"):
            excel_bin = generate_excel_report(df_filtered, missing_ids)
            st.download_button("Download Professional 108 Report", data=excel_bin, file_name="Executive_Fleet_Report.xlsx", 
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
