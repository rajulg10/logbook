import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem, 
                           QTabWidget, QMessageBox, QHeaderView, QFrame,
                           QSplitter, QComboBox, QLineEdit, QFormLayout,
                           QScrollArea, QGroupBox, QSpacerItem, QSizePolicy,
                           QTextEdit, QDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.database import (get_reports_by_status, get_report, 
                       update_report_status, add_approval_log)
from email_sender import EmailSender

class CommentDialog(QDialog):
    """Dialog for entering comments when sending back a report"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Comments")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add instruction label
        instruction = QLabel("Please provide comments explaining what needs to be revised:")
        layout.addWidget(instruction)
        
        # Add text edit for comments
        self.comments_edit = QTextEdit()
        layout.addWidget(self.comments_edit)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setDefault(True)
        self.submit_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.submit_btn)
        
        layout.addLayout(button_layout)
    
    def get_comments(self):
        """Get the entered comments"""
        return self.comments_edit.toPlainText()

class ReportDetailDialog(QDialog):
    """Dialog for viewing detailed report information"""
    def __init__(self, report, parent=None):
        super().__init__(parent)
        self.report = report
        self.setWindowTitle(f"Report #{report['report_id']}: {report['title']}")
        self.setMinimumSize(700, 500)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add report metadata
        meta_group = QGroupBox("Report Information")
        meta_layout = QFormLayout(meta_group)
        
        meta_layout.addRow("Report ID:", QLabel(str(self.report['report_id'])))
        meta_layout.addRow("Title:", QLabel(self.report['title']))
        meta_layout.addRow("Created by:", QLabel(self.report['creator_name']))
        meta_layout.addRow("Created on:", QLabel(str(self.report['created_at'])))
        meta_layout.addRow("Status:", QLabel(self.report['status']))
        meta_layout.addRow("Version:", QLabel(str(self.report['version'])))
        
        layout.addWidget(meta_group)
        
        # Add report fields in scrollable area
        fields_group = QGroupBox("Report Content")
        fields_layout = QVBoxLayout(fields_group)
        
        fields_scroll = QScrollArea()
        fields_scroll.setWidgetResizable(True)
        fields_container = QWidget()
        fields_form = QFormLayout(fields_container)
        
        # Group fields by category
        field_categories = self.group_fields_by_category()
        
        for category, fields in field_categories.items():
            # Add category label
            category_label = QLabel(category)
            category_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
            fields_form.addRow(category_label)
            
            # Add fields
            for field_name, field_value in fields:
                value_label = QLabel(field_value)
                value_label.setWordWrap(True)
                fields_form.addRow(f"{field_name}:", value_label)
            
            # Add spacer
            spacer_label = QLabel()
            spacer_label.setMinimumHeight(10)
            fields_form.addRow(spacer_label)
        
        fields_scroll.setWidget(fields_container)
        fields_layout.addWidget(fields_scroll)
        
        layout.addWidget(fields_group)
        
        # Add approval history
        if 'approval_logs' in self.report and self.report['approval_logs']:
            history_group = QGroupBox("Approval History")
            history_layout = QVBoxLayout(history_group)
            
            history_table = QTableWidget()
            history_table.setColumnCount(4)
            history_table.setHorizontalHeaderLabels(["Date", "User", "Action", "Comments"])
            history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            
            # Add rows for each log entry
            for row, log in enumerate(self.report['approval_logs']):
                history_table.insertRow(row)
                history_table.setItem(row, 0, QTableWidgetItem(str(log['timestamp'])))
                history_table.setItem(row, 1, QTableWidgetItem(log['actor_name']))
                history_table.setItem(row, 2, QTableWidgetItem(log['action']))
                history_table.setItem(row, 3, QTableWidgetItem(log['comments'] or ""))
            
            history_layout.addWidget(history_table)
            layout.addWidget(history_group)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
    
    def group_fields_by_category(self):
        """Group report fields by category for display"""
        categories = {}
        
        for field_name, field_value in self.report['fields'].items():
            # Determine category based on field name
            field_name_lower = field_name.lower()
            
            if "product" in field_name_lower or "planned" in field_name_lower or "actual" in field_name_lower:
                category = "Production Data"
            elif "issue" in field_name_lower:
                category = "Issues and Challenges"
            elif "note" in field_name_lower:
                category = "Notes"
            else:
                category = "General Information"
            
            # Create category if it doesn't exist
            if category not in categories:
                categories[category] = []
            
            # Add field to category
            categories[category].append((field_name, field_value))
        
        return categories

class UnitLeaderDashboard(QWidget):
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
        
        # Add Pending Reviews tab
        self.pending_tab = QWidget()
        self.tab_widget.addTab(self.pending_tab, "Pending Reviews")
        self.setup_pending_tab()
        
        # Add All Reports tab
        self.reports_tab = QWidget()
        self.tab_widget.addTab(self.reports_tab, "All Reports")
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
        
        instructions = QLabel("As a Unit Leader, you are responsible for reviewing reports submitted by users.")
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
        self.pending_count_label = QLabel("Pending Reviews: 0")
        self.pending_count_label.setStyleSheet("font-size: 16px; color: #e74c3c;")
        stats_layout.addWidget(self.pending_count_label)
        
        self.approved_count_label = QLabel("Approved: 0")
        self.approved_count_label.setStyleSheet("font-size: 16px; color: #2ecc71;")
        stats_layout.addWidget(self.approved_count_label)
        
        layout.addWidget(stats_frame)
        
        # Quick actions
        actions_label = QLabel("Quick Actions")
        actions_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(actions_label)
        
        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        
        review_reports_btn = QPushButton("Review Pending Reports")
        review_reports_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        review_reports_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        actions_layout.addWidget(review_reports_btn)
        
        view_all_reports_btn = QPushButton("View All Reports")
        view_all_reports_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        view_all_reports_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        actions_layout.addWidget(view_all_reports_btn)
        
        layout.addWidget(actions_frame)
        
        # Recent pending reports
        pending_label = QLabel("Pending Reviews")
        pending_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 15px;")
        layout.addWidget(pending_label)
        
        self.pending_reports_table = QTableWidget()
        self.pending_reports_table.setColumnCount(5)
        self.pending_reports_table.setHorizontalHeaderLabels(["ID", "Title", "Created by", "Submitted on", "Actions"])
        self.pending_reports_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.pending_reports_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pending_reports_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.pending_reports_table)
        
        # Add spacer at the bottom
        layout.addStretch()
        
    def setup_pending_tab(self):
        """Set up the pending reviews tab"""
        layout = QVBoxLayout(self.pending_tab)
        
        # Add instructions
        instructions = QLabel("Review and approve or send back reports submitted by users.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Create pending reports table
        self.detailed_pending_table = QTableWidget()
        self.detailed_pending_table.setColumnCount(6)
        self.detailed_pending_table.setHorizontalHeaderLabels(["ID", "Title", "Created by", "Submitted on", "Version", "Actions"])
        self.detailed_pending_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.detailed_pending_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detailed_pending_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.detailed_pending_table)
        
        # Add refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)
        
    def setup_reports_tab(self):
        """Set up the all reports tab"""
        layout = QVBoxLayout(self.reports_tab)
        
        # Create filter controls
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Reports", "all")
        self.status_filter.addItem("Submitted", "submitted")
        self.status_filter.addItem("Approved by Me", "approved_leader")
        self.status_filter.addItem("Approved Final", "approved_admin")
        self.status_filter.addItem("Needs Revision", "needs_revision")
        self.status_filter.currentIndexChanged.connect(self.refresh_all_reports_table)
        filter_layout.addWidget(self.status_filter)
        
        search_label = QLabel("Search:")
        filter_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in report titles...")
        self.search_input.textChanged.connect(self.refresh_all_reports_table)
        filter_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)
        
        layout.addWidget(filter_frame)
        
        # Create reports table
        self.all_reports_table = QTableWidget()
        self.all_reports_table.setColumnCount(6)
        self.all_reports_table.setHorizontalHeaderLabels(["ID", "Title", "Created by", "Submitted on", "Status", "Actions"])
        self.all_reports_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.all_reports_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.all_reports_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.all_reports_table)
        
    def refresh_data(self):
        """Refresh all data on the dashboard"""
        self.refresh_pending_tables()
        self.refresh_dashboard_stats()
        self.refresh_all_reports_table()
        
    def refresh_pending_tables(self):
        """Refresh the pending reports tables"""
        # Get pending reports (submitted and those sent back for revision)
        pending_reports = get_reports_by_status('submitted')
        # Include reports sent back by admin for revision
        pending_reports.extend(get_reports_by_status('needs_revision'))
        
        # Update dashboard pending table
        self.pending_reports_table.setRowCount(0)
        
        # Update detailed pending table
        self.detailed_pending_table.setRowCount(0)
        
        for row, report in enumerate(pending_reports):
            # Add to both tables
            self.pending_reports_table.insertRow(row)
            self.detailed_pending_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(report['report_id']))
            self.pending_reports_table.setItem(row, 0, id_item)
            self.detailed_pending_table.setItem(row, 0, QTableWidgetItem(str(report['report_id'])))
            
            # Title
            title_item = QTableWidgetItem(report['title'])
            self.pending_reports_table.setItem(row, 1, title_item)
            self.detailed_pending_table.setItem(row, 1, QTableWidgetItem(report['title']))
            
            # Created by
            creator_item = QTableWidgetItem(report['creator_name'])
            self.pending_reports_table.setItem(row, 2, creator_item)
            self.detailed_pending_table.setItem(row, 2, QTableWidgetItem(report['creator_name']))
            
            # Submitted on
            created_item = QTableWidgetItem(report['created_at'])
            self.pending_reports_table.setItem(row, 3, created_item)
            self.detailed_pending_table.setItem(row, 3, QTableWidgetItem(report['created_at']))
            
            # Version (detailed table only)
            self.detailed_pending_table.setItem(row, 4, QTableWidgetItem(str(report['version'])))
            
            # Actions
            for table_idx, table in enumerate([self.pending_reports_table, self.detailed_pending_table]):
                actions_cell = QWidget()
                actions_layout = QHBoxLayout(actions_cell)
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                # View button
                view_btn = QPushButton("View")
                view_btn.setStyleSheet("background-color: #3498db; color: white;")
                view_btn.clicked.connect(lambda checked, r=report['report_id']: self.view_report(r))
                actions_layout.addWidget(view_btn)
                
                # Approve button
                approve_btn = QPushButton("Approve")
                approve_btn.setStyleSheet("background-color: #2ecc71; color: white;")
                approve_btn.clicked.connect(lambda checked, r=report['report_id']: self.approve_report(r))
                actions_layout.addWidget(approve_btn)
                
                # Send Back button
                reject_btn = QPushButton("Send Back")
                reject_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                reject_btn.clicked.connect(lambda checked, r=report['report_id']: self.send_back_report(r))
                actions_layout.addWidget(reject_btn)
                
                if table_idx == 0:  # Dashboard table
                    table.setCellWidget(row, 4, actions_cell)
                else:  # Detailed table
                    table.setCellWidget(row, 5, actions_cell)
    
    def refresh_dashboard_stats(self):
        """Refresh the dashboard statistics"""
        # Get counts for different statuses
        pending_reports = get_reports_by_status('submitted')
        approved_reports = get_reports_by_status('approved_leader')
        
        # Update labels
        self.pending_count_label.setText(f"Pending Reviews: {len(pending_reports)}")
        self.approved_count_label.setText(f"Approved: {len(approved_reports)}")
    
    def refresh_all_reports_table(self):
        """Refresh the all reports table"""
        # Get filter values
        status_filter = self.status_filter.currentData()
        search_text = self.search_input.text().lower()
        
        # Get reports based on filter
        if status_filter == 'all':
            # Get all reports except drafts
            statuses = ['submitted', 'approved_leader', 'approved_admin', 'needs_revision']
            reports = []
            for status in statuses:
                reports.extend(get_reports_by_status(status))
        else:
            reports = get_reports_by_status(status_filter)
        
        # Clear the table
        self.all_reports_table.setRowCount(0)
        row = 0
        
        for report in reports:
            # Apply search filter
            if search_text and search_text not in report['title'].lower():
                continue
            
            self.all_reports_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(str(report['report_id']))
            self.all_reports_table.setItem(row, 0, id_item)
            
            # Title
            title_item = QTableWidgetItem(report['title'])
            self.all_reports_table.setItem(row, 1, title_item)
            
            # Created by
            creator_item = QTableWidgetItem(report['creator_name'])
            self.all_reports_table.setItem(row, 2, creator_item)
            
            # Submitted on
            created_item = QTableWidgetItem(report['created_at'])
            self.all_reports_table.setItem(row, 3, created_item)
            
            # Status with color coding
            status_text = self.get_status_display_text(report['status'])
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(self.get_status_color(report['status']))
            self.all_reports_table.setItem(row, 4, status_item)
            
            # Actions
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # View button
            view_btn = QPushButton("View")
            view_btn.setStyleSheet("background-color: #3498db; color: white;")
            view_btn.clicked.connect(lambda checked, r=report['report_id']: self.view_report(r))
            actions_layout.addWidget(view_btn)
            
            # Add approve/reject buttons only for submitted reports
            if report['status'] == 'submitted':
                # Approve button
                approve_btn = QPushButton("Approve")
                approve_btn.setStyleSheet("background-color: #2ecc71; color: white;")
                approve_btn.clicked.connect(lambda checked, r=report['report_id']: self.approve_report(r))
                actions_layout.addWidget(approve_btn)
                
                # Send Back button
                reject_btn = QPushButton("Send Back")
                reject_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                reject_btn.clicked.connect(lambda checked, r=report['report_id']: self.send_back_report(r))
                actions_layout.addWidget(reject_btn)
            
            self.all_reports_table.setCellWidget(row, 5, actions_cell)
            
            row += 1
    
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
        """View a report's details"""
        report = get_report(report_id)
        if not report:
            QMessageBox.warning(self, "Error", "Report not found.")
            return
            
        # Check if this is an Excel-based report
        excel_path = None
        if 'fields' in report and 'excel_file_path' in report['fields']:
            excel_path = report['fields']['excel_file_path']
            
        if excel_path and os.path.exists(excel_path):
            # Open the Excel file
            import subprocess
            if sys.platform == 'win32':
                os.startfile(excel_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', excel_path])
            else:  # Linux
                subprocess.run(['xdg-open', excel_path])
                
            # Also show the report detail dialog for approval history
            dialog = ReportDetailDialog(report, self)
            dialog.exec_()
        else:
            # Just show the report detail dialog
            dialog = ReportDetailDialog(report, self)
            dialog.exec_()
    
    def approve_report(self, report_id):
        """Approve a report and forward to admin"""
        reply = QMessageBox.question(self, 'Confirm Approval', 
                                    "Are you sure you want to approve this report and forward to the Section Head?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Update report status
            update_report_status(report_id, 'approved_leader', self.user['id'])
            
            # Add approval log
            add_approval_log(report_id, self.user['id'], 'approve_leader', "Approved by Unit Leader")
            
            # Get report for notifications
            report = get_report(report_id)
            excel_path = None
            if report:
                # Try to get Excel file path from report fields or directly
                excel_path = report.get('excel_file_path')
                if not excel_path:
                    fields = report.get('fields', {})
                    excel_path = fields.get('excel_file_path')
                if excel_path and not os.path.exists(excel_path):
                    excel_path = None  # Only attach if file exists
            # Send email notification to admin with Excel attachment and action links
            admin_users = [user for user in self.get_admin_users()]
            if admin_users and report:
                for admin in admin_users:
                    self.email_sender.send_notification_to_admin(
                        report_id, 
                        report['title'],
                        report['user_id'],
                        self.user['id'],
                        admin['id'],
                        excel_path=excel_path
                    )
            QMessageBox.information(self, "Success", "Report approved and forwarded to Section Head.")
            self.refresh_data()
    
    def send_back_report(self, report_id):
        """Send a report back for revision"""
        # Show dialog to get comments
        dialog = CommentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            comments = dialog.get_comments()
            
            if not comments:
                QMessageBox.warning(self, "Missing Comments", 
                                   "Please provide comments explaining what needs to be revised.")
                return
            
            # Update report status
            update_report_status(report_id, 'needs_revision', self.user['id'])
            
            # Add approval log
            add_approval_log(report_id, self.user['id'], 'send_back', comments)
            
            # Get report for notifications
            report = get_report(report_id)
            
            # Send email notification to user
            if report:
                self.email_sender.send_rejection_notification(
                    report_id,
                    report['title'],
                    report['user_id'],
                    self.user['id'],
                    comments
                )
            
            QMessageBox.information(self, "Success", "Report has been sent back for revision.")
            self.refresh_data()
    
    def get_admin_users(self):
        """Get all admin users for notifications"""
        # This would normally come from the database
        # For now, just return a simulated list
        from db.database import get_user_by_id
        admin_users = []
        # Try to get admin with ID 1 (default admin)
        admin = get_user_by_id(1)
        if admin and admin['role'] == 'admin':
            admin_users.append(admin)
        return admin_users 