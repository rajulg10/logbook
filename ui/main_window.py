import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QStackedWidget, QLabel, QPushButton, QAction, 
                            QMessageBox, QStatusBar)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from ui.login_window import LoginWindow
from ui.user_dashboard import UserDashboard
from ui.unit_leader_dashboard import UnitLeaderDashboard
from ui.admin_dashboard import AdminDashboard
from utils.auth import Auth

class MainWindow(QMainWindow):
    logout_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Report Management System")
        self.setMinimumSize(1000, 700)
        
        # Create the central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create header
        self.create_header()
        
        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        # Create login screen
        self.login_window = LoginWindow()
        self.stacked_widget.addWidget(self.login_window)
        
        # Connect login signal
        self.login_window.login_success.connect(self.on_login_success)
        
        # Show login screen by default
        self.stacked_widget.setCurrentWidget(self.login_window)
        
        # Set up other screens (they will be created when needed)
        self.user_dashboard = None
        self.unit_leader_dashboard = None
        self.admin_dashboard = None
        
    def create_menu_bar(self):
        """Create the menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_header(self):
        """Create the header with user info and logout button"""
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        
        # App title label
        self.title_label = QLabel("Report Management System")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        # User info (will be updated on login)
        self.user_info_label = QLabel("")
        header_layout.addWidget(self.user_info_label, alignment=Qt.AlignRight)
        
        # Logout button (initially hidden)
        self.logout_button = QPushButton("Logout")
        self.logout_button.setFixedWidth(100)
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setVisible(False)
        header_layout.addWidget(self.logout_button)
        
        self.main_layout.addWidget(self.header_widget)
        
    def on_login_success(self, user):
        """Handle successful login"""
        self.current_user = user
        self.user_info_label.setText(f"Logged in as: {user['username']} ({user['role']})")
        self.logout_button.setVisible(True)
        
        # Show appropriate dashboard based on user role
        if Auth.is_admin(user):
            self.show_admin_dashboard()
        elif Auth.is_unit_leader(user):
            self.show_unit_leader_dashboard()
        else:
            self.show_user_dashboard()
    
    def show_admin_dashboard(self):
        """Show the admin dashboard"""
        if not self.admin_dashboard:
            self.admin_dashboard = AdminDashboard(self.current_user)
            self.stacked_widget.addWidget(self.admin_dashboard)
        else:
            self.admin_dashboard.refresh_data()
            
        self.stacked_widget.setCurrentWidget(self.admin_dashboard)
        self.statusBar.showMessage(f"Welcome, {self.current_user['username']}! You are logged in as an administrator.")
    
    def show_unit_leader_dashboard(self):
        """Show the unit leader dashboard"""
        if not self.unit_leader_dashboard:
            self.unit_leader_dashboard = UnitLeaderDashboard(self.current_user)
            self.stacked_widget.addWidget(self.unit_leader_dashboard)
        else:
            self.unit_leader_dashboard.refresh_data()
            
        self.stacked_widget.setCurrentWidget(self.unit_leader_dashboard)
        self.statusBar.showMessage(f"Welcome, {self.current_user['username']}! You are logged in as a unit leader.")
    
    def show_user_dashboard(self):
        """Show the user dashboard"""
        if not self.user_dashboard:
            self.user_dashboard = UserDashboard(self.current_user)
            self.stacked_widget.addWidget(self.user_dashboard)
        else:
            self.user_dashboard.refresh_data()
            
        self.stacked_widget.setCurrentWidget(self.user_dashboard)
        self.statusBar.showMessage(f"Welcome, {self.current_user['username']}! You are logged in as a user.")
    
    def logout(self):
        """Log out the current user"""
        self.current_user = None
        self.user_info_label.setText("")
        self.logout_button.setVisible(False)
        
        # Reset and show login screen
        self.login_window.reset()
        self.stacked_widget.setCurrentWidget(self.login_window)
        self.statusBar.showMessage("You have been logged out.")
        
        # Emit logout signal
        self.logout_signal.emit()
    
    def show_about(self):
        """Show the about dialog"""
        QMessageBox.about(self, "About Report Management System", 
                         "Report Management System\n\n"
                         "Version 1.0\n\n"
                         "A cross-platform desktop application for managing reports with "
                         "Excel-based templates and multi-level approval workflow.")
    
    def closeEvent(self, event):
        """Handle the close event"""
        reply = QMessageBox.question(self, 'Confirm Exit',
                                    "Are you sure you want to exit?",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore() 