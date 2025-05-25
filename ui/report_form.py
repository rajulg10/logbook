import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFormLayout,
                           QDateEdit, QSpinBox, QTextEdit, QGroupBox,
                           QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.excel_handler import ExcelHandler
from db.database import create_report, add_report_data, update_report_status, add_approval_log

class ReportForm(QWidget):
    report_submitted = pyqtSignal(int)  # Signal to emit report_id when submitted
    
    def __init__(self, template_path, user_id):
        super().__init__()
        self.template_path = template_path
        self.user_id = user_id
        self.fields = []
        self.field_widgets = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI with dynamic form fields from template"""
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
        
        # Extract fields from template
        self.fields = ExcelHandler.get_template_fields(self.template_path)
        
        if not self.fields:
            error_label = QLabel("No fields found in the template or template is invalid.")
            error_label.setStyleSheet("color: red;")
            main_layout.addWidget(error_label)
        else:
            # Create form fields grouped by sections
            self.create_form_fields(main_layout)
        
        # Add buttons at the bottom
        buttons_layout = QHBoxLayout()
        
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
        buttons_layout.addWidget(save_draft_btn)
        
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
        buttons_layout.addWidget(submit_btn)
        
        clear_btn = QPushButton("Clear Form")
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
        buttons_layout.addWidget(clear_btn)
        
        main_layout.addLayout(buttons_layout)
        
    def create_form_fields(self, main_layout):
        """Create form fields based on template fields"""
        # Group fields into sections based on naming patterns
        sections = self.group_fields_into_sections()
        
        for section_name, section_fields in sections.items():
            # Create a group box for each section
            section_group = QGroupBox(section_name)
            section_layout = QFormLayout(section_group)
            
            for field in section_fields:
                # Create appropriate widget based on field type
                widget = self.create_field_widget(field)
                
                if widget:
                    # Store the widget for later access
                    self.field_widgets[field['name']] = widget
                    
                    # Add to form layout
                    section_layout.addRow(f"{field['name']}:", widget)
            
            main_layout.addWidget(section_group)
    
    def group_fields_into_sections(self):
        """Group fields into logical sections based on naming patterns"""
        sections = {"General Information": []}
        
        for field in self.fields:
            field_name = field['name'].lower()
            
            # Try to determine which section this field belongs to
            if "product" in field_name or "planned" in field_name or "actual" in field_name:
                section_name = "Production Data"
            elif "issue" in field_name:
                section_name = "Issues and Challenges"
            elif "note" in field_name:
                section_name = "Notes"
            else:
                section_name = "General Information"
            
            # Create section if it doesn't exist
            if section_name not in sections:
                sections[section_name] = []
            
            # Add field to section
            sections[section_name].append(field)
        
        # Remove empty sections
        return {k: v for k, v in sections.items() if v}
    
    def create_field_widget(self, field):
        """Create appropriate widget based on field type"""
        field_type = field.get('type', 'text')
        
        if field_type == 'date':
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDate(QDate.currentDate())
            return widget
        
        elif field_type == 'number':
            widget = QSpinBox()
            widget.setRange(0, 999999)
            return widget
        
        elif "notes" in field['name'].lower() or len(field['name']) > 30:
            # Use text edit for notes or long field names (likely multi-line)
            widget = QTextEdit()
            widget.setMaximumHeight(100)
            return widget
        
        else:
            # Default to line edit
            widget = QLineEdit()
            return widget
    
    def collect_form_data(self):
        """Collect data from all form fields"""
        data = {}
        
        for field_name, widget in self.field_widgets.items():
            # Get value based on widget type
            if isinstance(widget, QDateEdit):
                value = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QSpinBox):
                value = str(widget.value())
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                value = widget.text()
            else:
                value = ""
            
            data[field_name] = value
        
        return data
    
    def save_as_draft(self):
        """Save the report as a draft"""
        title = self.report_title.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter a title for this report.")
            self.report_title.setFocus()
            return
        
        # Collect form data
        data = self.collect_form_data()
        
        # Create report
        report_id = create_report(self.user_id, title)
        
        # Save form data
        for field_name, value in data.items():
            add_report_data(report_id, field_name, value)
        
        QMessageBox.information(self, "Success", "Report saved as draft successfully.")
        
        # Emit signal with report ID
        self.report_submitted.emit(report_id)
    
    def submit_report(self):
        """Submit the report for review"""
        title = self.report_title.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter a title for this report.")
            self.report_title.setFocus()
            return
        
        # Collect form data
        data = self.collect_form_data()
        
        # Check if required fields are filled
        required_fields = [f['name'] for f in self.fields if 'date' in f['name'].lower() or 'supervisor' in f['name'].lower()]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            QMessageBox.warning(self, "Missing Information", 
                              f"Please fill in all required fields: {', '.join(missing_fields)}")
            return
        
        # Create report
        report_id = create_report(self.user_id, title)
        
        # Save form data
        for field_name, value in data.items():
            add_report_data(report_id, field_name, value)
        
        # Update status to submitted
        update_report_status(report_id, 'submitted', self.user_id)
        
        # Add approval log
        add_approval_log(report_id, self.user_id, 'submit', "Initial submission")
        
        QMessageBox.information(self, "Success", "Report submitted successfully for review.")
        
        # Clear the form after submission
        self.clear_form()
        
        # Emit signal with report ID
        self.report_submitted.emit(report_id)
    
    def clear_form(self):
        """Clear all form fields"""
        self.report_title.clear()
        
        for widget in self.field_widgets.values():
            if isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())
            elif isinstance(widget, QSpinBox):
                widget.setValue(0)
            elif isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QLineEdit):
                widget.clear() 