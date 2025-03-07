from flask import Flask
from controllers.document_controller import document_blueprint
import importlib.util
import os
import secrets
import logging
from logging.handlers import RotatingFileHandler
import traceback

# Configure logging more thoroughly
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
    ]
)

# Create a specific logger for the app
logger = logging.getLogger('book_of_documents')
logger.setLevel(logging.DEBUG)  # Set to DEBUG for development

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Add file handler to save logs to file with more detailed formatting
file_handler = RotatingFileHandler(
    'logs/application.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
))
logger.addHandler(file_handler)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1073741824  # 1GB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key for sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds (1 hour)
app.config['LOGGER'] = logger

# Configure Flask to log errors
if not app.debug:
    app.logger.addHandler(file_handler)

# Check if ReportLab is available, otherwise use FPDF
try:
    import reportlab
    app.config['PDF_UTIL_MODULE'] = 'utils.pdf_utils'
    logger.info("Using ReportLab for PDF generation")
except ImportError:
    app.config['PDF_UTIL_MODULE'] = 'utils.pdf_utils_fpdf'
    logger.info("Using FPDF for PDF generation")

# Register blueprints
app.register_blueprint(document_blueprint)

# Error handler for internal server errors
@app.errorhandler(500)
def internal_error(error):
    error_traceback = traceback.format_exc()
    logger.error(f"Internal Server Error: {error_traceback}")
    return "Internal Server Error", 500

if __name__ == '__main__':
    # Create necessary directories
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        os.makedirs(folder, exist_ok=True)
    
    app.run(debug=True)
