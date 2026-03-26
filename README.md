# Ambulance Monitoring Dashboard

This is a complete end-to-end data analytics dashboard for Ambulance Monitoring in Jharkhand.
It processes instrument data across various ambulances, highlights high-risk vehicles, and provides top-level analytics.

## Features Included
1. **Interactive Dashboard**: KPI Cards showing Total Ambulances, Working / Failure %, and Risk Levels.
2. **Dynamic Risk Logic**: Ambulances are flagged as High Risk (<50%), Medium Risk (50-80%), or Low Risk (>80%).
3. **Advanced Analytics**: Pinpoints the most frequently failing instruments (Sabse jayeda kharab) and the worst-performing districts.
4. **Urban vs Rural**: Logical mapping derived from District names to compare performance.
5. **Auto Data Ingestion**: Built with `@st.cache_data(ttl=600)` to refresh every 10 minutes from source. Code includes instructions for connecting a live Google Sheet.
6. **Detailed Filters**: Filter by District, Urban/Rural Area, and select specific ambulances.
7. **Premium UI**: Custom CSS to make the dashboard look professional and sleek with Dark Mode styling.

## How to Run

1. **Activate the Environment:**
   ```bash
   source /home/deveshjha/108/108/bin/activate
   ```

2. **Navigate to the Project Folder:**
   ```bash
   cd /home/deveshjha/108/Ambulance_Monitoring_Dashboard
   ```

3. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Dashboard:**
   ```bash
   streamlit run app.py
   ```

4. **Access the Application:**
   Open the generated Local URL (usually `http://localhost:8501`) in your browser.

## Using Google Sheets API (Auto-Ingestion)
To configure the dashboard to fetch directly from Google Sheets automatically:
1. Open your Google Sheet.
2. Go to `File` -> `Share` -> `Publish to Web`.
3. Choose `Entire Document` and `Comma-separated values (.csv)`.
4. Click `Publish` and copy the generated link.
5. Open `app.py` and replace the `file_path` variable inside the `load_data()` function with your URL.
6. The dashboard will now automatically refresh from your Live Google Sheet due to the built-in `@st.cache_data`.
