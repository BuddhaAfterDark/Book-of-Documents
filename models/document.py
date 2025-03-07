import os
import uuid

class Document:
    def __init__(self, filename, original_filename, file_type):
        self.id = str(uuid.uuid4())
        self.filename = filename
        self.original_filename = original_filename
        self.file_type = file_type
        self.page_count = 0
        self.status = "pending"
        self.errors = []
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'page_count': self.page_count,
            'status': self.status,
            'errors': self.errors
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a Document instance from a dictionary"""
        doc = cls(
            filename=data.get('filename'),
            original_filename=data.get('original_filename'),
            file_type=data.get('file_type')
        )
        doc.id = data.get('id')
        doc.page_count = data.get('page_count', 0)
        doc.status = data.get('status', 'pending')
        doc.errors = data.get('errors', [])
        return doc
