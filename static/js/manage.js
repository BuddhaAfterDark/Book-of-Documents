document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const folderInput = document.getElementById('folder');
    const uploadForm = document.getElementById('uploadForm');
    const folderForm = document.getElementById('folderForm');
    const documentList = document.getElementById('documentList');
    const clearAllBtn = document.getElementById('clearAll');
    const generatePDFBtn = document.getElementById('generatePDF');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    // Delete document handler
    documentList.addEventListener('click', function(e) {
        if (e.target.closest('.btn-delete')) {
            const deleteBtn = e.target.closest('.btn-delete');
            const docId = deleteBtn.dataset.id;
            deleteDocument(docId);
        }
    });
    
    // Clear all documents handler
    clearAllBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear all documents? This cannot be undone.')) {
            fetch('/documents/clear', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    documentList.innerHTML = '<div class="no-documents">No documents uploaded yet</div>';
                }
            })
            .catch(error => console.error('Error clearing documents:', error));
        }
    });
    
    // Generate PDF handler
    generatePDFBtn.addEventListener('click', function() {
        // Create a form to submit the action
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/generate';
        document.body.appendChild(form);
        form.submit();
    });
    
    // File drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropZone.classList.add('active');
    }
    
    function unhighlight() {
        dropZone.classList.remove('active');
    }
    
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        uploadFiles(files);
    }
    
    // File input change handler
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            uploadFiles(this.files);
        }
    });
    
    // Folder input change handler
    folderInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const formData = new FormData(folderForm);
            uploadWithProgress(formData);
        }
    });
    
    function uploadFiles(files) {
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('file', files[i]);
        }
        uploadWithProgress(formData);
    }
    
    function uploadWithProgress(formData) {
        // Show upload progress overlay
        uploadProgress.style.display = 'flex';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        
        const xhr = new XMLHttpRequest();
        
        xhr.open('POST', uploadForm.action, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = percentComplete + '%';
            }
        });
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.status === 'success') {
                    // Update document list
                    refreshDocumentList();
                }
            } else {
                console.error('Upload failed');
                if (xhr.responseText) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        alert('Error: ' + response.error);
                    } catch (e) {
                        alert('An error occurred during upload.');
                    }
                }
            }
            
            // Hide upload progress overlay
            uploadProgress.style.display = 'none';
            
            // Reset file inputs
            uploadForm.reset();
            folderForm.reset();
        };
        
        xhr.send(formData);
    }
    
    function deleteDocument(docId) {
        fetch(`/documents/${docId}`, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Remove the document from the list
                const docElement = document.querySelector(`.document-item[data-id="${docId}"]`);
                if (docElement) {
                    docElement.remove();
                }
                
                // If no documents left, show the "No documents" message
                if (document.querySelectorAll('.document-item').length === 0) {
                    documentList.innerHTML = '<div class="no-documents">No documents uploaded yet</div>';
                }
            }
        })
        .catch(error => console.error('Error deleting document:', error));
    }
    
    function refreshDocumentList() {
        fetch('/documents', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(documents => {
            if (documents.length === 0) {
                documentList.innerHTML = '<div class="no-documents">No documents uploaded yet</div>';
                return;
            }
            
            documentList.innerHTML = '';
            
            documents.forEach(doc => {
                const docElement = createDocumentElement(doc);
                documentList.appendChild(docElement);
            });
            
            // Initialize drag and drop for the new elements
            initDragAndDrop();
        })
        .catch(error => console.error('Error refreshing document list:', error));
    }
    
    function createDocumentElement(doc) {
        const docElement = document.createElement('div');
        docElement.className = 'document-item';
        docElement.draggable = true;
        docElement.dataset.id = doc.id;
        
        docElement.innerHTML = `
            <div class="document-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
            </div>
            <div class="document-info">
                <div class="document-name">${doc.original_filename}</div>
                <div class="document-meta">
                    <span class="document-status ${doc.status}">${doc.status}</span>
                    <span class="document-pages">${doc.page_count} pages</span>
                </div>
            </div>
            <div class="document-actions">
                <button class="btn-delete" data-id="${doc.id}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
                <div class="drag-handle">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="9" cy="12" r="1"></circle>
                        <circle cx="9" cy="5" r="1"></circle>
                        <circle cx="9" cy="19" r="1"></circle>
                        <circle cx="15" cy="12" r="1"></circle>
                        <circle cx="15" cy="5" r="1"></circle>
                        <circle cx="15" cy="19" r="1"></circle>
                    </svg>
                </div>
            </div>
        `;
        
        return docElement;
    }
    
    // Initialize drag and drop for reordering
    function initDragAndDrop() {
        const draggableItems = document.querySelectorAll('.document-item');
        
        draggableItems.forEach(item => {
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragover', handleDragOver);
            item.addEventListener('dragenter', handleDragEnter);
            item.addEventListener('dragleave', handleDragLeave);
            item.addEventListener('drop', handleDragDrop);
            item.addEventListener('dragend', handleDragEnd);
        });
    }
    
    let draggedItem = null;
    
    function handleDragStart(e) {
        draggedItem = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', ''); // Required for Firefox
    }
    
    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        return false;
    }
    
    function handleDragEnter(e) {
        this.classList.add('drag-over');
    }
    
    function handleDragLeave(e) {
        this.classList.remove('drag-over');
    }
    
    function handleDragDrop(e) {
        e.stopPropagation();
        
        if (draggedItem !== this) {
            // Get positions in the list
            const list = Array.from(documentList.children);
            const draggedPos = list.indexOf(draggedItem);
            const dropPos = list.indexOf(this);
            
            // Reorder in DOM
            if (draggedPos < dropPos) {
                documentList.insertBefore(draggedItem, this.nextSibling);
            } else {
                documentList.insertBefore(draggedItem, this);
            }
            
            // Update server with new order
            const newOrder = Array.from(documentList.children).map(item => item.dataset.id);
            updateDocumentOrder(newOrder);
        }
        
        this.classList.remove('drag-over');
        return false;
    }
    
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        draggedItem = null;
    }
    
    function updateDocumentOrder(newOrder) {
        fetch('/documents/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ order: newOrder })
        })
        .then(response => response.json())
        .catch(error => console.error('Error updating document order:', error));
    }
    
    // Initialize drag and drop on page load
    initDragAndDrop();
});
