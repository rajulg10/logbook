import os
import subprocess
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def convert_excel_to_pdf(excel_path, output_pdf_path):
    """
    Converts an Excel file to PDF using LibreOffice (soffice) in headless mode.
    Before conversion, sets the worksheet scaling to fit to 1 page wide by 1 page tall.
    Returns True if successful, False otherwise.
    """
    try:
        # Set scaling to fit to 1 page wide by 1 page tall using openpyxl
        import openpyxl
        wb = openpyxl.load_workbook(excel_path)
        for ws in wb.worksheets:
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 1
        wb.save(excel_path)
        
        output_dir = os.path.dirname(output_pdf_path)
        cmd = [
            'soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, excel_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # LibreOffice names the output PDF after the Excel file
        base_pdf = os.path.splitext(os.path.basename(excel_path))[0] + '.pdf'
        generated_pdf = os.path.join(output_dir, base_pdf)
        if os.path.exists(generated_pdf):
            os.rename(generated_pdf, output_pdf_path)
            return True
        else:
            print(f"LibreOffice PDF not found: {generated_pdf}")
            print(f"stdout: {result.stdout.decode()}")
            print(f"stderr: {result.stderr.decode()}")
            return False
    except Exception as e:
        print(f"Error converting Excel to PDF: {e}")
        return False

def append_signatures_to_pdf(input_pdf_path, output_pdf_path, signatures):
    """
    Overlay digital signatures onto the bottom of the last page of a PDF.
    """
    from tempfile import NamedTemporaryFile
    from reportlab.pdfgen import canvas
    tmp_sig_pdf = NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_sig_pdf.close()
    # Create overlay PDF with signatures at bottom
    c = canvas.Canvas(tmp_sig_pdf.name, pagesize=letter)
    x_margin = 50
    y_start = 50
    line_height = 12
    # Title
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_margin, y_start + (len(signatures) + 1) * line_height, "Digital Signatures")
    # Headers
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x_margin, y_start + len(signatures) * line_height, "Role")
    c.drawString(x_margin + 100, y_start + len(signatures) * line_height, "Name")
    c.drawString(x_margin + 250, y_start + len(signatures) * line_height, "Emp Code")
    c.drawString(x_margin + 400, y_start + len(signatures) * line_height, "Date/Time")
    # Data rows
    c.setFont("Helvetica", 8)
    for i, sig in enumerate(signatures):
        y = y_start + (len(signatures) - i - 1) * line_height
        c.drawString(x_margin, y, sig['role'])
        c.drawString(x_margin + 100, y, sig['name'])
        c.drawString(x_margin + 250, y, sig.get('emp_code', ''))
        c.drawString(x_margin + 400, y, sig['timestamp'])
    c.save()
    # Merge overlay into last page of original PDF
    pdf_writer = PyPDF2.PdfWriter()
    sig_reader = PyPDF2.PdfReader(tmp_sig_pdf.name)
    with open(input_pdf_path, 'rb') as orig_pdf:
        pdf_reader = PyPDF2.PdfReader(orig_pdf)
        for idx, page in enumerate(pdf_reader.pages):
            if idx == len(pdf_reader.pages) - 1:
                page.merge_page(sig_reader.pages[0])
            pdf_writer.add_page(page)
    with open(output_pdf_path, 'wb') as out_pdf:
        pdf_writer.write(out_pdf)
    os.unlink(tmp_sig_pdf.name)
