# LogBook - Report Management System

A cross-platform desktop application for managing reports with multi-level approval workflow.

## Features

- Excel template-based dynamic form generation
- Multi-level approval workflow (User → Unit Leader → Admin)
- Digital signatures and version control
- PDF report generation matching Excel layout
- Email notifications

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Configuration
Create a `.env` file in the project root with your SMTP and API settings:
```
SMTP_SERVER=<your_smtp_host>
SMTP_PORT=<smtp_port>
SMTP_USERNAME=<smtp_username>
SMTP_PASSWORD=<smtp_password>
SENDER_EMAIL=<optional_sender_override>
ENABLE_EMAIL_NOTIFICATIONS=1
API_BASE_URL=<public_api_url_for_approve_links>
API_HOST=0.0.0.0       # for run_api.py
API_PORT=5050          # for run_api.py
```

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/logbook.git
cd logbook
```

2. Create a virtual environment:
```
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```
pip install -r requirements.txt
```

5. Initialize the database:
```
python db/init_db.py
```

6. Run the application:
```
python main.py
```

### Building Executables

#### Windows (EXE)
```
python build_windows.py
```

#### Ubuntu (AppImage)
```
python build_ubuntu.py
```

## Project Structure

- `ui/`: GUI components
- `db/`: Database models and operations
- `email/`: Email notification system
- `pdf/`: PDF generation utilities
- `admin/`: Admin functionality
- `user/`: User functionality
- `leader/`: Unit Leader functionality
- `utils/`: Common utilities

## Sample Excel Template

A sample Excel template is provided in the `templates/` directory. 