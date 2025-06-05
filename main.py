import sys
import os
import threading
import importlib.util
import logging
import traceback
import socket
import time
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QFile, QTextStream
from ui.main_window import MainWindow
from dotenv import load_dotenv

# Set up logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'logbook.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, 'w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Try to show error in a message box if possible
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        error_msg = f"""
        An unexpected error occurred:
        
        Type: {exc_type.__name__}
        Error: {str(exc_value)}
        
        Please check the log file for more details:
        {log_file.absolute()}
        """
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Unexpected Error")
        msg_box.setText("An unexpected error occurred.")
        msg_box.setDetailedText(traceback.format_exc())
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    except Exception as e:
        logger.error("Failed to show error dialog", exc_info=True)
    
    sys.exit(1)

# Set the exception handler
sys.excepthook = handle_exception

def initialize_application():
    """Initialize the application and handle startup errors"""
    logger.info("Starting application initialization")
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        from db.init_db import init_db, get_db_path
        
        # Get the database path for logging
        db_path = get_db_path()
        logger.info(f"Database path: {db_path}")
        
        # Check if we can create the database directory
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        # Test write permissions
        test_file = os.path.join(db_dir, '.permission_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            raise Exception(f"Cannot write to database directory: {db_dir}. Please check permissions.")
        
        # Initialize the database
        init_db()
        logger.info("Database initialized successfully")
        
    except ImportError as e:
        error_msg = f"Failed to import database module: {str(e)}\n\n{traceback.format_exc()}"
        logger.critical(error_msg)
        show_error_dialog(
            "Missing Dependencies",
            "Failed to load required database modules.\n\n"
            "Please make sure all dependencies are installed by running:\n"
            "pip install -r requirements.txt\n\n"
            f"Error: {str(e)}"
        )
        return False
        
    except Exception as e:
        error_msg = f"Failed to initialize database: {str(e)}\n\n{traceback.format_exc()}"
        logger.critical(error_msg)
        
        # Get the database path for the error message
        try:
            from db.init_db import get_db_path
            db_path = get_db_path()
        except:
            db_path = "Unknown"
            
        show_error_dialog(
            "Database Error",
            f"Failed to initialize database.\n\n"
            f"Database path: {db_path}\n\n"
            f"Error: {str(e)}\n\n"
            "Please check the log file for more details:"
            f"\n{log_file.absolute()}"
        )
        return False
    
    return True

def show_error_dialog(title, message):
    """Show an error dialog with the given title and message"""
    app = QApplication.instance() or QApplication(sys.argv)
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

# Initialize the application
if not initialize_application():
    sys.exit(1)

# Load environment variables from .env (override existing variables)
load_dotenv(override=True)

# Dynamically load local email_action_api for Flask endpoints (avoid stdlib email package conflict)
email_api_path = os.path.join(os.path.dirname(__file__), "email_module", "email_action_api.py")
if not os.path.exists(email_api_path):
    logger.error(f"Email API module not found at: {email_api_path}")
    email_api = None
    flask_app = None
else:
    try:
        spec = importlib.util.spec_from_file_location("email_action_api", email_api_path)
        email_api = importlib.util.module_from_spec(spec)
        sys.modules["email_action_api"] = email_api
        spec.loader.exec_module(email_api)
        flask_app = email_api.app
        logger.info("Successfully loaded email_action_api")
    except Exception as e:
        logger.error(f"Failed to load email_action_api: {e}")
        email_api = None
        flask_app = None

def _is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

if __name__ == "__main__":
    logger.info("Starting main application")
    
    # Initialize QApplication if not already done
    logger.info("Initializing QApplication...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        logger.info("Created new QApplication instance")
    else:
        logger.info("Using existing QApplication instance")
    
    # Set application style
    try:
        logger.info("Setting application style to Fusion...")
        app.setStyle('Fusion')  # Use Fusion style for consistent look across platforms
        logger.info("Successfully set application style")
    except Exception as e:
        logger.warning(f"Could not set Fusion style: {str(e)}")
    
    # Set application information
    logger.info("Setting application metadata...")
    app.setApplicationName("Logbook")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("YourOrganization")
    logger.info("Application metadata set")
    
    # Launch Flask API server on accessible host/port from env
    api_host = os.getenv('API_HOST', '0.0.0.0')
    api_port = int(os.getenv('API_PORT', '5050'))
    logger.info(f"Starting API server on {api_host}:{api_port}")

    # Set up ngrok tunnel in a separate thread to prevent blocking
    def setup_ngrok_tunnel():
        try:
            if not _is_online():
                logger.info("Offline mode detected; using localhost API")
                os.environ['API_BASE_URL'] = f'http://{api_host}:{api_port}'
                return

            logger.info("Internet connection detected, setting up ngrok tunnel...")
            
            import ssl
            import time
            from pyngrok import ngrok, conf, process
            
            # Configure ngrok to use a custom directory to avoid permission issues
            ngrok_config_dir = os.path.join(os.path.expanduser('~'), '.ngrok2')
            os.makedirs(ngrok_config_dir, exist_ok=True)
            conf.get_default().config_path = os.path.join(ngrok_config_dir, 'ngrok.yml')
            
            # Set ngrok authtoken if provided
            raw_token = os.getenv('NGROK_AUTH_TOKEN', '').strip()
            if raw_token:
                token = raw_token.strip('"\'')
                try:
                    # Try to set the auth token, but don't fail if it doesn't work
                    ngrok.set_auth_token(token)
                    logger.info("Successfully set ngrok authtoken")
                except Exception as e:
                    logger.warning(f"Failed to set ngrok authtoken: {e}")
                    logger.info("Continuing without ngrok authentication")
            
            # Start ngrok tunnel
            try:
                # Try to kill any existing ngrok processes if the method is available
                try:
                    if hasattr(process, 'get_processes'):
                        for proc in process.get_processes():
                            try:
                                proc.kill()
                            except Exception as e:
                                logger.warning(f"Failed to kill ngrok process: {e}")
                except Exception as e:
                    logger.warning(f"Error managing ngrok processes: {e}")
                
                # Create a new tunnel
                tunnel = ngrok.connect(api_port, 'http', bind_tls=True)
                public_url = tunnel.public_url
                os.environ['API_BASE_URL'] = public_url
                logger.info(f'Successfully established ngrok tunnel at {public_url}')
                
                # Show notification
                if app:
                    from PyQt5.QtWidgets import QSystemTrayIcon, QMenu
                    from PyQt5.QtGui import QIcon
                    
                    tray_icon = QSystemTrayIcon(QIcon(':/icons/app_icon.png'), app)
                    tray_icon.setToolTip('Logbook Application')
                    tray_icon.show()
                    tray_icon.showMessage("Logbook", f"Application is running at:\n{public_url}")
                
            except Exception as e:
                logger.error(f"Failed to establish ngrok tunnel: {e}")
                os.environ['API_BASE_URL'] = f'http://{api_host}:{api_port}'
                
        except Exception as e:
            logger.error(f"Error in ngrok setup: {e}")
            os.environ['API_BASE_URL'] = f'http://{api_host}:{api_port}'
    
    # Start ngrok setup in a separate thread
    ngrok_thread = threading.Thread(target=setup_ngrok_tunnel, daemon=True, name="NgrokSetup")
    ngrok_thread.start()

    threading.Thread(
        target=lambda: flask_app.run(host=api_host, port=api_port, debug=False, use_reloader=False),
        daemon=True
    ).start()
    # Start background processor for offline queued emails
    def _process_email_queue():
        try:
            from db.database import get_pending_email_queue, update_email_queue_status
            from email_module.email_sender import EmailSender
            logger.info("Email queue processor started")
            
            while True:
                try:
                    if _is_online():
                        queue_items = get_pending_email_queue()
                        if queue_items:
                            logger.info(f"Processing {len(queue_items)} queued emails...")
                            
                        for item in queue_items:
                            try:
                                qid = item['id']
                                rid = item['report_id']
                                aid = item['admin_id']
                                ppath = item['pdf_path']
                                
                                logger.info(f"Sending queued email for report {rid}")
                                sender = EmailSender()
                                success, msg = sender.send_final_pdf_to_admin(rid, None, aid, pdf_path=ppath)
                                
                                if success:
                                    update_email_queue_status(qid, 'sent')
                                    logger.info(f"Successfully sent queued email for report {rid}")
                                else:
                                    update_email_queue_status(qid, 'error', msg)
                                    logger.error(f"Failed to send queued email for report {rid}: {msg}")
                                    
                            except Exception as e:
                                logger.error(f"Error processing queued email {item.get('id', 'unknown')}", exc_info=True)
                                
                    time.sleep(60)  # Wait before checking again
                    
                except Exception as e:
                    logger.error("Error in email queue processor loop", exc_info=True)
                    time.sleep(60)  # Prevent tight loop on errors
                    
        except Exception as e:
            logger.critical("Email queue processor crashed", exc_info=True)
    
    # Start the email queue processor in a daemon thread
    email_thread = threading.Thread(target=_process_email_queue, daemon=True, name="EmailQueueProcessor")
    email_thread.start()
    try:
        logger.info("Creating main window...")
        main_window = MainWindow()
        logger.info("Main window created")
        
        logger.info("Showing main window...")
        main_window.show()
        logger.info("Main window shown")
        
        logger.info("Starting application event loop")
        exit_code = app.exec_()
        logger.info(f"Application event loop ended with code {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical("Fatal error in main application", exc_info=True)
        QMessageBox.critical(None, "Fatal Error", 
                           f"A fatal error occurred:\n{str(e)}\n\nCheck the log file for more details.")
        sys.exit(1)
