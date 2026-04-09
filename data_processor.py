import pandas as pd
import re

# --- District Name Normalization Map ---
DISTRICT_NORMALIZE = {
    'WESTSINGHBHUM': 'WEST SINGHBHUM',
    'WEST SINGHBHUM': 'WEST SINGHBHUM',
    'EAST SINGHBHUM': 'EAST SINGHBHUM',
    'EAST SINGHBHUM': 'EAST SINGHBHUM',
    'RAMGHAR': 'RAMGARH',
    'RAMGARH': 'RAMGARH',
    'HAZARIBAGH': 'HAZARIBAGH',
    'RANCHI': 'RANCHI',
    'SARAIKELA': 'SARAIKELA',
    'SAHIBGANJ': 'SAHIBGANJ',
}

VEHICLE_TYPE_NORMALIZE = {
    'BLS': 'BLS',
    'ALS': 'ALS',
    'NEO NATAL': 'NEO NATAL',
    'NEO NATAL AMBULANCE': 'NEO NATAL',
    'NEONATAL': 'NEO NATAL',
    'NEONATAL AMBULANCE': 'NEO NATAL',
}

def normalize_district(name):
    """Normalize district names to handle inconsistencies."""
    if pd.isna(name):
        return name
    cleaned = str(name).strip().upper()
    return DISTRICT_NORMALIZE.get(cleaned, cleaned)

def normalize_vehicle_type(vtype):
    """Normalize vehicle type values."""
    if pd.isna(vtype):
        return vtype
    cleaned = str(vtype).strip().upper()
    return VEHICLE_TYPE_NORMALIZE.get(cleaned, cleaned)

def extract_vehicle_id(vehicle_detail):
    """Extract clean vehicle registration number from VEHICLE DEITALS field.
    
    Status CSV has: 'JH01FL6498  NEO NATAL AMBULANCE' or 'JH01CH1018 BLS'
    We need:        'JH01FL6498'
    """
    if pd.isna(vehicle_detail):
        return vehicle_detail
    text = str(vehicle_detail).strip()
    # Match pattern: 2 letters + 2 digits + 2 letters + 4 digits (standard Indian registration)
    match = re.match(r'([A-Z]{2}\d{2}[A-Z]{1,2}\d{4})', text.upper())
    if match:
        return match.group(1)
    # Also try with RJ prefix (one vehicle has RJ32PA2174)
    match = re.match(r'([A-Z]{2}\d{2}[A-Z]{1,2}\d{4})', text.upper())
    if match:
        return match.group(1)
    return text.split()[0] if text else text

def standardize_columns(df):
    """Clean and standardize column names and values."""
    df.columns = df.columns.str.replace('  ', ' ').str.strip()
    return df

def get_instrument_cols(df):
    """Identify instrument status columns based on known markers."""
    try:
        start_idx = df.columns.get_loc('TYPE OF VEHICLE') + 1
        # Try to find EMT column with different name variations
        emt_col = None
        for col in df.columns:
            if 'EMT' in col.upper():
                emt_col = col
                break
        if emt_col:
            end_idx = df.columns.get_loc(emt_col)
        else:
            # Fallback: use all columns after TYPE OF VEHICLE except last
            end_idx = len(df.columns) - 1
        return df.columns[start_idx:end_idx].tolist()
    except Exception:
        return [c for c in df.columns if any(kw in c.upper() for kw in 
                ['STRETCHER', 'OXYGEN', 'MACHINE', 'SPLINT', 'COLLAR', 
                 'THERMOMETER', 'GLUCOMETER', 'PULSE', 'NEBULIZER',
                 'SUCTION', 'DEFIBRILLATOR', 'VENTILATOR', 'MONITOR'])]

def process_ambulance_data(df):
    """Main data processing pipeline for ambulance status.
    Returns: (processed_df, instrument_cols, duplicate_count)
    """
    initial_count = len(df)
    df = standardize_columns(df)
    instrument_cols = get_instrument_cols(df)
    
    # Clean status values
    for col in instrument_cols:
        df[col] = df[col].astype(str).str.strip().str.upper()
        
    # Normalize district names
    if 'DISTRICT' in df.columns:
        df['DISTRICT'] = df['DISTRICT'].apply(normalize_district)
    
    # Normalize vehicle type
    if 'TYPE OF VEHICLE' in df.columns:
        df['TYPE OF VEHICLE'] = df['TYPE OF VEHICLE'].apply(normalize_vehicle_type)
    
    # Identify Vehicle Detail column (handle typos like DEITALS vs DETAILS)
    veh_detail_col = None
    for col in df.columns:
        if 'VEHICLE' in col.upper() and ('DETAIL' in col.upper() or 'DEITAL' in col.upper()):
            veh_detail_col = col
            break
            
    if veh_detail_col:
        df['VEHICLE_ID'] = df[veh_detail_col].apply(extract_vehicle_id)
        
        # Deduplicate based on Timestamp if possible
        if 'Timestamp' in df.columns:
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Remove GMT and other timezone strings that might confuse pandas
                    temp_time = df['Timestamp'].astype(str).str.replace('GMT', '', case=False)
                    # Try flexible parsing
                    df['_Parsed_Time'] = pd.to_datetime(temp_time, errors='coerce')
                
                # Sort: Latest items at the bottom
                df = df.sort_values(by=['_Parsed_Time', 'Timestamp'], ascending=True)
                # Keep the last (latest) one
                df = df.drop_duplicates(subset=['VEHICLE_ID'], keep='last')
                df = df.drop(columns=['_Parsed_Time'])
            except Exception:
                df = df.drop_duplicates(subset=['VEHICLE_ID'], keep='last')
        else:
            df = df.drop_duplicates(subset=['VEHICLE_ID'], keep='last')
    elif 'VEHICLE_ID' not in df.columns:
        # Fallback if no specific column found but we have other columns
        # No deduplication possible without id
        pass
    
    # Area mapping
    urban_list = ['RANCHI', 'DHANBAD', 'BOKARO', 'EAST SINGHBHUM']
    if 'DISTRICT' in df.columns:
        df['Area Level'] = df['DISTRICT'].apply(lambda x: 'Urban' if str(x).upper() in urban_list else 'Rural')
    else:
        df['Area Level'] = 'Unknown'
    
    # Health Metrics
    df['Working Count'] = (df[instrument_cols] == 'WORKING').sum(axis=1)
    df['Not Working Count'] = (df[instrument_cols] == 'NOT WORKING').sum(axis=1)
    df['Not Available Count'] = df[instrument_cols].apply(
        lambda row: row.isin(['NOT AVALIABLE', 'NOT AVAILABLE', 'NAN', '']).sum(), axis=1)
    df['Total Applicable'] = df['Working Count'] + df['Not Working Count']
    df['Health %'] = (df['Working Count'] / df['Total Applicable'] * 100).fillna(0).round(2)
    
    # Risk Classification
    def classify_risk(h):
        if h < 50: return "High Risk"
        elif h <= 80: return "Medium Risk"
        return "Low Risk"
    
    df['Risk Level'] = df['Health %'].apply(classify_risk)
    
    duplicate_count = initial_count - len(df)
    return df, instrument_cols, duplicate_count

def process_master_fleet(master_df):
    """Process the master fleet data from Check.xlsx MasterSheet format.
    
    Expected columns: REG NO PERMANENT, DISTRICT, Vehicle Model, Vehicle Type,
                      HOTO Status, HOTO Status by ZHL+CS+EMRI, etc.
    """
    master_df = master_df.copy()
    
    # Standardize column names
    master_df.columns = master_df.columns.str.strip()
    
    # Identify the vehicle ID column
    id_col = None
    for candidate in ['REG NO PERMANENT', 'Registration No.', 'REG NO']:
        if candidate in master_df.columns:
            id_col = candidate
            break
    
    if id_col is None:
        # Try first column that looks like vehicle IDs
        for col in master_df.columns:
            sample = master_df[col].dropna().astype(str).head(5)
            if sample.str.match(r'[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}').any():
                id_col = col
                break
    
    if id_col is None:
        id_col = master_df.columns[0]
    
    # Clean vehicle IDs  
    master_df['VEHICLE_ID'] = master_df[id_col].astype(str).str.strip().str.replace('\n', '')
    
    # Normalize district
    if 'DISTRICT' in master_df.columns or 'District' in master_df.columns:
        dist_col = 'DISTRICT' if 'DISTRICT' in master_df.columns else 'District'
        master_df['DISTRICT'] = master_df[dist_col].apply(normalize_district)
    
    # Normalize vehicle type
    type_col = None
    for candidate in ['Vehicle Type', 'Type of Vehicle', 'TYPE OF VEHICLE']:
        if candidate in master_df.columns:
            type_col = candidate
            break
    if type_col:
        master_df['VEHICLE_TYPE'] = master_df[type_col].apply(normalize_vehicle_type)
    
    # Categorize fleet status
    hoto_col = 'HOTO Status' if 'HOTO Status' in master_df.columns else None
    zhl_col = 'HOTO Status by ZHL+CS+EMRI' if 'HOTO Status by ZHL+CS+EMRI' in master_df.columns else None
    
    def get_fleet_status(row):
        hoto = str(row.get(hoto_col, '')).strip().upper() if hoto_col else ''
        zhl = str(row.get(zhl_col, '')).strip().upper() if zhl_col else ''
        
        if 'UNDER CS REPAIR' in zhl:
            return 'Under CS Repair'
        elif 'PENDING FROM EMRI' in zhl:
            return 'Pending from EMRI'
        elif 'HOTO PENDING' in hoto:
            return 'HOTO Pending'
        elif 'HOTO' in hoto:
            return 'On-Road (HOTO Done)'
        return 'Unknown'
    
    master_df['Fleet Status'] = master_df.apply(get_fleet_status, axis=1)
    
    return master_df

def get_missing_trucking(fleet_df, master_df):
    """Identifies missing fleet submissions using clean vehicle IDs."""
    if master_df is None or master_df.empty:
        return []
    
    # Process master data
    processed_master = process_master_fleet(master_df)
    
    # Get clean IDs from both
    master_ids = set(processed_master['VEHICLE_ID'].astype(str).str.strip().str.upper())
    
    if 'VEHICLE_ID' in fleet_df.columns:
        reported_ids = set(fleet_df['VEHICLE_ID'].astype(str).str.strip().str.upper())
    else:
        reported_ids = set(fleet_df['VEHICLE DEITALS'].apply(extract_vehicle_id).astype(str).str.strip().str.upper())
    
    missing = master_ids - reported_ids
    return sorted(list(missing))

def get_fleet_analysis(master_df):
    """Get comprehensive fleet analysis from master data."""
    processed = process_master_fleet(master_df)
    
    analysis = {
        'total_fleet': len(processed),
        'by_type': processed['VEHICLE_TYPE'].value_counts().to_dict() if 'VEHICLE_TYPE' in processed.columns else {},
        'by_district': processed['DISTRICT'].value_counts().to_dict() if 'DISTRICT' in processed.columns else {},
        'by_status': processed['Fleet Status'].value_counts().to_dict(),
        'under_repair': processed[processed['Fleet Status'] == 'Under CS Repair'],
        'pending_emri': processed[processed['Fleet Status'] == 'Pending from EMRI'],
        'hoto_pending': processed[processed['Fleet Status'] == 'HOTO Pending'],
        'on_road': processed[processed['Fleet Status'] == 'On-Road (HOTO Done)'],
        'processed_df': processed,
    }
    
    return analysis
