#!/usr/bin/env python3
"""
Entry point for production API server using waitress WSGI.
Run: python run_api.py
"""
import os
from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()
import sys
import importlib.util
from waitress import serve

# Dynamically load local email_action_api to avoid stdlib 'email' collision
email_api_path = os.path.join(os.path.dirname(__file__), "email", "email_action_api.py")
spec = importlib.util.spec_from_file_location("email_action_api", email_api_path)
email_api = importlib.util.module_from_spec(spec)
sys.modules["email_action_api"] = email_api
spec.loader.exec_module(email_api)
app = email_api.app

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', '5050'))
    host = os.getenv('API_HOST', '0.0.0.0')
    print(f"Serving API on {host}:{port} using waitress")
    serve(app, host=host, port=port)
