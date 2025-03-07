import os
import PyPDF2
from fpdf import FPDF
from datetime import datetime

def get_pdf_page_count(pdf_path):
    """Returns the number of pages in a PDF file."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return len(reader.pages)

def create_cover_page(output_path, title, translations=None):
    """Create a cover page for the Book of Documents using FPDF."""
    if translations is None:
        translations = {"generated_on": "Generated on"}
        
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Set font and title
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 40, txt="", ln=1)  # Add some space at top
    pdf.cell(0, 20, txt=title, align='C', ln=1)
    
    # Draw the date
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, txt=f"{translations.get('generated_on', 'Generated on')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align='C')
    
    pdf.output(output_path)
    return output_path

def create_index_page(output_path, documents, translations=None):
    """Create an index page listing all documents with page numbers."""
    # Default translations to English if not provided
    if translations is None:
        translations = {
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
            "total_pages": "Total Pages"
        }
    
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Define colors
    header_bg = (44, 62, 80)  # #2c3e50 dark blue
    alt_row_bg = (242, 242, 242)  # #f2f2f2 light gray
    success_color = (40, 167, 69)  # green
    error_color = (220, 53, 69)  # red
    link_color = (0, 0, 255)  # blue for links
    
    # Add title with translation
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, translations["book_title"], 0, 1, 'C')
    
    # Add subtitle with translation
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, translations["index_title"], 0, 1, 'C')
    
    # Add instruction for navigation with translation
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, translations["index_navigation_hint"], 0, 1, 'C')
    pdf.ln(5)
    
    # Define column widths
    page_width = 210  # A4 width in mm
    margin = 10
    usable_width = page_width - (2 * margin)
    col_widths = [usable_width * 0.55, usable_width * 0.15, usable_width * 0.15, usable_width * 0.15]
    
    # Create table header for index with translations
    header = [translations["document_name"], translations["starting_page"], 
              translations["ending_page"], translations["status"]]
    
    # Set header style
    pdf.set_fill_color(*header_bg)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    
    # Draw header row
    pdf.set_x(margin)
    for i in range(len(header)):
        pdf.cell(col_widths[i], 12, header[i], 1, 0, 'C', True)
    pdf.ln()
    
    # Reset text color for content
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    
    current_page = 1  # Cover page is page 1
    current_page += 1  # Add index page to count
    
    # Draw table content
    for i, document in enumerate(documents):
        start_page = current_page
        end_page = current_page + document.page_count - 1
        
        # Alternate row colors
        if i % 2 == 1:
            pdf.set_fill_color(*alt_row_bg)
            fill = True
        else:
            pdf.set_fill_color(255, 255, 255)
            fill = True
        
        # Format long filenames
        doc_name = document.original_filename
        if len(doc_name) > 45:
            doc_name = doc_name[:42] + "..."
        
        # Set position for new row
        pdf.set_x(margin)
        
        # Document name column - with link if document status is success
        if document.status == "success":
            # Add link to the document page
            pdf.set_text_color(*link_color)  # Blue color for links
            pdf.set_font("Helvetica", "U", 10)  # Underlined font for links
            
            # Create a link to document page using page number
            # For documents after the index, their pages in the PDF start at 3 (1-based)
            target_page = i + 3 
            
            # Add cell with link to target page
            pdf.cell(col_widths[0], 8, doc_name, 1, 0, 'L', fill, link=target_page)
            
            # Reset text color and font
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 10)
        else:
            # No link for error documents
            pdf.cell(col_widths[0], 8, doc_name, 1, 0, 'L', fill)
        
        # Page number columns
        if document.status == "success":
            pdf.cell(col_widths[1], 8, str(start_page), 1, 0, 'C', fill)
            pdf.cell(col_widths[2], 8, str(end_page), 1, 0, 'C', fill)
        else:
            pdf.cell(col_widths[1], 8, "-", 1, 0, 'C', fill)
            pdf.cell(col_widths[2], 8, "-", 1, 0, 'C', fill)
        
        # Status column with color
        status_text = translations["included"] if document.status == "success" else translations["error"]
        pdf.set_x(pdf.get_x())  # Maintain position
        
        # Save current text color
        current_color = pdf.text_color
        
        # Set color based on status
        if document.status == "success":
            pdf.set_text_color(*success_color)
        else:
            pdf.set_text_color(*error_color)
            
        pdf.cell(col_widths[3], 8, status_text, 1, 0, 'C', fill)
        
        # Reset text color
        pdf.set_text_color(*current_color)
        
        pdf.ln()
        
        if document.status == "success":
            current_page += document.page_count
    
    # Add receipt page to count
    current_page += 1
    
    # Add footer with translations
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    total_text = f"{translations['total_documents']}: {len(documents)} | {translations['total_pages']}: {current_page - 1}"
    pdf.cell(0, 10, total_text, 0, 1, 'C')
    
    # Save the PDF without trying to create links
    pdf.output(output_path)
    
    # Return just the output path - no links needed
    return output_path

def create_receipt_page(output_path, book, translations=None):
    """Create a receipt page showing processing results."""
    # Default translations to English if not provided
    if translations is None:
        translations = {
            "receipt_title": "Processing Receipt",
            "summary": "Summary",
            "book_id": "Book ID",
            "created": "Created",
            "total_documents": "Total Documents",
            "total_pages": "Total Pages",
            "processing_results": "Processing Results",
            "document_name": "Document Name",
            "status": "Status",
            "pages": "Pages",
            "errors": "Errors",
            "none": "None"
        }
    
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Define colors
    header_bg = (44, 62, 80)  # #2c3e50 dark blue
    alt_row_bg = (242, 242, 242)  # #f2f2f2 light gray
    success_color = (40, 167, 69)  # green
    error_color = (220, 53, 69)  # red
    
    # Add title
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, translations["receipt_title"], 0, 1, 'C')
    
    # Add subtitle
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, translations["summary"], 0, 1, 'C')
    pdf.ln(10)
    
    # Add summary
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, txt=f"{translations['book_id']}: {book.id}", ln=1)
    pdf.cell(0, 8, txt=f"{translations['created']}: {book.created_at.strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
    pdf.cell(0, 8, txt=f"{translations['total_documents']}: {len(book.documents)}", ln=1)
    pdf.cell(0, 8, txt=f"{translations['total_pages']}: {book.total_pages}", ln=1)
    pdf.ln(10)
    
    # Add detailed results title
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, txt=translations["processing_results"], ln=1)
    pdf.ln(5)
    
    # Create table for results
    column_widths = [80, 25, 25, 60]
    header = [translations["document_name"], translations["status"], translations["pages"], translations["errors"]]
    
    # Set header style
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(*header_bg)
    pdf.set_text_color(255, 255, 255)
    
    # Draw header row
    for i in range(len(header)):
        pdf.cell(column_widths[i], 10, txt=header[i], border=1, fill=True)
    pdf.ln()
    
    # Reset text color for content
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    
    # Draw table content
    for i, doc in enumerate(book.documents):
        fill = i % 2 == 0
        
        # Truncate long filenames to fit in cell
        doc_name = doc.original_filename
        if len(doc_name) > 30:
            doc_name = doc_name[:27] + "..."
            
        pdf.cell(column_widths[0], 8, txt=doc_name, border=1, fill=fill)
        pdf.cell(column_widths[1], 8, txt=doc.status, border=1, fill=fill)
        pdf.cell(column_widths[2], 8, txt=str(doc.page_count), border=1, fill=fill)
        
        # Format errors to fit in cell
        error_txt = "\n".join(doc.errors) if doc.errors else translations["none"]
        if len(error_txt) > 40:
            error_txt = error_txt[:37] + "..."
        
        pdf.cell(column_widths[3], 8, txt=error_txt, border=1, fill=fill)
        pdf.ln()
    
    pdf.output(output_path)
    return output_path

def merge_pdfs(pdf_paths, output_path):
    """Merge multiple PDFs into a single file with bookmarks for navigation."""
    merger = PyPDF2.PdfMerger()
    
    # Add cover page
    merger.append(pdf_paths[0])
    merger.add_outline_item("Cover Page", 0, parent=None)
    
    # Add index page
    merger.append(pdf_paths[1])
    merger.add_outline_item("Index", 1, parent=None)
    
    # Create a Documents parent bookmark
    docs_parent = merger.add_outline_item("Documents", 2, parent=None)
    
    # Add each document with bookmarks
    current_page = 2  # Start after cover and index
    for i, pdf in enumerate(pdf_paths[2:-1]):  # Skip cover, index, and receipt pages
        try:
            # Add document to the merger
            merger.append(pdf)
            
            # Add a bookmark for the document
            doc_name = os.path.basename(pdf)
            merger.add_outline_item(doc_name, current_page, parent=docs_parent)
            
            # Update current page for next document
            with open(pdf, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                current_page += len(reader.pages)
        except Exception as e:
            print(f"Error merging {pdf}: {str(e)}")
    
    # Add receipt page
    merger.append(pdf_paths[-1])
    merger.add_outline_item("Receipt", current_page, parent=None)
    
    # Write the merged PDF
    merger.write(output_path)
    merger.close()
    
    return output_path

class Document:
    def __init__(self, output_path, content=None):
        self.output_path = output_path
        self.content = content or []
        self.pdf = FPDF()
        self.pdf.add_page()
    
    def build(self):
        """Build the PDF document from the content elements"""
        if not self.content:
            raise ValueError("No content to build document with")
        
        # Process each content item
        for item in self.content:
            if isinstance(item, str):
                self.pdf.cell(0, 10, txt=item, ln=True)
        
        # Save the PDF document
        self.pdf.output(self.output_path)
        return self.output_path
