// Language translations
const translations = {
    // English translations
    en: {
        "app_title": "Book of Documents Generator",
        "upload_title": "Upload Documents",
        "upload_instructions": "Drag and drop PDF or ZIP files here, or click to select files",
        "choose_files": "Choose Files",
        "upload_folder_option": "You can also upload a folder containing PDF files",
        "document_list": "Document List",
        "clear_all": "Clear All",
        "generate_book": "Generate Book",
        "drag_hint": "Drag items to reorder documents in the final PDF",
        "no_documents": "No documents uploaded yet",
        "about_title": "About Book of Documents",
        "about_description": "This tool combines multiple documents into a single PDF file with:",
        "feature_cover": "A custom cover page",
        "feature_index": "An index listing all documents with page numbers",
        "feature_receipt": "A receipt page showing processing status",
        "supported_formats": "Supported formats: PDF files, ZIP archives containing PDFs",
        "view_logs": "View Recent Logs",
        "refresh_logs": "Refresh Logs",
        "uploading": "Uploading Documents",
        "generating": "Generating Book of Documents",
        "download_complete": "Download complete!",
        "book_downloaded": "Your Book of Documents has been downloaded.",
        "error": "Error!",
        "close": "Close",
        "preview_not_available": "Cannot preview: This document has errors and is not available for preview.",
        "document_status_success": "success",
        "document_status_error": "error",
        "document_pages": "pages",
        "language": "Language",
        "initializing_generation": "Initializing document generation...",
        "processing_content": "Processing document content...",
        "creating_index": "Creating index and tables...",
        "merging_documents": "Merging documents...",
        "finalizing": "Finalizing your Book of Documents...",
        "starting_download": "Starting download...",
        "download_progress": "Download in progress...",
        "show_details": "Show technical details",
        "hide_details": "Hide technical details",
        "unknown_error": "Unknown error occurred",
        "confirm_clear": "Are you sure you want to clear all documents? This cannot be undone."
    },
    // French translations
    fr: {
        "app_title": "Générateur de Livre de Documents",
        "upload_title": "Télécharger des Documents",
        "upload_instructions": "Glissez et déposez des fichiers PDF ou ZIP ici, ou cliquez pour sélectionner des fichiers",
        "choose_files": "Choisir des Fichiers",
        "upload_folder_option": "Vous pouvez également télécharger un dossier contenant des fichiers PDF",
        "document_list": "Liste des Documents",
        "clear_all": "Tout Effacer",
        "generate_book": "Générer le Livre",
        "drag_hint": "Faites glisser les éléments pour réorganiser les documents dans le PDF final",
        "no_documents": "Aucun document n'a encore été téléchargé",
        "about_title": "À propos du Livre de Documents",
        "about_description": "Cet outil combine plusieurs documents en un seul fichier PDF avec :",
        "feature_cover": "Une page de couverture personnalisée",
        "feature_index": "Un index listant tous les documents avec les numéros de page",
        "feature_receipt": "Une page de reçu montrant l'état du traitement",
        "supported_formats": "Formats pris en charge : fichiers PDF, archives ZIP contenant des PDF",
        "view_logs": "Voir les Logs Récents",
        "refresh_logs": "Actualiser les Logs",
        "uploading": "Téléchargement des Documents",
        "generating": "Génération du Livre de Documents",
        "download_complete": "Téléchargement terminé !",
        "book_downloaded": "Votre Livre de Documents a été téléchargé.",
        "error": "Erreur !",
        "close": "Fermer",
        "preview_not_available": "Impossible de prévisualiser : Ce document contient des erreurs et n'est pas disponible pour la prévisualisation.",
        "document_status_success": "succès",
        "document_status_error": "erreur",
        "document_pages": "pages",
        "language": "Langue",
        "initializing_generation": "Initialisation de la génération du document...",
        "processing_content": "Traitement du contenu du document...",
        "creating_index": "Création de l'index et des tableaux...",
        "merging_documents": "Fusion des documents...",
        "finalizing": "Finalisation de votre Livre de Documents...",
        "starting_download": "Démarrage du téléchargement...",
        "download_progress": "Téléchargement en cours...",
        "show_details": "Afficher les détails techniques",
        "hide_details": "Masquer les détails techniques",
        "unknown_error": "Une erreur inconnue s'est produite",
        "confirm_clear": "Êtes-vous sûr de vouloir effacer tous les documents ? Cette action ne peut pas être annulée."
    }
};

// Default language
let currentLanguage = localStorage.getItem('language') || 'en';

// Function to change language
function changeLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('language', lang);
    updatePageLanguage();
}

// Update all text elements on the page
function updatePageLanguage() {
    // Update title
    document.title = translations[currentLanguage]["app_title"];
    
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[currentLanguage][key]) {
            element.textContent = translations[currentLanguage][key];
        }
    });
    
    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        if (translations[currentLanguage][key]) {
            element.placeholder = translations[currentLanguage][key];
        }
    });
    
    // Update specific HTML elements that need innerHTML
    document.querySelectorAll('[data-i18n-html]').forEach(element => {
        const key = element.getAttribute('data-i18n-html');
        if (translations[currentLanguage][key]) {
            element.innerHTML = translations[currentLanguage][key];
        }
    });
    
    // Update the language selector to show current language
    const languageSelector = document.getElementById('languageSelector');
    if (languageSelector) {
        languageSelector.value = currentLanguage;
    }
}

// Initialize language when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up the language selector
    const languageSelector = document.getElementById('languageSelector');
    if (languageSelector) {
        languageSelector.value = currentLanguage;
        languageSelector.addEventListener('change', function() {
            changeLanguage(this.value);
        });
    }
    
    // Initial page translation
    updatePageLanguage();
});

// Export functions for use in other scripts
window.i18n = {
    t: function(key) {
        return translations[currentLanguage][key] || key;
    },
    getCurrentLanguage: function() {
        return currentLanguage;
    },
    changeLanguage: changeLanguage
};
