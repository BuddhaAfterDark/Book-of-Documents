import os
import zipfile
import tempfile
import shutil
from models.document import Document

def extract_zip_to_folder(zip_path, extract_path):
    """Extract a ZIP file to the specified folder."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    return extract_path

def process_zip_file(zip_path, upload_folder):
    """Process a ZIP file and return a list of Document objects."""
    documents = []
    
    # Create a temporary directory for extraction
    temp_dir = tempfile.mkdtemp()
    try:
        extract_zip_to_folder(zip_path, temp_dir)
        
        # Walk through the extracted files
        for root, dirs, files in os.walk(temp_dir):
            for filename in files:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                
                file_path = os.path.join(root, filename)
                
                # Only process PDF files
                if filename.lower().endswith('.pdf'):
                    # Create a unique filename in the upload folder
                    new_filename = os.path.join(
                        upload_folder, 
                        f"{os.path.splitext(filename)[0]}_{os.path.getmtime(file_path):.0f}.pdf"
                    )
                    
                    # Copy the file to the upload folder
                    shutil.copy2(file_path, new_filename)
                    
                    # Create a document record
                    rel_path = os.path.relpath(file_path, temp_dir)
                    doc = Document(
                        filename=os.path.basename(new_filename),
                        original_filename=rel_path,
                        file_type='pdf'
                    )
                    documents.append(doc)
    
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return documents
