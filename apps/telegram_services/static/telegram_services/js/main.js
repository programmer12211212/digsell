/* ============================================================================
   TELEGRAM SERVICES - MAIN JAVASCRIPT
   ============================================================================ */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Telegram Services initialized');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize animations
    observeElements();
    
    // Setup CSRF token
    setupCsrfToken();
});

/* ============================================================================
   BOOTSTRAP TOOLTIPS
   ============================================================================ */

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/* ============================================================================
   INTERSECTION OBSERVER FOR ANIMATIONS
   ============================================================================ */

function observeElements() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    document.querySelectorAll('.premium-card, .product-card').forEach(el => {
        observer.observe(el);
    });
}

/* ============================================================================
   CSRF TOKEN SETUP
   ============================================================================ */

function setupCsrfToken() {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrftoken) {
        window.csrfToken = csrftoken.value;
    }
}

function getCsrfToken() {
    if (window.csrfToken) {
        return window.csrfToken;
    }
    const cookieMatch = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (cookieMatch) {
        return decodeURIComponent(cookieMatch[1]);
    }
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
}

/* ============================================================================
   TOAST NOTIFICATIONS
   ============================================================================ */

class Toast {
    constructor(message, type = 'info', duration = 3000) {
        this.message = message;
        this.type = type; // success, error, warning, info
        this.duration = duration;
        this.show();
    }
    
    show() {
        const toastContainer = document.getElementById('toast-container') || this.createContainer();
        
        const toast = document.createElement('div');
        toast.className = `alert alert-${this.type} toast-enter`;
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.minWidth = '300px';
        toast.style.zIndex = '9999';
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex gap-3">
                <div class="flex-grow-1">${this.message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const closeBtn = toast.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => this.close(toast));
        
        setTimeout(() => this.close(toast), this.duration);
    }
    
    close(toast) {
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
}

/* ============================================================================
   LOADING STATE
   ============================================================================ */

class LoadingState {
    static show(element = null) {
        if (element) {
            element.disabled = true;
            element.dataset.originalContent = element.innerHTML;
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        }
    }
    
    static hide(element = null) {
        if (element && element.dataset.originalContent) {
            element.disabled = false;
            element.innerHTML = element.dataset.originalContent;
        }
    }
}

/* ============================================================================
   FORM UTILITIES
   ============================================================================ */

function serializeFormData(formElement) {
    const formData = new FormData(formElement);
    return Object.fromEntries(formData);
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateTelegramUsername(username) {
    const regex = /^@?\w{5,32}$/;
    return regex.test(username);
}

/* ============================================================================
   API REQUESTS
   ============================================================================ */

class Api {
    static async fetch(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            let errorMsg = `HTTP error! status: ${response.status}`;
            try {
                const errData = await response.json();
                if (errData && errData.message) {
                    errorMsg = errData.message;
                } else if (errData && errData.error) {
                    errorMsg = errData.error;
                }
            } catch (e) {
                // Ignore parsing errors
            }
            throw new Error(errorMsg);
        }
        
        return response.json();
    }
    
    static async get(url) {
        return this.fetch(url, { method: 'GET' });
    }
    
    static async post(url, data) {
        return this.fetch(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    static async put(url, data) {
        return this.fetch(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    static async delete(url) {
        return this.fetch(url, { method: 'DELETE' });
    }
}

/* ============================================================================
   USER INFO LOOKUP
   ============================================================================ */

async function lookupTelegramUser(username) {
    try {
        const response = await Api.get(`/telegram-services/api/user-info/?username=${username}`);
        return response;
    } catch (error) {
        console.error('Error looking up user:', error);
        throw error;
    }
}

/* ============================================================================
   ORDER CREATION
   ============================================================================ */

async function createOrder(productId, telegramUsername, button, quantity = null) {
    try {
        LoadingState.show(button);
        
        const payload = {
            telegram_username: telegramUsername
        };
        if (quantity) {
            payload.quantity = quantity;
        }
        
        const response = await Api.post(`/telegram-services/orders/create/${productId}/`, payload);
        
        if (response.success) {
            new Toast('Order created successfully!', 'success');
            window.location.href = response.redirect_url;
        } else {
            new Toast(response.message || response.error || 'Failed to create order', 'danger');
        }
    } catch (error) {
        new Toast('Error creating order: ' + error.message, 'danger');
    } finally {
        LoadingState.hide(button);
    }
}

/* ============================================================================
   PRODUCT FILTERING
   ============================================================================ */

function filterProducts(category = '', search = '', sortBy = '') {
    const params = new URLSearchParams();
    
    if (category) params.append('category', category);
    if (search) params.append('search', search);
    if (sortBy) params.append('sort_by', sortBy);
    
    const queryString = params.toString();
    window.location.href = `/telegram-services/products/?${queryString}`;
}

/* ============================================================================
   COPY TO CLIPBOARD
   ============================================================================ */

function copyToClipboard(text, button = null) {
    navigator.clipboard.writeText(text).then(() => {
        if (button) {
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check me-2"></i>Copied!';
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        }
        new Toast('Copied to clipboard!', 'success', 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        new Toast('Failed to copy', 'danger');
    });
}

/* ============================================================================
   CURRENCY FORMATTING
   ============================================================================ */

function formatCurrency(amount, currency = 'UZS') {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('uz-UZ').format(number);
}

/* ============================================================================
   DATE FORMATTING
   ============================================================================ */

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('uz-UZ', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/* ============================================================================
   SMOOTH SCROLL
   ============================================================================ */

function smoothScroll(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

/* ============================================================================
   MODAL HELPERS
   ============================================================================ */

function showModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) modal.hide();
}

/* ============================================================================
   KEYBOARD SHORTCUTS
   ============================================================================ */

document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + K to focus search
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        const searchInput = document.querySelector('input[type="search"]');
        if (searchInput) searchInput.focus();
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            bootstrap.Modal.getInstance(modal)?.hide();
        });
    }
});

/* ============================================================================
   UTILITY FUNCTIONS
   ============================================================================ */

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other files
window.Toast = Toast;
window.Api = Api;
window.LoadingState = LoadingState;
window.validateTelegramUsername = validateTelegramUsername;
window.copyToClipboard = copyToClipboard;
window.formatCurrency = formatCurrency;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.smoothScroll = smoothScroll;
