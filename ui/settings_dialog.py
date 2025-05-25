import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from pathlib import Path
from dotenv import load_dotenv, set_key
from email_sender import EmailSender

class SettingsDialog(QDialog):
    """Dialog for Admin to set email notification and workflow preferences"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Settings")
        self.setMinimumWidth(400)
        # Load environment variables from .env
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(dotenv_path=str(env_path))
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # SMTP Server
        self.smtp_server_input = QLineEdit()
        layout.addWidget(QLabel("SMTP Server:"))
        layout.addWidget(self.smtp_server_input)

        # SMTP Port
        self.smtp_port_input = QLineEdit()
        layout.addWidget(QLabel("SMTP Port:"))
        layout.addWidget(self.smtp_port_input)

        # SMTP Username
        self.smtp_user_input = QLineEdit()
        layout.addWidget(QLabel("SMTP Username:"))
        layout.addWidget(self.smtp_user_input)

        # SMTP Password
        self.smtp_pass_input = QLineEdit()
        self.smtp_pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("SMTP Password:"))
        layout.addWidget(self.smtp_pass_input)

        # Enable/Disable Email Notifications
        self.enable_notifications_cb = QCheckBox("Enable Email Notifications")
        layout.addWidget(self.enable_notifications_cb)

        # Save Button
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        # Test Email button
        test_btn = QPushButton("Send Test Email")
        test_btn.clicked.connect(self.send_test_email)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)

    def load_settings(self):
        # Load settings from environment or config file
        self.smtp_server_input.setText(os.environ.get("SMTP_SERVER", ""))
        self.smtp_port_input.setText(os.environ.get("SMTP_PORT", ""))
        self.smtp_user_input.setText(os.environ.get("SMTP_USERNAME", ""))
        self.smtp_pass_input.setText(os.environ.get("SMTP_PASSWORD", ""))
        self.enable_notifications_cb.setChecked(os.environ.get("ENABLE_EMAIL_NOTIFICATIONS", "1") == "1")

    def save_settings(self):
        # Persist settings to .env file and runtime environment
        env_path = Path(__file__).resolve().parent.parent / ".env"
        # Ensure .env file exists
        env_path.touch(exist_ok=True)
        # Write settings
        set_key(str(env_path), "SMTP_SERVER", self.smtp_server_input.text())
        set_key(str(env_path), "SMTP_PORT", self.smtp_port_input.text())
        set_key(str(env_path), "SMTP_USERNAME", self.smtp_user_input.text())
        set_key(str(env_path), "SMTP_PASSWORD", self.smtp_pass_input.text())
        set_key(str(env_path), "ENABLE_EMAIL_NOTIFICATIONS", "1" if self.enable_notifications_cb.isChecked() else "0")
        # Update runtime environment
        os.environ["SMTP_SERVER"] = self.smtp_server_input.text()
        os.environ["SMTP_PORT"] = self.smtp_port_input.text()
        os.environ["SMTP_USERNAME"] = self.smtp_user_input.text()
        os.environ["SMTP_PASSWORD"] = self.smtp_pass_input.text()
        os.environ["ENABLE_EMAIL_NOTIFICATIONS"] = "1" if self.enable_notifications_cb.isChecked() else "0"
        QMessageBox.information(self, "Settings Saved", "Settings have been saved. Please restart the application for changes to take effect.")
        self.accept()

    def send_test_email(self):
        """Send a test email to verify SMTP settings"""
        recipient = self.smtp_user_input.text().strip()
        if not recipient:
            QMessageBox.warning(self, "Missing Recipient", "Please enter a recipient email (SMTP Username).")
            return
        sender = EmailSender()
        success, msg = sender.send_email(recipient,
                                         "Test Email from LogBook",
                                         "<p>This is a test email to verify SMTP settings.</p>")
        if success:
            QMessageBox.information(self, "Test Email Sent", msg)
        else:
            QMessageBox.warning(self, "Test Email Failed", msg)
