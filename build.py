import PyInstaller.__main__
import os

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the build options
    build_options = [
        'main.py',  # Main script
        '--onefile',  # Create a single executable
        '--windowed',  # No console window
        '--name=Logbook',  # Name of the executable
        '--icon=NONE',  # No icon
        '--clean',  # Clean up build files
        '--noconfirm',  # Don't ask for confirmation
        # Add all required packages
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtNetwork',
        '--hidden-import=PyQt5.QtSql',
        '--hidden-import=PyQt5.QtSvg',
        '--hidden-import=PyQt5.QtXml',
        '--hidden-import=openpyxl',
        '--hidden-import=reportlab',
        '--hidden-import=passlib',
        '--hidden-import=Pillow',
        '--hidden-import=PyPDF2',
        '--hidden-import=python_dotenv',
        '--hidden-import=flask',
        '--hidden-import=flask.cli',
        '--hidden-import=flask.json',
        '--hidden-import=flask.helpers',
        '--hidden-import=werkzeug',
        '--hidden-import=werkzeug.serving',
        '--hidden-import=werkzeug.debug',
        '--hidden-import=jinja2',
        '--hidden-import=markupsafe',
        '--hidden-import=itsdangerous',
        '--hidden-import=click',
        '--hidden-import=waitress',
        '--hidden-import=pyngrok',
        # Add data files
        '--add-data=db;db',
        '--add-data=email;email',
        '--add-data=templates;templates',
        '--add-data=.env;.env'
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(build_options)

if __name__ == '__main__':
    main()
