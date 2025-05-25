import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFormLayout,
                           QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.auth import Auth

class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Create logo/title section
        title_label = QLabel("Report Management System")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Add subtitle
        subtitle_label = QLabel("Excel-Based Reports with Approval Workflow")
        subtitle_label.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # Add some spacing
        main_layout.addSpacing(30)
        
        # Create login group box
        login_group = QGroupBox("Login")
        login_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        login_layout = QFormLayout(login_group)
        login_layout.setContentsMargins(20, 30, 20, 20)
        login_layout.setSpacing(15)
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        login_layout.addRow("Username:", self.username_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        login_layout.addRow("Password:", self.password_input)
        
        # Add login button
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        self.login_button.clicked.connect(self.login)
        login_layout.addRow("", self.login_button)
        
        # Add login group to main layout
        main_layout.addWidget(login_group)
        
        # Add an info label about default credentials
        info_label = QLabel("Default Admin: username 'admin', password 'admin123'")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)
        
        # Make the login form fixed width but centered
        login_group.setFixedWidth(400)
        main_layout.setAlignment(login_group, Qt.AlignCenter)
        
        # Set tab order
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.login_button)
        
        # Connect enter key in password field to login
        self.password_input.returnPressed.connect(self.login)
        
    def login(self):
        """Attempt to login with provided credentials"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        # Authenticate user
        user = Auth.login(username, password)
        
        if user:
            self.login_success.emit(user)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def reset(self):
        """Reset the login form"""
        self.username_input.clear()
        self.password_input.clear()
        self.username_input.setFocus()