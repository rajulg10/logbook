import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem, 
                           QTabWidget, QMessageBox, QHeaderView, QFrame,
                           QSplitter, QComboBox, QLineEdit, QFormLayout,
                           QScrollArea, QGroupBox, QSpacerItem, QSizePolicy,
                           QFileDialog, QDialog, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.database import (get_user_reports, create_report, add_report_data, 
                        update_report_status, get_report, add_approval_log, get_user_by_id)
from utils.excel_handler import ExcelHandler
from ui.report_form import ReportForm
from utils.auth import Auth
from email_sender import EmailSender

class ExcelReportForm(QWidget):
    """Widget for creating reports based on Excel templates without conversion"""
    report_submitted = pyqtSignal(int)  # Signal to emit report_id when submitted
    
    def __init__(self, template_path, user_id):
        super().__init__()
        self.template_path = template_path
        self.user_id = user_id
        self.report_id = None
        self.excel_file_path = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI for Excel-based report creation"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Add form title
        title_label = QLabel("Create New Report")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Add report title field
        title_group = QGroupBox("Report Information")
        title_form = QFormLayout(title_group)
        
        self.report_title = QLineEdit()
        self.report_title.setPlaceholderText("Enter a title for this report")
        title_form.addRow("Report Title:", self.report_title)
        
        main_layout.addWidget(title_group)
        
        # Add Excel file section
        excel_group = QGroupBox("Excel Report Template")
        excel_layout = QVBoxLayout(excel_group)
        
        template_info = QLabel(f"Template: {os.path.basename(self.template_path)}")
        excel_layout.addWidget(template_info)
        
        instructions = QLabel(
            "Click 'Open Template for Editing' to directly edit the template uploaded by the administrator. "
            "After editing, click 'Save Changes' to confirm your edits."
        )
        instructions.setWordWrap(True)
        excel_layout.addWidget(instructions)
        
        buttons_layout = QHBoxLayout()
        
        open_template_btn = QPushButton("Open Template for Editing")
        open_template_btn.setStyleSheet("background-color: #3498db; color: white;")
        open_template_btn.clicked.connect(self.open_template_for_editing)
        buttons_layout.addWidget(open_template_btn)
        
        save_changes_btn = QPushButton("Save Changes")
        save_changes_btn.setStyleSheet("background-color: #9b59b6; color: white;")
        save_changes_btn.clicked.connect(self.save_changes)
        buttons_layout.addWidget(save_changes_btn)
        
        excel_layout.addLayout(buttons_layout)
        
        self.excel_status_label = QLabel("Status: Template not edited yet")
        excel_layout.addWidget(self.excel_status_label)
        
        main_layout.addWidget(excel_group)
        
        # Add digital signature info section
        signature_group = QGroupBox("Digital Signature Information")
        signature_layout = QVBoxLayout(signature_group)
        
        main_window = QApplication.instance().activeWindow()
        user = None
        if hasattr(main_window, 'current_user'):
            from db.database import get_user_by_id
            user = get_user_by_id(main_window.current_user['id'])
        if user and 'emp_code' in user and 'designation' in user and user['emp_code'] and user['designation']:
            signature_info = QLabel(
                f"Your report will be automatically signed with the following information:\n"
                f"Employee Code: {user['emp_code']}\n"
                f"Designation: {user['designation']}"
            )
            signature_info.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            signature_info = QLabel(
                "Your profile is missing employee code or designation information that is required for digital signature.\n"
                "Please contact an administrator to update your profile."
            )
            signature_info.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
        signature_info.setWordWrap(True)
        signature_layout.addWidget(signature_info)
        
        main_layout.addWidget(signature_group)
        
        # Add buttons at the bottom
        action_buttons_layout = QHBoxLayout()
        
        save_draft_btn = QPushButton("Save as Draft")
        save_draft_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                min-width: 150px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_draft_btn.clicked.connect(self.save_as_draft)
        action_buttons_layout.addWidget(save_draft_btn)
        
        submit_btn = QPushButton("Submit for Review")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px;
                min-width: 150px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        submit_btn.clicked.connect(self.submit_report)
        action_buttons_layout.addWidget(submit_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                min-width: 150px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self.clear_form)
        action_buttons_layout.addWidget(clear_btn)
        
        main_layout.addLayout(action_buttons_layout)
    
    def open_template_for_editing(self):
        """Open the admin-uploaded template directly for editing"""
        if not self.report_title.text():
            QMessageBox.warning(self, "Missing Information", "Please enter a report title first.")
            return
        
        # Create a report in draft status to get a report ID
        if not self.report_id:
            self.report_id = create_report(self.user_id, self.report_title.text())
            if not self.report_id:
                QMessageBox.warning(self, "Error", "Failed to create report.")
                return
        
        # Instead of generating a new file, we create a copy of the template in a user-specific location
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_reports', str(self.user_id))
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create a file name based on the report ID and original template name
        file_name = f"report_{self.report_id}_{os.path.basename(self.template_path)}"
        file_path = os.path.join(reports_dir, file_name)
        
        # If this is the first time, copy the template; otherwise, use existing file
        if not os.path.exists(file_path):
            import shutil
            try:
                shutil.copy2(self.template_path, file_path)
                # Add report title as data
                add_report_data(self.report_id, "report_title", self.report_title.text())
                add_report_data(self.report_id, "excel_file_path", file_path)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to copy template file: {str(e)}")
                return
        
        self.excel_file_path = file_path
        self.excel_status_label.setText(f"Status: Editing template at {file_path}")
        
        # Open the file in the default application
        try:
            import subprocess
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
                
            QMessageBox.information(
                self, "Template Opened", 
                "The Excel template has been opened for editing. Fill in your data and save the file, "
                "then click 'Save Changes' to register your edits."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open Excel file: {str(e)}")
    
    def save_changes(self):
        """Save changes after editing the template"""
        if not self.report_id or not self.excel_file_path:
            QMessageBox.warning(self, "No Open Template", "Please open the template for editing first.")
            return
        
        # Check if the file exists and was modified
        if not os.path.exists(self.excel_file_path):
            QMessageBox.warning(self, "File Not Found", "The Excel file cannot be found. Please open the template again.")
            return
        
        # Update report title if changed
        if self.report_title.text():
            add_report_data(self.report_id, "report_title", self.report_title.text())
        
        self.excel_status_label.setText(f"Status: Changes saved for {os.path.basename(self.excel_file_path)}")
        QMessageBox.information(
            self, "Changes Saved", 
            "Your changes to the Excel file have been saved. You can continue editing, save as draft, or submit for review."
        )
    
    def save_as_draft(self):
        """Save the report as a draft"""
        if not self.report_id or not self.excel_file_path:
            QMessageBox.warning(self, "No Data", "Please open and edit the template first.")
            return
            
        if not os.path.exists(self.excel_file_path):
            QMessageBox.warning(self, "File Not Found", "The Excel file cannot be found. Please open the template again.")
            return
        
        # Update report status to draft (it should already be draft, but just to be sure)
        update_report_status(self.report_id, 'draft', self.user_id)
        
        QMessageBox.information(self, "Success", "Report saved as draft.")
        self.report_submitted.emit(self.report_id)
    
    def submit_report(self):
        """Submit the report for review with automatic digital signature"""
        if not self.report_id or not self.excel_file_path:
            QMessageBox.warning(self, "No Data", "Please open and edit the template first.")
            return
            
        if not os.path.exists(self.excel_file_path):
            QMessageBox.warning(self, "File Not Found", "The Excel file cannot be found. Please open the template again.")
            return
        
        main_window = QApplication.instance().activeWindow()
        user = None
        if hasattr(main_window, 'current_user'):
            from db.database import get_user_by_id
            user = get_user_by_id(main_window.current_user['id'])
        if not user or not user.get('emp_code') or not user.get('designation'):
            QMessageBox.warning(self, "Missing Signature Information", 
                               "Your profile is missing employee code or designation required for digital signature. "
                               "Please contact an administrator to update your profile.")
            return
        
        # Generate digital signature
        signature = f"{user['emp_code']} - {user['designation']}"
        
        # Confirm submission
        reply = QMessageBox.question(
            self, "Confirm Submission", 
            f"Are you sure you want to submit this report for review?\nIt will be digitally signed as: {signature}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Removed single user_signature field; using approval_logs to gather all signatures
            # Update report status
            update_report_status(self.report_id, 'submitted', user['id'])
            
            # Add approval log with signature information
            add_approval_log(self.report_id, user['id'], 'submit', f"Submission with digital signature: {signature}")
            
            QMessageBox.information(self, "Success", "Report submitted for review with your digital signature.")
            self.report_submitted.emit(self.report_id)
    
    def clear_form(self):
        """Clear the form and reset"""
        self.report_title.clear()
        self.excel_file_path = None
        self.report_id = None
        self.excel_status_label.setText("Status: Template not edited yet")

class UserDashboard(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.email_sender = EmailSender()
        self.init_ui()
        self.refresh_data()
        
    def init_ui(self):
        """Initialize the UI"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget for different sections
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add Dashboard tab
        self.dashboard_tab = QWidget()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.setup_dashboard_tab()
        
        # Add New Report tab
        self.new_report_tab = QWidget()
        self.tab_widget.addTab(self.new_report_tab, "New Report")
        self.setup_new_report_tab()
        
        # Add My Reports tab
        self.reports_tab = QWidget()
        self.tab_widget.addTab(self.reports_tab, "My Reports")
        self.setup_reports_tab()
        
    def setup_dashboard_tab(self):
        """Set up the dashboard tab with summary info"""
        layout = QVBoxLayout(self.dashboard_tab)
        
        # Add welcome section
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        welcome_layout = QVBoxLayout(welcome_frame)
        
        welcome_label = QLabel(f"Welcome, {self.user['username']}!")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        welcome_layout.addWidget(welcome_label)
        
        instructions = QLabel("Use this system to create and manage your reports based on Excel templates.")
        instructions.setWordWrap(True)
        welcome_layout.addWidget(instructions)
        
        layout.addWidget(welcome_frame)
        
        # Add stats section
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        # Stats will be populated in refresh_data
        self.draft_count_label = QLabel("Draft: 0")
        self.draft_count_label.setStyleSheet("font-size: 16px; color: #3498db;")
        stats_layout.addWidget(self.draft_count_label)
        
        self.submitted_count_label = QLabel("Submitted: 0")
        self.submitted_count_label.setStyleSheet("font-size: 16px; color: #f39c12;")
        stats_layout.addWidget(self.submitted_count_label)
        
        self.approved_count_label = QLabel("Approved: 0")
        self.approved_count_label.setStyleSheet("font-size: 16px; color: #2ecc71;")
        stats_layout.addWidget(self.approved_count_label)
        
        self.rejected_count_label = QLabel("Needs Revision: 0")
        self.rejected_count_label.setStyleSheet("font-size: 16px; color: #e74c3c;")
        stats_layout.addWidget(self.rejected_count_label)
        
        layout.addWidget(stats_frame)
        
        # Recent reports section
        recent_label = QLabel("Recent Reports")
        recent_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(recent_label)
        
        self.recent_reports_table = QTableWidget()
        self.recent_reports_table.setColumnCount(4)
        self.recent_reports_table.setHorizontalHeaderLabels(["Title", "Created", "Status", "Actions"])
        self.recent_reports_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.recent_reports_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_reports_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.recent_reports_table)
        
        # Quick actions section
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        actions_layout = QHBoxLayout(actions_frame)
        
        new_report_btn = QPushButton("New Report")
        new_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        new_report_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        actions_layout.addWidget(new_report_btn)
        
        view_reports_btn = QPushButton("View All Reports")
        view_reports_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        view_reports_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        actions_layout.addWidget(view_reports_btn)
        
        layout.addWidget(actions_frame)
        
        # Add spacer at the bottom
        layout.addStretch()
        
    def setup_new_report_tab(self):
        """Set up the new report tab for creating reports based on templates"""
        layout = QVBoxLayout(self.new_report_tab)
        
        # Add header and instructions
        header = QLabel("Create New Report")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        instructions = QLabel("Select an Excel template below to create a new report:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create table for templates
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(4)
        self.templates_table.setHorizontalHeaderLabels(["ID", "Name", "Uploaded By", "Actions"])
        self.templates_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.templates_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.templates_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.templates_table)
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh Templates")
        refresh_btn.clicked.connect(self.refresh_templates)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)
        
        # Container for the selected template form
        self.report_form_container = QScrollArea()
        self.report_form_container.setWidgetResizable(True)
        self.report_form_container.setFrameShape(QFrame.NoFrame)
        
        # Placeholder widget
        placeholder = QLabel("Select a template from the list above to create a new report.")
        placeholder.setAlignment(Qt.AlignCenter)
        self.report_form_container.setWidget(placeholder)
        
        layout.addWidget(self.report_form_container)
        
    def refresh_templates(self):
        """Refresh the templates table"""
        from db.database import get_all_templates
        
        templates = get_all_templates()
        
        # Clear the table
        self.templates_table.setRowCount(0)
        
        for row, template in enumerate(templates):
            self.templates_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(template['id']))
            self.templates_table.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(template['name'])
            self.templates_table.setItem(row, 1, name_item)
            
            # Uploaded By
            uploader = get_user_by_id(template['uploaded_by'])
            uploader_name = uploader['username'] if uploader else "Unknown"
            uploader_item = QTableWidgetItem(uploader_name)
            self.templates_table.setItem(row, 2, uploader_item)
            
            # Actions
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Use button
            use_btn = QPushButton("Use Template")
            use_btn.setStyleSheet("background-color: #2ecc71; color: white;")
            use_btn.clicked.connect(lambda checked, t=template: self.use_template(t))
            actions_layout.addWidget(use_btn)
            
            # Preview button
            preview_btn = QPushButton("Preview")
            preview_btn.setStyleSheet("background-color: #3498db; color: white;")
            preview_btn.clicked.connect(lambda checked, t=template: self.preview_template(t['file_path']))
            actions_layout.addWidget(preview_btn)
            
            self.templates_table.setCellWidget(row, 3, actions_cell)
            
        # Resize columns for better view
        self.templates_table.resizeColumnsToContents()
        
    def preview_template(self, template_path):
        """Preview an Excel template"""
        try:
            import subprocess
            if sys.platform == 'win32':
                os.startfile(template_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', template_path])
            else:  # Linux
                subprocess.run(['xdg-open', template_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open template: {str(e)}")
            
    def use_template(self, template):
        """Use the selected template to create a new report"""
        # Create an Excel report form based on template
        template_path = template['file_path']
        self.report_form = ExcelReportForm(template_path, self.user['id'])
        self.report_form.report_submitted.connect(self.on_report_submitted)
        self.report_form_container.setWidget(self.report_form)
    
    def setup_reports_tab(self):
        """Set up the reports tab for viewing user reports"""
        layout = QVBoxLayout(self.reports_tab)
        
        # Create filter controls
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Reports", "all")
        self.status_filter.addItem("Draft", "draft")
        self.status_filter.addItem("Submitted", "submitted")
        self.status_filter.addItem("Approved by Unit Leader", "approved_leader")
        self.status_filter.addItem("Approved Final", "approved_admin")
        self.status_filter.addItem("Needs Revision", "needs_revision")
        self.status_filter.currentIndexChanged.connect(self.refresh_reports_table)
        filter_layout.addWidget(self.status_filter)
        
        search_label = QLabel("Search:")
        filter_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in report titles...")
        self.search_input.textChanged.connect(self.refresh_reports_table)
        filter_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)
        
        layout.addWidget(filter_frame)
        
        # Create reports table
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(5)
        self.reports_table.setHorizontalHeaderLabels(["ID", "Title", "Created", "Status", "Actions"])
        self.reports_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.reports_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.reports_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.reports_table)
        
    def refresh_data(self):
        """Refresh all data on the dashboard"""
        self.refresh_templates()
        self.refresh_reports_table()
        self.refresh_dashboard_stats()
        
    def refresh_reports_table(self):
        """Refresh the reports table"""
        # Get filter values
        status_filter = self.status_filter.currentData()
        search_text = self.search_input.text().lower()
        
        # Get user reports
        reports = get_user_reports(self.user['id'])
        
        # Clear the table
        self.reports_table.setRowCount(0)
        row = 0
        
        for report in reports:
            # Apply filters
            if status_filter != "all" and report['status'] != status_filter:
                continue
                
            if search_text and search_text not in report['title'].lower():
                continue
            
            self.reports_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(report['report_id']))
            self.reports_table.setItem(row, 0, id_item)
            
            # Title
            title_item = QTableWidgetItem(report['title'])
            self.reports_table.setItem(row, 1, title_item)
            
            # Created date
            created_item = QTableWidgetItem(report['created_at'])
            self.reports_table.setItem(row, 2, created_item)
            
            # Status with color coding
            status_text = self.get_status_display_text(report['status'])
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(self.get_status_color(report['status']))
            self.reports_table.setItem(row, 3, status_item)
            
            # Actions
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # View button
            view_btn = QPushButton("View")
            view_btn.setStyleSheet("background-color: #3498db; color: white;")
            view_btn.clicked.connect(lambda checked, r=report['report_id']: self.view_report(r))
            actions_layout.addWidget(view_btn)
            
            # Edit button - only for drafts, submitted, or reports needing revision
            if report['status'] in ['draft', 'submitted', 'needs_revision']:
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("background-color: #f39c12; color: white;")
                edit_btn.clicked.connect(lambda checked, r=report['report_id']: self.edit_report(r))
                actions_layout.addWidget(edit_btn)
            
            # Submit button - allow multiple submissions until approved
            if report['status'] in ['draft', 'submitted', 'needs_revision']:
                submit_btn = QPushButton("Submit")
                submit_btn.setStyleSheet("background-color: #2ecc71; color: white;")
                submit_btn.clicked.connect(lambda checked, r=report['report_id']: self.submit_report(r))
                actions_layout.addWidget(submit_btn)
            
            self.reports_table.setCellWidget(row, 4, actions_cell)
            
            row += 1
        
        # Also update the recent reports table on dashboard
        self.update_recent_reports_table(reports[:5])
    
    def refresh_dashboard_stats(self):
        """Refresh the dashboard statistics"""
        reports = get_user_reports(self.user['id'])
        
        # Count reports by status
        draft_count = sum(1 for r in reports if r['status'] == 'draft')
        submitted_count = sum(1 for r in reports if r['status'] in ['submitted', 'approved_leader'])
        approved_count = sum(1 for r in reports if r['status'] == 'approved_admin')
        rejected_count = sum(1 for r in reports if r['status'] == 'needs_revision')
        
        # Update labels
        self.draft_count_label.setText(f"Draft: {draft_count}")
        self.submitted_count_label.setText(f"Submitted: {submitted_count}")
        self.approved_count_label.setText(f"Approved: {approved_count}")
        self.rejected_count_label.setText(f"Needs Revision: {rejected_count}")
    
    def update_recent_reports_table(self, reports):
        """Update the recent reports table on the dashboard"""
        self.recent_reports_table.setRowCount(0)
        
        for row, report in enumerate(reports):
            self.recent_reports_table.insertRow(row)
            
            # Title
            title_item = QTableWidgetItem(report['title'])
            self.recent_reports_table.setItem(row, 0, title_item)
            
            # Created date
            created_item = QTableWidgetItem(report['created_at'])
            self.recent_reports_table.setItem(row, 1, created_item)
            
            # Status with color coding
            status_text = self.get_status_display_text(report['status'])
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(self.get_status_color(report['status']))
            self.recent_reports_table.setItem(row, 2, status_item)
            
            # Quick actions
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # View button
            view_btn = QPushButton("View")
            view_btn.setStyleSheet("background-color: #3498db; color: white;")
            view_btn.clicked.connect(lambda checked, r=report['report_id']: self.view_report(r))
            actions_layout.addWidget(view_btn)
            
            self.recent_reports_table.setCellWidget(row, 3, actions_cell)
    
    def get_status_display_text(self, status):
        """Convert status code to display text"""
        status_map = {
            'draft': 'Draft',
            'submitted': 'Submitted',
            'approved_leader': 'Approved by Unit Leader',
            'approved_admin': 'Approved (Final)',
            'needs_revision': 'Needs Revision'
        }
        return status_map.get(status, status.capitalize())
    
    def get_status_color(self, status):
        """Get color for status"""
        status_colors = {
            'draft': QColor(128, 128, 128),  # Grey
            'submitted': QColor(52, 152, 219),  # Blue
            'approved_leader': QColor(241, 196, 15),  # Yellow
            'approved_admin': QColor(46, 204, 113),  # Green
            'needs_revision': QColor(231, 76, 60)  # Red
        }
        return status_colors.get(status, QColor(0, 0, 0))
    
    def view_report(self, report_id):
        """View a report"""
        report = get_report(report_id)
        if not report:
            QMessageBox.warning(self, "Error", "Report not found.")
            return
            
        # Check if this is an Excel-based report
        excel_path = report.get('fields', {}).get('excel_file_path')
        # Gather all submission logs as digital signatures
        submit_logs = [log for log in report.get('approval_logs', []) if log['action']=='submit']
        if submit_logs:
            signature_text = "\n".join([
                f"Prepared By: {log['actor_name']} ({log['timestamp']})" for log in submit_logs
            ])
        else:
            signature_text = "Not signed"
            
        # Create a more detailed view dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Report Details - {report['title']}")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        
        # Report metadata
        info_group = QGroupBox("Report Information")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Report ID:", QLabel(str(report_id)))
        info_layout.addRow("Title:", QLabel(report['title']))
        info_layout.addRow("Status:", QLabel(self.get_status_display_text(report['status'])))
        info_layout.addRow("Created by:", QLabel(report['creator_name']))
        info_layout.addRow("Created on:", QLabel(str(report['created_at'])))
        
        # Show all user submission signatures, wrap text for multiline
        sig_label = QLabel(signature_text)
        sig_label.setWordWrap(True)
        info_layout.addRow("Digital Signatures:", sig_label)
        
        layout.addWidget(info_group)
        
        # File controls
        # Restrict access if report is approved by unit leader
        if report.get('status') == 'approved_leader':
            restricted_label = QLabel("Access to the Excel file is restricted after approval by the Unit Leader.")
            restricted_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(restricted_label)
        elif excel_path and os.path.exists(excel_path):
            file_group = QGroupBox("Excel Report File")
            file_layout = QVBoxLayout(file_group)
            
            file_label = QLabel(f"File: {os.path.basename(excel_path)}")
            file_layout.addWidget(file_label)
            
            open_btn = QPushButton("Open Excel File")
            open_btn.setStyleSheet("background-color: #3498db; color: white;")
            open_btn.clicked.connect(lambda: self._open_file(excel_path))
            file_layout.addWidget(open_btn)
            
            layout.addWidget(file_group)
        else:
            no_file_label = QLabel("No Excel file is available for this report.")
            layout.addWidget(no_file_label)
        
        # Approval history
        if 'approval_logs' in report and report['approval_logs']:
            history_group = QGroupBox("Approval History")
            history_layout = QVBoxLayout(history_group)
            
            for log in report['approval_logs']:
                # Map actions to user-friendly labels
                role_map = {'submit': 'Submitted By', 'approve_leader': 'Verified By', 'approve_admin': 'Approved By'}
                action_label = role_map.get(log['action'], log['action'].capitalize())
                text = f"{log['timestamp']} - {action_label}: {log['actor_name']}"
                if log.get('comments'):
                    text += f"\n{log['comments']}"
                entry = QLabel(text)
                entry.setWordWrap(True)
                history_layout.addWidget(entry)
                
            layout.addWidget(history_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
        
    def _open_file(self, file_path):
        """Helper method to open a file in the default application"""
        try:
            import subprocess
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
    
    def edit_report(self, report_id):
        """Edit a report"""
        report = get_report(report_id)
        if not report:
            QMessageBox.warning(self, "Error", "Report not found.")
            return
            
        # We can only edit reports that are in draft, submitted, or sent back for revision
        if report['status'] not in ['draft', 'submitted', 'needs_revision']:
            QMessageBox.warning(self, "Cannot Edit", 
                               f"This report is in '{self.get_status_display_text(report['status'])}' status and cannot be edited.")
            return
            
        # Check if this is an Excel-based report
        excel_path = None
        if 'fields' in report and 'excel_file_path' in report['fields']:
            excel_path = report['fields']['excel_file_path']
            
        if excel_path and os.path.exists(excel_path):
            # Open the Excel file for editing
            import subprocess
            try:
                if sys.platform == 'win32':
                    os.startfile(excel_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', excel_path])
                else:  # Linux
                    subprocess.run(['xdg-open', excel_path])
                    
                QMessageBox.information(self, "Edit Report", 
                                      "The Excel file has been opened for editing. "
                                      "After making changes and saving the file, you can submit the report for review.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open Excel file: {str(e)}")
        else:
            # Get the active template and create a new copy for this report
            from db.database import get_active_template
            active_template = get_active_template()
            
            if not active_template:
                QMessageBox.warning(self, "No Template", "No active template found. Please contact an administrator.")
                return
                
            # Create a directory for this user's reports if it doesn't exist
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user_reports', str(self.user['id']))
            os.makedirs(reports_dir, exist_ok=True)
            
            # Create a file name based on the report ID and original template name
            file_name = f"report_{report_id}_{os.path.basename(active_template['file_path'])}"
            file_path = os.path.join(reports_dir, file_name)
            
            # Copy the template to the user's directory
            import shutil
            try:
                shutil.copy2(active_template['file_path'], file_path)
                
                # Update the report with the new file path
                add_report_data(report_id, "excel_file_path", file_path)
                
                # Open the new file
                import subprocess
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', file_path])
                    
                QMessageBox.information(self, "New Excel File Created", 
                                      "A new Excel file has been created from the active template. "
                                      "Fill in your data and save the file, then you can submit the report for review.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to copy or open file: {str(e)}")
    
    def on_report_submitted(self, report_id):
        """Handle signal when a new report is submitted from the form"""
        self.refresh_data()
        self.tab_widget.setCurrentIndex(2)  # Switch to My Reports tab

    def submit_report(self, report_id):
        """Submit a report for review"""
        report = get_report(report_id)
        if not report:
            QMessageBox.warning(self, "Error", "Report not found.")
            return
            
        main_window = QApplication.instance().activeWindow()
        user = None
        if hasattr(main_window, 'current_user'):
            from db.database import get_user_by_id
            user = get_user_by_id(main_window.current_user['id'])
        if not user or not user.get('emp_code') or not user.get('designation'):
            QMessageBox.warning(self, "Missing Signature Information", 
                               "Your profile is missing employee code or designation required for digital signature. "
                               "Please contact an administrator to update your profile.")
            return
        
        # Generate digital signature
        signature = f"{user['emp_code']} - {user['designation']}"
        
        reply = QMessageBox.question(self, 'Confirm Submission', 
                                    f"Are you sure you want to submit this report for review?\nIt will be digitally signed as: {signature}",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Removed single user_signature field; using approval_logs to gather all signatures
            # Update report status
            update_report_status(report_id, 'submitted', user['id'])
            
            # Add approval log with signature information
            add_approval_log(report_id, user['id'], 'submit', f"Submission with digital signature: {signature}")
            
            QMessageBox.information(self, "Success", "Report submitted successfully for review.")
            self.refresh_data() 