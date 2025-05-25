import sys
import threading
import os, sys, importlib.util
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from dotenv import load_dotenv
import socket
import time

# Load environment variables from .env (override existing variables)
load_dotenv(override=True)

# Dynamically load local email_action_api for Flask endpoints (avoid stdlib email package conflict)
email_api_path = os.path.join(os.path.dirname(__file__), "email", "email_action_api.py")
spec = importlib.util.spec_from_file_location("email_action_api", email_api_path)
email_api = importlib.util.module_from_spec(spec)
sys.modules["email_action_api"] = email_api
spec.loader.exec_module(email_api)
flask_app = email_api.app
print("DEBUG: Starting email_action_api server on port 5050")

def _is_online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

if __name__ == "__main__":
    # Launch Flask API server on accessible host/port from env
    api_host = os.getenv('API_HOST', '0.0.0.0')
    api_port = int(os.getenv('API_PORT', '5050'))

    # Attempt to set up external tunnel only if internet is available
    if _is_online():
        try:
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            from pyngrok import ngrok
            raw_token = os.getenv('NGROK_AUTH_TOKEN', '')
            token = raw_token.strip().strip('"').strip("'")
            if token:
                ngrok.set_auth_token(token)
                print("DEBUG: Ngrok authtoken set")
            else:
                print("WARNING: NGROK_AUTH_TOKEN not set, using existing ngrok CLI config")
            tunnel = ngrok.connect(api_port, 'http', bind_tls=True)
            public_url = tunnel.public_url
            print(f'DEBUG: Ngrok tunnel established at {public_url}')
            os.environ['API_BASE_URL'] = public_url
        except Exception as e:
            print(f"WARNING: ngrok failed ({e}), using localhost API")
            os.environ['API_BASE_URL'] = f'http://{api_host}:{api_port}'
    else:
        print("DEBUG: Offline mode detected; using localhost API")
        os.environ['API_BASE_URL'] = f'http://{api_host}:{api_port}'

    threading.Thread(
        target=lambda: flask_app.run(host=api_host, port=api_port, debug=False, use_reloader=False),
        daemon=True
    ).start()
    # Start background processor for offline queued emails
    def _process_email_queue():
        from db.database import get_pending_email_queue, update_email_queue_status
        from email.email_sender import EmailSender
        while True:
            if _is_online():
                queue_items = get_pending_email_queue()
                for item in queue_items:
                    qid = item['id']
                    rid = item['report_id']
                    aid = item['admin_id']
                    ppath = item['pdf_path']
                    sender = EmailSender()
                    success, msg = sender.send_final_pdf_to_admin(rid, None, aid, pdf_path=ppath)
                    if success:
                        update_email_queue_status(qid, 'sent')
                        print(f"DEBUG: Sent queued email for report {rid}")
                    else:
                        update_email_queue_status(qid, 'error', msg)
                        print(f"ERROR: Queued email failed for report {rid}: {msg}")
            time.sleep(60)
    threading.Thread(target=_process_email_queue, daemon=True).start()
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
