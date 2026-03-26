import pandas as pd

def standardize_columns(df):
    """Clean and standardize column names and values."""
    df.columns = df.columns.str.replace('  ', ' ').str.strip()
    return df

def get_instrument_cols(df):
    """Identify instrument status columns based on known markers."""
    try:
        start_idx = df.columns.get_loc('TYPE OF VEHICLE') + 1
        end_idx = df.columns.get_loc('EMT NAME / ID')
        return df.columns[start_idx:end_idx].tolist()
    except:
        return [c for c in df.columns if 'STRETCHER' in c.upper() or 'OXYGEN' in c.upper() or 'MACHINE' in c.upper()]

def process_ambulance_data(df):
    """Main data processing pipeline for ambulance status."""
    df = standardize_columns(df)
    instrument_cols = get_instrument_cols(df)
    
    # Clean status values
    for col in instrument_cols:
        df[col] = df[col].astype(str).str.strip().str.upper()
        
    # Area mapping
    urban_list = ['RANCHI', 'DHANBAD', 'BOKARO', 'EAST SINGHBHUM']
    df['Area Level'] = df['DISTRICT'].apply(lambda x: 'Urban' if str(x).upper() in urban_list else 'Rural')
    
    # Health Metrics
    df['Working Count'] = (df[instrument_cols] == 'WORKING').sum(axis=1)
    df['Not Working Count'] = (df[instrument_cols] == 'NOT WORKING').sum(axis=1)
    df['Total Applicable'] = df['Working Count'] + df['Not Working Count']
    df['Health %'] = (df['Working Count'] / df['Total Applicable'] * 100).fillna(0).round(2)
    
    # Risk Classification (High < 50, Medium 50-80, Low > 80)
    # Hint: Limits can be changed here
    def classify_risk(h):
        if h < 50: return "High Risk"
        elif h <= 80: return "Medium Risk"
        return "Low Risk"
    
    df['Risk Level'] = df['Health %'].apply(classify_risk)
    
    return df, instrument_cols

def get_missing_trucking(fleet_df, master_list_df):
    """Identifies missing fleet submissions."""
    if master_list_df is None or master_list_df.empty:
        return []
    
    master_list_df.columns = master_list_df.columns.str.strip().str.upper()
    id_col = master_list_df.columns[0]
    
    master_ids = set(master_list_df[id_col].astype(str).str.strip())
    reported_ids = set(fleet_df['VEHICLE DEITALS'].astype(str).str.strip())
    
    return list(master_ids - reported_ids)
