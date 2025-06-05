import sys
import os
from pathlib import Path
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
from utils.pdf_excel_tools import convert_excel_to_pdf, append_signatures_to_pdf
from datetime import datetime, timezone

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.database import get_report, get_user_by_id
from utils.excel_handler import ExcelHandler

class PDFGenerator:
    @staticmethod
    def generate_report_pdf(report_id, template_path, output_path):
        """Generate a PDF report from a report ID and template"""
        try:
            # Get the report data from the database
            report = get_report(report_id)
            if not report:
                return False, "Report not found"
            
            # First create an Excel file with the data
            temp_dir = tempfile.gettempdir()
            temp_excel = os.path.join(temp_dir, f"report_{report_id}.xlsx")
            
            # Extract report fields data
            fields_data = report['fields']
            
            # Defensive check for fields_data
            if not isinstance(fields_data, dict):
                raise ValueError(f"Expected fields_data to be dict, got {type(fields_data)}: {fields_data}")
            
            # Build signature list with descriptive roles, always include all admins' latest 'approve_admin' actions as 'Approved By'
            role_map = {
                'submit': 'Prepared By',
                'approve_leader': 'Verified By',
                'approve_admin': 'Approved By'
            }
            latest_log_per_user = {}
            admin_logs = {}
            for log in report['approval_logs']:
                if log['action'] == 'approve_admin':
                    # For admin approvals, keep latest per admin
                    key = f"admin:{log['actor_name']}"
                    admin_logs[key] = log
                elif log['action'] in role_map:
                    key = log['actor_name']
                    latest_log_per_user[key] = log
            # Merge admin logs into signature set (distinct admins, latest only)
            for admin_log in admin_logs.values():
                latest_log_per_user[admin_log['actor_name']] = admin_log
            # Sort by timestamp ascending
            sorted_logs = sorted(latest_log_per_user.values(), key=lambda l: l['timestamp'])
            signatures = []
            for log in sorted_logs:
                # Include employee code for each signer
                user_info = get_user_by_id(log['action_by'])
                emp_code = user_info.get('emp_code', '') if user_info else ''
                # Convert UTC timestamp to local system time
                raw_ts = log['timestamp']
                try:
                    dt = datetime.strptime(raw_ts, '%Y-%m-%d %H:%M:%S')
                    dt = dt.replace(tzinfo=timezone.utc).astimezone()
                    ts_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    ts_str = raw_ts
                signatures.append({
                    'role': role_map.get(log['action'], 'Signed By'),
                    'name': log['actor_name'],
                    'emp_code': emp_code,
                    'timestamp': ts_str
                })
            fields_data['signatures'] = signatures

            # Determine user_excel_path and log
            user_excel_path = report.get('excel_file_path') or fields_data.get('excel_file_path')
            with open("pdf_debug_log.txt", "a") as f:
                f.write(f"DEBUG: user_excel_path={repr(user_excel_path)}, exists={os.path.exists(user_excel_path)}\n")
            # Use user-filled Excel if available
            if user_excel_path and os.path.exists(user_excel_path):
                try:
                    import shutil
                    shutil.copy(user_excel_path, temp_excel)
                    with open("pdf_debug_log.txt", "a") as f:
                        f.write(f"DEBUG: Successfully copied user Excel to temp: {temp_excel}\n")
                except Exception as e:
                    with open("pdf_debug_log.txt", "a") as f:
                        f.write(f"ERROR: copying user Excel failed: {e}\n")
                    # Fallback to template fill
                    if not ExcelHandler.create_report_from_template(template_path, temp_excel, fields_data):
                        return False, "Failed to create Excel report after copy error"
            else:
                with open("pdf_debug_log.txt", "a") as f:
                    f.write("DEBUG: user Excel not found, falling back to template\n")
                if not ExcelHandler.create_report_from_template(template_path, temp_excel, fields_data):
                    return False, "Failed to create Excel report from template"

            # Convert Excel to PDF using LibreOffice
            temp_pdf = temp_excel.replace('.xlsx', '_temp.pdf')
            pdf_success = convert_excel_to_pdf(temp_excel, temp_pdf)
            if not pdf_success:
                return False, "Failed to convert Excel to PDF. Ensure LibreOffice is installed and 'soffice' is in your PATH."

            # Append digital signatures to the PDF
            append_signatures_to_pdf(temp_pdf, output_path, signatures)

            # Clean up temp files
            try:
                os.remove(temp_excel)
                os.remove(temp_pdf)
            except Exception as e:
                print(f"Warning: Could not remove temp files - {e}")

            return True, output_path
                
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return False, str(e) 