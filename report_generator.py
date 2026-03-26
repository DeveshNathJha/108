import pandas as pd
import io
from fpdf import FPDF

class AmbulancePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Ambulance Health Report', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def generate_pdf(amb_data, instrument_cols):
    """Generates a professional PDF for a specific ambulance."""
    pdf = AmbulancePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    
    # Vehicle Info
    pdf.cell(0, 10, f"Vehicle Details: {amb_data['VEHICLE DEITALS']}", ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"District: {amb_data['DISTRICT']}", ln=True)
    pdf.cell(0, 10, f"Health Score: {amb_data['Health %']}%", ln=True)
    pdf.cell(0, 10, f"Risk Status: {amb_data['Risk Level']}", ln=True)
    pdf.cell(0, 10, f"EMT Name: {amb_data.get('EMT NAME / ID', 'Not Specified')}", ln=True)
    pdf.ln(10)
    
    # Instrument Table
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 10, 'Instrument Name', 1)
    pdf.cell(60, 10, 'Current Status', 1, ln=True)
    
    pdf.set_font('Arial', '', 10)
    for inst in instrument_cols:
        pdf.cell(100, 8, str(inst)[:50], 1)
        pdf.cell(60, 8, str(amb_data[inst]), 1, ln=True)
        
    return bytes(pdf.output(dest='S'))

def generate_excel_report(df_filtered, missing_ids=None):
    """Generates a multi-sheet Excel report with charts and summary metrics."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Raw Dashboard Data
        df_filtered.to_excel(writer, index=False, sheet_name='Dashboard_Data')
        
        workbook = writer.book
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        
        # Sheet 2: Professional Summary (Inspired by template)
        summary_sheet = workbook.add_worksheet('Fleet_Summary_Insights')
        
        # Summary Metrics
        summary_sheet.write('A1', 'JHARKHAND 108 AMBULANCE FLEET SUMMARY', header_format)
        summary_sheet.write('A3', 'Total Vehicles Reported')
        summary_sheet.write('B3', len(df_filtered))
        summary_sheet.write('A4', 'Average Operational Health')
        summary_sheet.write('B4', f"{df_filtered['Health %'].mean():.2f}%")
        summary_sheet.write('A5', 'High Risk Vehicles (Immediate Attention)')
        summary_sheet.write('B5', len(df_filtered[df_filtered['Risk Level'] == 'High Risk']))
        
        # Missing Data Tracking Table
        if missing_ids is not None and len(missing_ids) > 0:
            summary_sheet.write('A8', 'PENDING / MISSING VEHICLE REPORTS', header_format)
            for i, mid in enumerate(missing_ids):
                summary_sheet.write(i+8, 0, mid)
        
        # Add Charts
        # We need a data sheet for the chart source
        data_sheet = workbook.add_worksheet('Chart_Data')
        risk_counts = df_filtered['Risk Level'].value_counts()
        data_sheet.write_column('A1', risk_counts.index)
        data_sheet.write_column('B1', risk_counts.values)
        
        # Risk Distribution Pie Chart
        pie_chart = workbook.add_chart({'type': 'pie'})
        pie_chart.add_series({
            'name': 'Risk Levels',
            'categories': ['Chart_Data', 0, 0, len(risk_counts)-1, 0],
            'values':     ['Chart_Data', 0, 1, len(risk_counts)-1, 1],
            'points': [
                {'fill': {'color': '#f85149'}}, # High
                {'fill': {'color': '#d29922'}}, # Medium
                {'fill': {'color': '#238636'}}, # Low
            ]
        })
        pie_chart.set_title({'name': 'Operational Risk Distribution'})
        summary_sheet.insert_chart('D2', pie_chart)

    return output.getvalue()
