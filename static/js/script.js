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
    const generationProgress = document.getElementById('generationProgress');
    
    // Delete document handler
    if (documentList) {
        documentList.addEventListener('click', function(e) {
            if (e.target.closest('.btn-delete')) {
                const deleteBtn = e.target.closest('.btn-delete');
                const docId = deleteBtn.dataset.id;
                deleteDocument(docId);
            }
        });
    }
    
    // Clear all documents handler
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function() {
            if (confirm(window.i18n.t('confirm_clear'))) {
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
    }
    
    // Generate PDF handler
    if (generatePDFBtn) {
        generatePDFBtn.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent any default form submission
            
            // Show the generation progress overlay
            generationProgress.style.display = 'flex';
            
            // Get the progress bar element and reset its state
            const progressBar = generationProgress.querySelector('.progress-bar');
            const progressText = document.getElementById('generationText');
            const progressContent = generationProgress.querySelector('.upload-progress-content');
            
            // Reset progress bar color and width
            progressBar.style.backgroundColor = "#3498db"; // Reset to blue
            progressBar.style.width = '0%';
            progressBar.classList.remove('progress-indeterminate');
            
            // Remove any existing close buttons
            const existingCloseButtons = progressContent.querySelectorAll('.close-btn');
            existingCloseButtons.forEach(btn => btn.remove());
            
            // Simulate generation progress up to 95%
            let progress = 0;
            const interval = setInterval(() => {
                // Faster progression
                if (progress < 20) {
                    progress += 1.5;
                } else if (progress < 60) {
                    progress += 2;
                } else if (progress < 85) {
                    progress += 1.2;
                } else if (progress < 95) {
                    progress += 0.8;
                }
                
                // Update the progress bar
                progressBar.style.width = `${Math.min(progress, 95)}%`;
                
                // Update text for better UX with translations
                if (progress < 20) {
                    progressText.textContent = window.i18n.t('initializing_generation');
                } else if (progress < 40) {
                    progressText.textContent = window.i18n.t('processing_content');
                } else if (progress < 60) {
                    progressText.textContent = window.i18n.t('creating_index');
                } else if (progress < 80) {
                    progressText.textContent = window.i18n.t('merging_documents');
                } else {
                    progressText.textContent = window.i18n.t('finalizing');
                }
                
                // At 95%, initiate the actual download
                if (progress >= 95) {
                    clearInterval(interval);
                    progressBar.style.width = "100%";
                    progressText.textContent = window.i18n.t('starting_download');
                    
                    // Initiate fetch request instead of form submission
                    fetch('/generate', {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => {
                        // Check if the response is valid
                        if (!response.ok) {
                            // Try to get error details from response
                            return response.json().then(errData => {
                                throw new Error(`Error ${response.status}: ${errData.message || response.statusText}${errData.details ? '\n' + errData.details.join('\n') : ''}`);
                            }).catch(e => {
                                // If response isn't JSON, throw standard error
                                if (e instanceof SyntaxError) {
                                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                                }
                                throw e;
                            });
                        }
                        
                        // Get filename from content-disposition if available
                        let filename = 'book_of_documents.pdf';
                        const disposition = response.headers.get('content-disposition');
                        if (disposition && disposition.includes('filename=')) {
                            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                            const matches = filenameRegex.exec(disposition);
                            if (matches && matches[1]) {
                                filename = matches[1].replace(/['"]/g, '');
                            }
                        }
                        
                        progressText.textContent = window.i18n.t('download_progress');
                        
                        // Return the blob
                        return response.blob().then(blob => ({ blob, filename }));
                    })
                    .then(({ blob, filename }) => {
                        // Create a download link and trigger it
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = filename;
                        document.body.appendChild(a);
                        
                        // Trigger the download
                        a.click();
                        window.URL.revokeObjectURL(url);
                        
                        // Show success message with translations
                        progressText.innerHTML = `<strong>${window.i18n.t('download_complete')}</strong><br>${window.i18n.t('book_downloaded')}`;
                        
                        // Add a single close button
                        addCloseButton(progressContent, generationProgress);
                        
                        // Auto-hide after a reasonable time if not clicked
                        setTimeout(() => {
                            generationProgress.style.display = 'none';
                        }, 5000); // Hide after 5 seconds
                    })
                    .catch(error => {
                        console.error('Download error:', error);
                        
                        // Show detailed error information with translations
                        const errorMessage = error.message || window.i18n.t('unknown_error');
                        progressBar.style.backgroundColor = "#dc3545"; // Red for error
                        progressText.innerHTML = `<strong>${window.i18n.t('error')}</strong><br>${errorMessage.replace(/\n/g, '<br>')}`;
                        
                        // Add error details collapsible section if available
                        if (error.details) {
                            const detailsContainer = document.createElement('div');
                            detailsContainer.className = 'error-details';
                            detailsContainer.innerHTML = `
                                <button class="btn details-toggle">${window.i18n.t('show_details')}</button>
                                <div class="details-content" style="display:none; text-align:left; margin-top:10px;">
                                    <pre>${error.details.join('\n')}</pre>
                                </div>
                            `;
                            progressText.appendChild(detailsContainer);
                            
                            // Add toggle functionality with translations
                            const toggleBtn = detailsContainer.querySelector('.details-toggle');
                            const content = detailsContainer.querySelector('.details-content');
                            toggleBtn.addEventListener('click', function() {
                                const isVisible = content.style.display !== 'none';
                                content.style.display = isVisible ? 'none' : 'block';
                                toggleBtn.textContent = isVisible ? window.i18n.t('show_details') : window.i18n.t('hide_details');
                            });
                        }
                        
                        // Add a single close button
                        addCloseButton(progressContent, generationProgress);
                    });
                }
            }, 50); // Update more frequently for smoother animation
        });
    }
    
    // Helper function to add a single close button
    function addCloseButton(container, overlay) {
        // Remove any existing close buttons first
        const existingButtons = container.querySelectorAll('.close-btn');
        existingButtons.forEach(btn => btn.remove());
        
        // Add a new close button
        const closeButton = document.createElement('button');
        closeButton.textContent = window.i18n.t('close');
        closeButton.className = "btn close-btn";
        closeButton.onclick = function() {
            overlay.style.display = 'none';
        };
        
        container.appendChild(closeButton);
    }
    
    // Folder link handler
    const folderLink = document.querySelector('.folder-link');
    if (folderLink) {
        folderLink.addEventListener('click', function() {
            folderInput.click();
        });
    }
    
    // File drag and drop handlers
    if (dropZone) {
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
    }
    
    // File input change handler
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                uploadFiles(this.files);
            }
        });
    }
    
    // Folder input change handler
    if (folderInput) {
        folderInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const formData = new FormData(folderForm);
                uploadWithProgress(formData);
            }
        });
    }
    
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
    
    // Function to create document element with localized text
    function createDocumentElement(doc) {
        const docElement = document.createElement('div');
        docElement.className = 'document-item';
        docElement.draggable = true;
        docElement.dataset.id = doc.id;
        
        // Get localized status
        const status = doc.status === 'success' ? 
            window.i18n.t('document_status_success') : 
            window.i18n.t('document_status_error');
        
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
                    <span class="document-status ${doc.status}">${status}</span>
                    <span class="document-pages">${doc.page_count} ${window.i18n.t('document_pages')}</span>
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
    if (documentList && documentList.children.length > 0 && 
        !documentList.querySelector('.no-documents')) {
        initDragAndDrop();
    }

    // Document icon click handler for preview
    if (documentList) {
        documentList.addEventListener('click', function(e) {
            // Check if we clicked on the document icon or any of its children
            const iconClicked = e.target.closest('.document-icon');
            if (iconClicked) {
                const docItem = iconClicked.closest('.document-item');
                if (docItem) {
                    const docId = docItem.dataset.id;
                    
                    // Get document status and only open if status is "success"
                    const statusElement = docItem.querySelector('.document-status');
                    if (statusElement && statusElement.classList.contains('success')) {
                        // Open the document in a new tab
                        window.open(`/documents/view/${docId}`, '_blank');
                    } else {
                        alert(window.i18n.t('preview_not_available'));
                    }
                }
            }
        });
    }
    
    // Function to display error message in current language
    function showLocalizedError(message) {
        return window.i18n.t('error') + ': ' + message;
    }
});
