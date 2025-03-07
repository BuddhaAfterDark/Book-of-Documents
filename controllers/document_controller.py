import os
import tempfile
import shutil
import importlib
import json
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, send_file, session, jsonify
import PyPDF2
from werkzeug.utils import secure_filename
from models.document import Document
from models.book import Book
from utils.zip_utils import process_zip_file
from utils.folder_utils import process_folder
import getpass  # Add this to get the username
from datetime import datetime  # Add this for timestamp

document_blueprint = Blueprint('document', __name__, template_folder='../views/templates')

ALLOWED_EXTENSIONS = {'pdf', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_session():
    if 'documents' not in session:
        session['documents'] = []
    if 'document_count' not in session:
        session['document_count'] = 0

def save_document_to_session(doc):
    """Save document to session storage"""
    init_session()
    # Convert document object to dict for session storage
    doc_dict = doc.to_dict()
    session['documents'].append(doc_dict)
    session['document_count'] += 1
    session.modified = True
    return doc_dict

def get_documents_from_session():
    """Get list of documents from session storage"""
    init_session()
    docs = []
    for doc_dict in session.get('documents', []):
        # Convert back to Document object
        doc = Document.from_dict(doc_dict)
        docs.append(doc)
    return docs

def clear_session_documents():
    """Clear documents from session"""
    session['documents'] = []
    session['document_count'] = 0
    session.modified = True

@document_blueprint.route('/', methods=['GET'])
def index():
    init_session()
    documents = get_documents_from_session()
    return render_template('index.html', documents=documents)

@document_blueprint.route('/documents', methods=['GET'])
def get_documents():
    documents = get_documents_from_session()
    return jsonify([doc.to_dict() for doc in documents])

@document_blueprint.route('/documents/clear', methods=['POST'])
def clear_documents():
    clear_session_documents()
    return jsonify({'status': 'success'})

@document_blueprint.route('/documents/reorder', methods=['POST'])
def reorder_documents():
    new_order = request.json.get('order', [])
    documents = session.get('documents', [])
    
    # Create a new list with reordered documents
    reordered_docs = []
    for doc_id in new_order:
        for doc in documents:
            if doc['id'] == doc_id:
                reordered_docs.append(doc)
                break
    
    session['documents'] = reordered_docs
    session.modified = True
    return jsonify({'status': 'success'})

@document_blueprint.route('/upload', methods=['POST'])
def upload_file():
    # Dynamically import the configured PDF utility module
    pdf_utils_module = importlib.import_module(current_app.config['PDF_UTIL_MODULE'])
    get_pdf_page_count = pdf_utils_module.get_pdf_page_count
    
    if 'file' not in request.files and 'folder' not in request.files:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'No file or folder selected'}), 400
        flash('No file or folder selected')
        return redirect(url_for('document.index'))
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Process uploaded file or folder
    if 'file' in request.files:
        files = request.files.getlist('file')
        uploaded_docs = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Process based on file type
                if filename.lower().endswith('.pdf'):
                    # Create document object
                    doc = Document(filename=filename, original_filename=file.filename, file_type='pdf')
                    try:
                        doc.page_count = get_pdf_page_count(file_path)
                        doc.status = "success"
                    except Exception as e:
                        doc.status = "error"
                        doc.errors.append(str(e))
                    
                    # Save to session
                    doc_dict = save_document_to_session(doc)
                    uploaded_docs.append(doc_dict)
                    
                elif filename.lower().endswith('.zip'):
                    # Process ZIP file
                    try:
                        documents = process_zip_file(file_path, upload_folder)
                        for doc in documents:
                            try:
                                pdf_path = os.path.join(upload_folder, doc.filename)
                                doc.page_count = get_pdf_page_count(pdf_path)
                                doc.status = "success"
                            except Exception as e:
                                doc.status = "error"
                                doc.errors.append(str(e))
                            
                            # Save to session
                            doc_dict = save_document_to_session(doc)
                            uploaded_docs.append(doc_dict)
                    except Exception as e:
                        error_msg = f"Error processing ZIP file: {str(e)}"
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({'error': error_msg}), 400
                        flash(error_msg)
                        return redirect(url_for('document.index'))
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success', 
                'documents': uploaded_docs,
                'message': f'Successfully uploaded {len(uploaded_docs)} document(s)'
            })
    
    # Process uploaded folder (if supported by the browser)
    elif 'folder' in request.files:
        folder = request.files.getlist('folder')
        temp_folder = tempfile.mkdtemp()
        uploaded_docs = []
        
        try:
            # Save all files to temporary folder
            for file in folder:
                if file.filename == '':
                    continue
                
                # Create subdirectories if necessary
                dirs = os.path.dirname(file.filename)
                if dirs:
                    os.makedirs(os.path.join(temp_folder, dirs), exist_ok=True)
                
                file_path = os.path.join(temp_folder, file.filename)
                file.save(file_path)
            
            # Process the folder
            documents = process_folder(temp_folder, upload_folder)
            for doc in documents:
                try:
                    pdf_path = os.path.join(upload_folder, doc.filename)
                    doc.page_count = get_pdf_page_count(pdf_path)
                    doc.status = "success"
                except Exception as e:
                    doc.status = "error"
                    doc.errors.append(str(e))
                
                # Save to session
                doc_dict = save_document_to_session(doc)
                uploaded_docs.append(doc_dict)
                
        finally:
            # Clean up temp folder
            shutil.rmtree(temp_folder, ignore_errors=True)
            
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'success', 
                'documents': uploaded_docs,
                'message': f'Successfully uploaded {len(uploaded_docs)} document(s) from folder'
            })
    
    # For non-AJAX requests, redirect back to index page
    return redirect(url_for('document.index'))

# Add translations dictionary for PDF generation
PDF_TRANSLATIONS = {
    "en": {
        "book_title": "Book of Documents",
        "index_title": "Index of Contents",
        "index_navigation_hint": "Use the bookmarks panel in your PDF viewer to navigate between documents",
        "document_name": "Document Name",
        "starting_page": "Starting Page",
        "ending_page": "Ending Page",
        "status": "Status",
        "included": "Included",
        "error": "Error",
        "total_documents": "Total Documents",
        "total_pages": "Total Pages",
        "receipt_title": "Processing Receipt",
        "summary": "Summary",
        "book_id": "Book ID",
        "created": "Created",
        "processing_results": "Processing Results",
        "pages": "Pages",
        "errors": "Errors",
        "none": "None",
        "generated_on": "Generated on"
    },
    "fr": {
        "book_title": "Livre de Documents",
        "index_title": "Index du Contenu",
        "index_navigation_hint": "Utilisez le panneau des signets dans votre lecteur PDF pour naviguer entre les documents",
        "document_name": "Nom du Document",
        "starting_page": "Page de Début",
        "ending_page": "Page de Fin",
        "status": "Statut",
        "included": "Inclus",
        "error": "Erreur",
        "total_documents": "Total des Documents",
        "total_pages": "Total des Pages",
        "receipt_title": "Reçu de Traitement",
        "summary": "Résumé",
        "book_id": "ID du Livre",
        "created": "Créé le",
        "processing_results": "Résultats de Traitement",
        "pages": "Pages",
        "errors": "Erreurs",
        "none": "Aucune",
        "generated_on": "Généré le"
    }
}

@document_blueprint.route('/generate', methods=['POST'])
def generate_pdf():
    logger = current_app.config['LOGGER']
    logger.info("Starting Book of Documents generation")
    
    # Get the selected language from request or default to English
    language = request.args.get('language', 'en')
    if language not in PDF_TRANSLATIONS:
        language = 'en'
    
    logger.info(f"Generating Book of Documents in language: {language}")
    
    # Dynamically import the configured PDF utility module
    try:
        pdf_utils_module = importlib.import_module(current_app.config['PDF_UTIL_MODULE'])
        create_cover_page = pdf_utils_module.create_cover_page
        create_index_page = pdf_utils_module.create_index_page
        create_receipt_page = pdf_utils_module.create_receipt_page
        merge_pdfs = pdf_utils_module.merge_pdfs
        Document_PDF = pdf_utils_module.Document  # Get the Document class from the PDF module
    except ImportError as e:
        error_msg = f"Failed to import PDF utilities: {str(e)}"
        logger.error(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': error_msg}), 500
        flash(error_msg)
        return redirect(url_for('document.index'))
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    output_folder = current_app.config['OUTPUT_FOLDER']
    
    # Get documents from session
    documents = get_documents_from_session()
    logger.info(f"Retrieved {len(documents)} documents from session")
    
    # Create a new Book instance
    book = Book()
    
    # Add all documents to the book
    for doc in documents:
        book.add_document(doc)
    
    # If no documents were processed successfully, return error
    if all(doc.status == "error" for doc in book.documents) or not book.documents:
        error_msg = "No valid PDF documents were found."
        logger.error(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': error_msg}), 400
        flash(error_msg)
        return redirect(url_for('document.index'))
    
    # Create the Book of Documents
    try:
        # Generate temporary files for cover, index, and receipt
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        cover_path = os.path.join(temp_dir, 'cover.pdf')
        index_path = os.path.join(temp_dir, 'index.pdf')
        receipt_path = os.path.join(temp_dir, 'receipt.pdf')
        
        # Pass translations to PDF generation functions
        translations = PDF_TRANSLATIONS[language]
        
        logger.info("Creating cover page...")
        create_cover_page(cover_path, translations["book_title"])
        
        logger.info("Creating index page...")
        index_result = create_index_page(index_path, book.documents, translations)
        
        # Handle both return formats (path or tuple with links)
        if isinstance(index_result, tuple):
            index_path, document_links = index_result
        
        logger.info("Creating receipt page...")
        create_receipt_page(receipt_path, book, translations)
        
        # Prepare list of PDFs to merge
        pdfs_to_merge = [cover_path, index_path]
        
        # Add document PDFs in the order they appear in the session
        success_count = 0
        for doc in documents:
            if doc.status == "success":
                pdf_path = os.path.join(upload_folder, doc.filename)
                # Verify the file exists before trying to merge
                if not os.path.exists(pdf_path):
                    logger.error(f"Document file not found: {pdf_path}")
                    continue
                pdfs_to_merge.append(pdf_path)
                success_count += 1
        
        logger.info(f"Found {success_count} successful documents to merge")
        
        # Add receipt at the end
        pdfs_to_merge.append(receipt_path)
        
        # Verify each PDF file to be merged exists and is valid
        valid_pdfs = []
        for pdf_path in pdfs_to_merge:
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if len(reader.pages) > 0:
                        valid_pdfs.append(pdf_path)
                    else:
                        logger.error(f"PDF has 0 pages: {pdf_path}")
            except Exception as e:
                logger.error(f"Invalid PDF file {pdf_path}: {str(e)}")
        
        if len(valid_pdfs) < 3:  # At minimum need cover, index, receipt
            raise ValueError("Not enough valid PDF components to create the book")
        
        # Get current username and format timestamp for filename
        username = getpass.getuser()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create filename with username and timestamp instead of GUID
        output_filename = f"book_of_documents_{username}_{timestamp}.pdf"
        output_path = os.path.join(output_folder, output_filename)
        logger.info(f"Merging {len(valid_pdfs)} PDFs to: {output_path}")
        merge_pdfs(valid_pdfs, output_path)
        
        book.output_path = output_path
        
        # Verify the output file was created successfully
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise FileNotFoundError("Generated PDF file is missing or empty")
        
        # Cleanup temporary files
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as cleanup_error:
            logger.warning(f"Error cleaning up temp dir: {str(cleanup_error)}")
        
        logger.info(f"Successfully generated Book of Documents: {output_path}")
        
        # Return the compiled PDF
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        # Get detailed error information
        import traceback
        error_traceback = traceback.format_exc()
        error_message = f"Error creating Book of Documents: {str(e)}\n\nDetails:\n{error_traceback}"
        
        # Log the error with all details
        logger.error(error_message)
        
        # Try to clean up temp dir if it exists
        try:
            if 'temp_dir' in locals() and temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass  # Ignore cleanup errors
        
        # Return appropriate error response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'error',
                'message': str(e),
                'details': error_traceback.split('\n')[-3:] # Send last 3 lines of traceback
            }), 500
            
        flash(error_message)
        return redirect(url_for('document.index'))

@document_blueprint.route('/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    documents = session.get('documents', [])
    for i, doc in enumerate(documents):
        if doc['id'] == document_id:
            # Remove document from session
            documents.pop(i)
            session['documents'] = documents
            session['document_count'] = len(documents)
            session.modified = True
            
            # Delete file from upload folder if it exists
            try:
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, doc['filename'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass  # Ignore errors deleting file
                
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Document not found'}), 404

@document_blueprint.route('/documents/view/<document_id>', methods=['GET'])
def view_document(document_id):
    """View a single document by ID"""
    logger = current_app.config['LOGGER']
    
    # Find document in session
    documents = session.get('documents', [])
    for doc in documents:
        if doc['id'] == document_id:
            try:
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, doc['filename'])
                
                if os.path.exists(file_path):
                    logger.info(f"Serving document: {doc['original_filename']} from {file_path}")
                    return send_file(
                        file_path,
                        mimetype='application/pdf'
                    )
                else:
                    logger.error(f"Document file not found: {file_path}")
                    return "Document file not found", 404
            except Exception as e:
                logger.error(f"Error serving document {document_id}: {str(e)}")
                return f"Error serving document: {str(e)}", 500
    
    logger.error(f"Document with ID {document_id} not found in session")
    return "Document not found", 404

@document_blueprint.route('/logs', methods=['GET'])
def view_logs():
    """View the most recent log entries"""
    try:
        log_path = 'logs/application.log'
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                # Get the last 100 lines (or fewer if file is smaller)
                lines = f.readlines()
                last_lines = lines[-100:] if len(lines) > 100 else lines
                return ''.join(last_lines)
        else:
            return "No log file found"
    except Exception as e:
        return f"Error reading log file: {str(e)}"
