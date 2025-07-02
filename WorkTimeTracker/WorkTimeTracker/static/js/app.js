// TimeTracker Pro - Main Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeApp();
});

function initializeApp() {
    // Initialize GPS functionality
    if (typeof initGPS === 'function') {
        initGPS();
    }
    
    // Initialize form validations
    initFormValidations();
    
    // Initialize tooltips
    initTooltips();
    
    // Auto-dismiss alerts
    autoDismissAlerts();
    
    console.log('TimeTracker Pro initialized successfully');
}

// Form validation utilities
function initFormValidations() {
    // Add validation to all forms
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showValidationErrors(form);
            }
            form.classList.add('was-validated');
        });
    });
}

function showValidationErrors(form) {
    const invalidInputs = form.querySelectorAll(':invalid');
    
    invalidInputs.forEach(input => {
        const feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            const div = document.createElement('div');
            div.className = 'invalid-feedback';
            div.textContent = getValidationMessage(input);
            input.parentNode.appendChild(div);
        }
    });
}

function getValidationMessage(input) {
    if (input.validity.valueMissing) {
        return `${input.labels[0]?.textContent || 'This field'} is required.`;
    }
    if (input.validity.typeMismatch) {
        return `Please enter a valid ${input.type}.`;
    }
    if (input.validity.patternMismatch) {
        return 'Please match the requested format.';
    }
    return 'Please check this field.';
}

// Tooltip initialization
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-dismiss alerts after 5 seconds
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// Utility functions
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toastId = 'toast_' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    return container;
}

// Loading state management
function showLoading(element, text = 'Loading...') {
    if (element.tagName === 'BUTTON') {
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${text}`;
        element.disabled = true;
    }
}

function hideLoading(element) {
    if (element.tagName === 'BUTTON' && element.dataset.originalText) {
        element.innerHTML = element.dataset.originalText;
        element.disabled = false;
        delete element.dataset.originalText;
    }
}

// Time formatting utilities
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function formatDate(date) {
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

// Local storage utilities
function saveToStorage(key, value) {
    try {
        localStorage.setItem('timetracker_' + key, JSON.stringify(value));
    } catch (e) {
        console.warn('Failed to save to localStorage:', e);
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem('timetracker_' + key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.warn('Failed to load from localStorage:', e);
        return defaultValue;
    }
}

// Error handling
function handleError(error, context = 'Application') {
    console.error(`${context} Error:`, error);
    
    showToast('An error occurred. Please try again.', 'danger');
    
    // You could send errors to a logging service here
    // logError(error, context);
}

// Export functions for global use
window.TimeTracker = {
    showToast,
    showLoading,
    hideLoading,
    formatDuration,
    formatTime,
    formatDate,
    saveToStorage,
    loadFromStorage,
    handleError
};
