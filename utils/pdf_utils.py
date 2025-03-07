import os
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def get_pdf_page_count(pdf_path):
    """Returns the number of pages in a PDF file."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return len(reader.pages)

def create_cover_page(output_path, title, translations=None):
    """Create a cover page for the Book of Documents."""
    if translations is None:
        translations = {"generated_on": "Generated on"}
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Draw the title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 100, title)
    
    # Draw the date
    from datetime import datetime
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 150, 
                      f"{translations.get('generated_on', 'Generated on')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.save()
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
    
    index_doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = styles['Title']
    title_style.fontSize = 24
    title_style.spaceAfter = 20
    
    subtitle_style = styles['Heading2']
    subtitle_style.alignment = 1  # Center alignment
    subtitle_style.spaceAfter = 30
    
    # Create style for document names (blue but not clickable)
    doc_name_style = styles['Normal'].clone('DocStyle')
    doc_name_style.textColor = colors.blue
    doc_name_style.fontSize = 10
    
    # Create content
    content = []
    
    # Add title and subtitle with translations
    content.append(Paragraph(translations["book_title"], title_style))
    content.append(Paragraph(translations["index_title"], subtitle_style))
    content.append(Paragraph(translations["index_navigation_hint"], styles['Italic']))
    content.append(Paragraph(" ", styles['Normal']))
    
    # Create table for index with better column widths
    column_widths = [280, 75, 75, 70]
    data = [[translations["document_name"], translations["starting_page"], 
             translations["ending_page"], translations["status"]]]
    
    current_page = 1  # Cover page is page 1
    current_page += 1  # Add index page to count
    
    # Add document rows
    for i, document in enumerate(documents):
        if document.status == "success":
            status_text = translations["included"]
            
            # Format long file names nicely
            doc_name = document.original_filename
            if len(doc_name) > 40:
                doc_name = doc_name[:37] + "..."
            
            start_page = current_page
            end_page = current_page + document.page_count - 1
            
            # Add document name with blue styling but NO link
            doc_text = Paragraph(doc_name, doc_name_style)
            
            data.append([
                doc_text,
                start_page,
                end_page,
                status_text
            ])
            current_page += document.page_count
        else:
            # For error documents
            status_text = translations["error"]
            
            # Format long file names nicely
            doc_name = document.original_filename
            if len(doc_name) > 40:
                doc_name = doc_name[:37] + "..."
                
            data.append([
                doc_name,
                "-",
                "-",
                status_text
            ])
    
    # Add receipt page to count
    current_page += 1
    
    # Create table with enhanced styling
    table = Table(data, colWidths=column_widths)
    table_style = [
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Content styling - alternating rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center-align numeric columns
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Left-align document names
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
        
        # Zebra striping
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f2f2f2')) for i in range(2, len(data), 2)],
        
        # Status column color coding
        *[('TEXTCOLOR', (3, i), (3, i), 
          colors.green if isinstance(data[i][3], str) and data[i][3] == "Included" else colors.red) 
          for i in range(1, len(data))],
    ]
    
    table.setStyle(TableStyle(table_style))
    content.append(table)
    
    # Add footer text with translations
    footer_text = f"{translations['total_documents']}: {len(documents)} | {translations['total_pages']}: {current_page - 1}"
    footer_style = styles['Normal']
    footer_style.alignment = 1  # Center alignment
    footer_style.spaceBefore = 30
    content.append(Paragraph(footer_text, footer_style))
    
    # Build the PDF
    index_doc.build(content)
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
    
    receipt_doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = styles['Title']
    title_style.fontSize = 24
    title_style.spaceAfter = 20
    
    subtitle_style = styles['Heading2']
    subtitle_style.alignment = 1  # Center alignment
    subtitle_style.spaceAfter = 30
    
    # Create content
    content = []
    
    # Add title and subtitle with translations
    content.append(Paragraph(translations["receipt_title"], title_style))
    content.append(Paragraph(" ", styles['Normal']))
    
    # Add summary with translations
    content.append(Paragraph(f"{translations['book_id']}: {book.id}", styles['Normal']))
    content.append(Paragraph(f"{translations['created']}: {book.created_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    content.append(Paragraph(f"{translations['total_documents']}: {len(book.documents)}", styles['Normal']))
    content.append(Paragraph(f"{translations['total_pages']}: {book.total_pages}", styles['Normal']))
    content.append(Paragraph(" ", styles['Normal']))
    
    # Add detailed results
    content.append(Paragraph(translations["processing_results"], subtitle_style))
    
    # Create table for results with translations
    data = [[translations["document_name"], translations["status"], 
             translations["pages"], translations["errors"]]]
    
    for doc in book.documents:
        data.append([
            doc.original_filename,
            doc.status,
            doc.page_count,
            "\n".join(doc.errors) if doc.errors else translations["none"]
        ])
    
    # Create table with enhanced styling
    table = Table(data, colWidths=[200, 75, 75, 150])
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Content styling - alternating rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center-align numeric columns
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Left-align document names
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c3e50')),
        
        # Zebra striping
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f2f2f2')) for i in range(2, len(data), 2)],
        
        # Status column color coding
        *[('TEXTCOLOR', (1, i), (1, i), 
          colors.green if data[i][1] == "success" else colors.red) 
          for i in range(1, len(data))],
    ]))
    
    content.append(table)
    
    # Build the PDF
    receipt_doc.build(content)
    return output_path

def merge_pdfs(pdf_paths, output_path):
    """Merge multiple PDFs into a single file with bookmarks for navigation."""
    merger = PyPDF2.PdfMerger()
    
    # Add cover page
    merger.append(pdf_paths[0])
    
    # Add index page
    merger.append(pdf_paths[1])
    
    # Add each document with a bookmark
    current_page = 2  # Start after cover and index
    for i, pdf in enumerate(pdf_paths[2:-1]):  # Skip cover, index, and receipt pages
        try:
            # Add the document to the merger
            merger.append(pdf)
            
            # Add bookmark that links to this page
            doc_name = os.path.basename(pdf)
            # Create a bookmark at the current page number
            merger.add_outline_item(doc_name, current_page, parent=None)
            
            # Get page count to update current_page
            with open(pdf, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                current_page += len(reader.pages)
        except Exception as e:
            print(f"Error merging {pdf}: {str(e)}")
    
    # Add receipt page
    merger.append(pdf_paths[-1])
    
    # Write the merged PDF
    merger.write(output_path)
    merger.close()
    
    return output_path

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

class Document:
    def __init__(self, output_path, content=None):
        self.output_path = output_path
        self.content = content or []
        self.doc = SimpleDocTemplate(output_path)
        self.styles = getSampleStyleSheet()
    
    def build(self):
        """Build the PDF document from the content elements"""
        if not self.content:
            raise ValueError("No content to build document with")
        
        # Convert string content items to Paragraph objects if needed
        elements = []
        for item in self.content:
            if isinstance(item, str):
                elements.append(Paragraph(item, self.styles["Normal"]))
            else:
                elements.append(item)
                
        # Build the document with the elements
        self.doc.build(elements)
        return self.output_path
