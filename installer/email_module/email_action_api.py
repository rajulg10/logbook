from flask import Flask, request, jsonify
import os
from db.database import update_report_status, get_report, get_user_by_id, add_approval_log, add_email_queue
from email_sender import EmailSender
import socket

app = Flask(__name__)

def get_admin_email():
    # You should implement this to fetch the admin email from your DB/config
    admin = get_user_by_id(1)  # Example: admin user_id = 1
    return admin['email'] if admin else None

def _is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

@app.route('/api/report/approve', methods=['GET'])
def approve_report():
    report_id = request.args.get('report_id')
    admin_id = request.args.get('admin_id')
    print(f"DEBUG[approve_report] Called with report_id={report_id}, admin_id={admin_id}")
    if not report_id or not admin_id:
        return jsonify({'success': False, 'message': 'Missing report_id or admin_id'}), 400
    update_report_status(report_id, 'approved_admin', admin_id)
    # Add approval log for admin to include in PDF signatures
    add_approval_log(report_id, admin_id, 'approve_admin')
    # Generate PDF and email to admin
    try:
        print("DEBUG[approve_report] Entering PDF generation and email send block")
        from pdf.pdf_generator import PDFGenerator
        report = get_report(report_id)
        if not report:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        # Assume template_path can be fetched or is fixed for now
        template_path = None
        if hasattr(report, 'template_path'):
            template_path = report['template_path']
        elif 'template_path' in report:
            template_path = report['template_path']
        else:
            # You may need to update this logic to fetch the template path
            template_path = 'templates/default_template.xlsx'
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'approved_reports')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, f"report_{report_id}_final.pdf")
        PDFGenerator.generate_report_pdf(report_id, template_path, output_path)
        print(f"DEBUG[approve_report] PDFGenerator output_path: {output_path}, exists: {os.path.exists(output_path)}")
        # Send PDF to admin and handle failures
        sender = EmailSender()
        # Attempt immediate send, else queue
        if _is_online():
            sent, send_msg = sender.send_final_pdf_to_admin(report_id, report['title'], admin_id, pdf_path=output_path)
            print(f"DEBUG: send_final_pdf_to_admin result: success={sent}, message={send_msg}")
            if not sent:
                add_email_queue(report_id, admin_id, output_path)
                return jsonify({'success': True, 'message': f'Email queued for later: {send_msg}'}), 200
            return jsonify({'success': True, 'message': 'Email sent successfully'}), 200
        else:
            add_email_queue(report_id, admin_id, output_path)
            print("DEBUG: Offline mode, email queued for later")
            return jsonify({'success': True, 'message': 'Offline mode, email queued for later'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'PDF or Email error: {str(e)}'}), 500

@app.route('/api/report/send_back', methods=['GET'])
def send_back_report():
    report_id = request.args.get('report_id')
    admin_id = request.args.get('admin_id')
    if not report_id or not admin_id:
        return jsonify({'success': False, 'message': 'Missing report_id or admin_id'}), 400
    update_report_status(report_id, 'needs_revision', admin_id)
    return jsonify({'success': True, 'message': 'Report sent back for review'}), 200

if __name__ == '__main__':
    app.run(port=5050, debug=True)
