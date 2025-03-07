import os
import shutil
from models.document import Document

def process_folder(folder_path, upload_folder):
    """Process a folder and return a list of Document objects."""
    documents = []
    
    # Walk through the folder
    for root, dirs, files in os.walk(folder_path):
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
                rel_path = os.path.relpath(file_path, folder_path)
                doc = Document(
                    filename=os.path.basename(new_filename),
                    original_filename=rel_path,
                    file_type='pdf'
                )
                documents.append(doc)
    
    return documents
