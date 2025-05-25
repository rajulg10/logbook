import smtplib
import os
import sys
import ssl
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Load environment variables
load_dotenv()

from db.database import get_user_by_id

class EmailSender:
    def __init__(self):
        # Reload environment variables (in case .env was updated)
        load_dotenv(override=True)
        # Load email settings from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_email = os.getenv('SENDER_EMAIL', self.smtp_username)
        
    def send_email(self, recipient_email, subject, body, attachment_path=None):
        """Send an email with optional attachment"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Attach body
            msg.attach(MIMEText(body, 'html'))
            
            # Attach file if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as file:
                    attachment = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
                attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(attachment)
            
            # Connect to SMTP server and send email with SSL/TLS (bypass SSL verification)
            context = ssl._create_unverified_context()
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
            with server:
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True, "Email sent successfully"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def send_notification_to_unit_leader(self, report_id, report_title, user_id, unit_leader_id):
        """Send a notification to a unit leader for report review"""
        try:
            user = get_user_by_id(user_id)
            unit_leader = get_user_by_id(unit_leader_id)
            
            if not user or not unit_leader:
                return False, "User or Unit Leader not found"
            
            subject = f"New Report for Review: {report_title}"
            body = f"""
            <html>
            <body>
                <h2>New Report for Review</h2>
                <p>Hello {unit_leader['username']},</p>
                <p>A new report has been submitted by {user['username']} and requires your review.</p>
                <p><strong>Report ID:</strong> {report_id}</p>
                <p><strong>Report Title:</strong> {report_title}</p>
                <p>Please log in to the system to review this report.</p>
                <p>Thank you,<br>LogBook System</p>
            </body>
            </html>
            """
            
            return self.send_email(unit_leader['email'], subject, body)
        except Exception as e:
            return False, f"Failed to send unit leader notification: {str(e)}"
    
    def send_notification_to_admin(self, report_id, report_title, user_id, unit_leader_id, admin_id, excel_path=None):
        """Send a notification to an admin for final approval with Excel attachment and action links"""
        try:
            # Determine backend API URL
            api_base_url = os.getenv('API_BASE_URL', 'http://localhost:5050')
            user = get_user_by_id(user_id)
            unit_leader = get_user_by_id(unit_leader_id)
            admin = get_user_by_id(admin_id)
            
            if not user or not unit_leader or not admin:
                return False, "User, Unit Leader, or Admin not found"
            
            subject = f"Report Ready for Final Approval: {report_title}"
            # Construct action URLs
            approve_url = f"{api_base_url}/api/report/approve?report_id={report_id}&admin_id={admin_id}"
            send_back_url = f"{api_base_url}/api/report/send_back?report_id={report_id}&admin_id={admin_id}"
            body = f"""
            <html>
            <body>
                <h2>Report Ready for Final Approval</h2>
                <p>Hello {admin['username']},</p>
                <p>A report has been reviewed and approved by Unit Leader {unit_leader['username']} and is now ready for your final approval.</p>
                <p><strong>Report ID:</strong> {report_id}</p>
                <p><strong>Report Title:</strong> {report_title}</p>
                <p><strong>Created by:</strong> {user['username']}</p>
                <p>Please use one of the options below:</p>
                <p><a href="{approve_url}">Approve Report</a> | <a href="{send_back_url}">Request Revision</a></p>
                <p>Thank you,<br>LogBook System</p>
            </body>
            </html>
            """
            
            # Attach Excel report if provided
            return self.send_email(admin['email'], subject, body, attachment_path=excel_path)
        except Exception as e:
            return False, f"Failed to send admin notification: {str(e)}"
    
    def send_final_pdf_to_admin(self, report_id, report_title, admin_id, pdf_path=None):
        """Send the final approved PDF to the admin"""
        try:
            admin = get_user_by_id(admin_id)
            
            if not admin:
                return False, "Admin not found"
            
            subject = f"Final PDF Report Approved"
            body = f"""
            <html>
            <body>
                <h2>Final PDF Report Approved</h2>
                <p>Hello {admin['username']},</p>
                <p>The final PDF report has been approved and is attached to this email.</p>
                <p><strong>Report ID:</strong> {report_id}</p>
                <p><strong>Report Title:</strong> {report_title}</p>
                <p>Status: Approved and finalized.</p>
                <p>Thank you,<br>LogBook System</p>
            </body>
            </html>
            """
            
            return self.send_email(admin['email'], subject, body, attachment_path=pdf_path)
        except Exception as e:
            return False, f"Failed to send final PDF to admin: {str(e)}"
    
    def send_final_approval_notification(self, report_id, report_title, user_id, pdf_path=None):
        """Send a final approval notification to the user who created the report"""
        try:
            user = get_user_by_id(user_id)
            
            if not user:
                return False, "User not found"
            
            subject = f"Report Approved: {report_title}"
            body = f"""
            <html>
            <body>
                <h2>Report Approved</h2>
                <p>Hello {user['username']},</p>
                <p>Your report "{report_title}" has been approved and finalized.</p>
                <p><strong>Report ID:</strong> {report_id}</p>
                {("<p>The final report is attached to this email as a PDF.</p>") if pdf_path else ""}
                <p>Thank you,<br>LogBook System</p>
            </body>
            </html>
            """
            
            return self.send_email(user['email'], subject, body, pdf_path)
        except Exception as e:
            return False, f"Failed to send final approval notification: {str(e)}"
    
    def send_rejection_notification(self, report_id, report_title, user_id, rejected_by_id, comments):
        """Send a notification to the user that their report was rejected/needs revision"""
        try:
            user = get_user_by_id(user_id)
            rejected_by = get_user_by_id(rejected_by_id)
            
            if not user or not rejected_by:
                return False, "User or Reviewer not found"
            
            subject = f"Report Requires Revision: {report_title}"
            body = f"""
            <html>
            <body>
                <h2>Report Requires Revision</h2>
                <p>Hello {user['username']},</p>
                <p>Your report "{report_title}" requires some revisions before it can be approved.</p>
                <p><strong>Report ID:</strong> {report_id}</p>
                <p><strong>Reviewed by:</strong> {rejected_by['username']}</p>
                <p><strong>Comments:</strong> {comments}</p>
                <p>Please log in to the system to make the necessary revisions.</p>
                <p>Thank you,<br>LogBook System</p>
            </body>
            </html>
            """
            
            return self.send_email(user['email'], subject, body)
        except Exception as e:
            return False, f"Failed to send rejection notification: {str(e)}"