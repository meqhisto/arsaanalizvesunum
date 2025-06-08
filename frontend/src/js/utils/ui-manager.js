// frontend/src/js/utils/ui-manager.js

export class UIManager {
    constructor() {
        this.modals = new Map();
        this.loadingStates = new Map();
        this.activeDropdowns = new Set();
        
        this.init();
    }

    init() {
        // Setup global event listeners
        this.setupGlobalEventListeners();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    setupGlobalEventListeners() {
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            this.closeDropdownsExcept(e.target);
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleEscapeKey();
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.openSearch();
            }
            
            // Ctrl/Cmd + / for help
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.openHelp();
            }
        });
    }

    // Modal management
    openModal(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal with id '${modalId}' not found`);
            return;
        }

        // Store modal state
        this.modals.set(modalId, {
            element: modal,
            options,
            isOpen: true
        });

        // Show modal
        modal.classList.remove('hidden');
        
        // Add backdrop click handler
        if (options.closeOnBackdrop !== false) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modalId);
                }
            });
        }

        // Focus management
        if (options.autoFocus !== false) {
            const firstInput = modal.querySelector('input, textarea, select, button');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        const modalState = this.modals.get(modalId);
        if (!modalState) return;

        const modal = modalState.element;
        modal.classList.add('hidden');
        
        // Update state
        modalState.isOpen = false;
        
        // Restore body scroll if no other modals are open
        const hasOpenModals = Array.from(this.modals.values()).some(state => state.isOpen);
        if (!hasOpenModals) {
            document.body.style.overflow = '';
        }

        // Call close callback if provided
        if (modalState.options.onClose) {
            modalState.options.onClose();
        }
    }

    closeAllModals() {
        for (const modalId of this.modals.keys()) {
            this.closeModal(modalId);
        }
    }

    // Loading states
    showLoading(elementId, message = 'Yükleniyor...') {
        const element = document.getElementById(elementId);
        if (!element) return;

        // Store original content
        this.loadingStates.set(elementId, {
            originalContent: element.innerHTML,
            element
        });

        // Show loading
        element.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                <span class="text-gray-600">${message}</span>
            </div>
        `;
    }

    hideLoading(elementId) {
        const loadingState = this.loadingStates.get(elementId);
        if (!loadingState) return;

        // Restore original content
        loadingState.element.innerHTML = loadingState.originalContent;
        
        // Clean up
        this.loadingStates.delete(elementId);
    }

    // Dropdown management
    toggleDropdown(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;

        const isOpen = !dropdown.classList.contains('hidden');
        
        if (isOpen) {
            this.closeDropdown(dropdownId);
        } else {
            this.openDropdown(dropdownId);
        }
    }

    openDropdown(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;

        // Close other dropdowns
        this.closeAllDropdowns();
        
        // Open this dropdown
        dropdown.classList.remove('hidden');
        this.activeDropdowns.add(dropdownId);
    }

    closeDropdown(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;

        dropdown.classList.add('hidden');
        this.activeDropdowns.delete(dropdownId);
    }

    closeAllDropdowns() {
        for (const dropdownId of this.activeDropdowns) {
            this.closeDropdown(dropdownId);
        }
    }

    closeDropdownsExcept(target) {
        for (const dropdownId of this.activeDropdowns) {
            const dropdown = document.getElementById(dropdownId);
            const trigger = document.querySelector(`[data-dropdown="${dropdownId}"]`);
            
            if (dropdown && !dropdown.contains(target) && 
                trigger && !trigger.contains(target)) {
                this.closeDropdown(dropdownId);
            }
        }
    }

    // Form helpers
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return null;

        const formData = new FormData(form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    }

    setFormData(formId, data) {
        const form = document.getElementById(formId);
        if (!form) return;

        for (const [key, value] of Object.entries(data)) {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = !!value;
                } else if (field.type === 'radio') {
                    const radioButton = form.querySelector(`[name="${key}"][value="${value}"]`);
                    if (radioButton) radioButton.checked = true;
                } else {
                    field.value = value || '';
                }
            }
        }
    }

    clearForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.reset();
    }

    // Validation helpers
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        // Remove existing error
        this.clearFieldError(fieldId);

        // Add error styling
        field.classList.add('border-red-500', 'focus:ring-red-500');
        field.classList.remove('border-gray-300', 'focus:ring-blue-500');

        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.id = `${fieldId}-error`;
        errorDiv.className = 'text-red-600 text-sm mt-1';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        // Remove error styling
        field.classList.remove('border-red-500', 'focus:ring-red-500');
        field.classList.add('border-gray-300', 'focus:ring-blue-500');

        // Remove error message
        const errorDiv = document.getElementById(`${fieldId}-error`);
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    clearAllFieldErrors(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        const fields = form.querySelectorAll('input, textarea, select');
        fields.forEach(field => {
            if (field.id) {
                this.clearFieldError(field.id);
            }
        });
    }

    // Utility methods
    handleEscapeKey() {
        // Close modals
        this.closeAllModals();
        
        // Close dropdowns
        this.closeAllDropdowns();
    }

    handleWindowResize() {
        // Close dropdowns on resize
        this.closeAllDropdowns();
    }

    openSearch() {
        // Implement search functionality
        console.log('Search opened');
    }

    openHelp() {
        // Implement help functionality
        console.log('Help opened');
    }

    // Animation helpers
    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        const start = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress.toString();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    fadeOut(element, duration = 300) {
        const start = performance.now();
        const startOpacity = parseFloat(element.style.opacity) || 1;
        
        const animate = (currentTime) => {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = (startOpacity * (1 - progress)).toString();
            
            if (progress >= 1) {
                element.style.display = 'none';
            } else {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
}

export default UIManager;
