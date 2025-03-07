import os
import uuid
from datetime import datetime

class Book:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.title = f"Book of Documents - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        self.documents = []
        self.total_pages = 0
        self.output_path = ""
        
    def add_document(self, document):
        self.documents.append(document)
        self.total_pages += document.page_count
        return self
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'documents': [doc.to_dict() for doc in self.documents],
            'total_pages': self.total_pages,
            'output_path': self.output_path
        }
