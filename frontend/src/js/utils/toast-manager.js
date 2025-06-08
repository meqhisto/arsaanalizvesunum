// frontend/src/js/utils/toast-manager.js

export class ToastManager {
    constructor() {
        this.toasts = new Map();
        this.container = null;
        this.defaultDuration = 5000;
        this.maxToasts = 5;
        
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(this.container);
        }
    }

    // Show success toast
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    // Show error toast
    error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    // Show warning toast
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    // Show info toast
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    // Show generic toast
    show(message, type = 'info', options = {}) {
        const toastId = this.generateId();
        const duration = options.duration || this.defaultDuration;
        const persistent = options.persistent || false;
        const actions = options.actions || [];

        // Remove oldest toast if we have too many
        if (this.toasts.size >= this.maxToasts) {
            const oldestToastId = this.toasts.keys().next().value;
            this.remove(oldestToastId);
        }

        // Create toast element
        const toast = this.createToastElement(toastId, message, type, actions, persistent);
        
        // Add to container
        this.container.appendChild(toast);
        
        // Store toast reference
        this.toasts.set(toastId, {
            element: toast,
            type,
            message,
            timestamp: Date.now(),
            persistent
        });

        // Animate in
        this.animateIn(toast);

        // Auto-remove if not persistent
        if (!persistent && duration > 0) {
            setTimeout(() => {
                this.remove(toastId);
            }, duration);
        }

        return toastId;
    }

    // Remove toast
    remove(toastId) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        this.animateOut(toast.element, () => {
            if (toast.element.parentNode) {
                toast.element.parentNode.removeChild(toast.element);
            }
            this.toasts.delete(toastId);
        });
    }

    // Remove all toasts
    removeAll() {
        for (const toastId of this.toasts.keys()) {
            this.remove(toastId);
        }
    }

    // Create toast element
    createToastElement(toastId, message, type, actions, persistent) {
        const toast = document.createElement('div');
        toast.id = `toast-${toastId}`;
        toast.className = `toast-item transform transition-all duration-300 ease-in-out translate-x-full opacity-0 max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden`;

        const typeConfig = this.getTypeConfig(type);
        
        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <div class="w-6 h-6 ${typeConfig.iconBg} rounded-full flex items-center justify-center">
                            ${typeConfig.icon}
                        </div>
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                        ${actions.length > 0 ? this.createActionsHTML(actions) : ''}
                    </div>
                    ${!persistent ? `
                        <div class="ml-4 flex-shrink-0 flex">
                            <button class="toast-close bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                <span class="sr-only">Close</span>
                                <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                                </svg>
                            </button>
                        </div>
                    ` : ''}
                </div>
            </div>
            ${!persistent ? `<div class="toast-progress bg-gray-200 h-1"><div class="toast-progress-bar bg-${typeConfig.color}-500 h-full transition-all duration-${this.defaultDuration} ease-linear w-full"></div></div>` : ''}
        `;

        // Add event listeners
        this.addToastEventListeners(toast, toastId);

        return toast;
    }

    // Get type configuration
    getTypeConfig(type) {
        const configs = {
            success: {
                icon: '<svg class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>',
                iconBg: 'bg-green-100',
                color: 'green'
            },
            error: {
                icon: '<svg class="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>',
                iconBg: 'bg-red-100',
                color: 'red'
            },
            warning: {
                icon: '<svg class="w-4 h-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>',
                iconBg: 'bg-yellow-100',
                color: 'yellow'
            },
            info: {
                icon: '<svg class="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>',
                iconBg: 'bg-blue-100',
                color: 'blue'
            }
        };

        return configs[type] || configs.info;
    }

    // Create actions HTML
    createActionsHTML(actions) {
        return `
            <div class="mt-3 flex space-x-2">
                ${actions.map(action => `
                    <button class="toast-action bg-white px-2 py-1 text-sm font-medium text-${action.color || 'indigo'}-600 hover:text-${action.color || 'indigo'}-500 border border-transparent rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-${action.color || 'indigo'}-500" data-action="${action.id}">
                        ${action.text}
                    </button>
                `).join('')}
            </div>
        `;
    }

    // Add event listeners to toast
    addToastEventListeners(toast, toastId) {
        // Close button
        const closeButton = toast.querySelector('.toast-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.remove(toastId);
            });
        }

        // Action buttons
        const actionButtons = toast.querySelectorAll('.toast-action');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const actionId = e.target.getAttribute('data-action');
                this.handleAction(toastId, actionId);
            });
        });

        // Progress bar animation
        const progressBar = toast.querySelector('.toast-progress-bar');
        if (progressBar) {
            // Start progress animation
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 100);
        }
    }

    // Handle action click
    handleAction(toastId, actionId) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        // Emit custom event
        const event = new CustomEvent('toast-action', {
            detail: { toastId, actionId, toast }
        });
        document.dispatchEvent(event);

        // Remove toast after action
        this.remove(toastId);
    }

    // Animate toast in
    animateIn(toast) {
        // Force reflow
        toast.offsetHeight;
        
        // Animate in
        toast.classList.remove('translate-x-full', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    }

    // Animate toast out
    animateOut(toast, callback) {
        toast.classList.remove('translate-x-0', 'opacity-100');
        toast.classList.add('translate-x-full', 'opacity-0');
        
        setTimeout(() => {
            if (callback) callback();
        }, 300);
    }

    // Generate unique ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Get toast count
    getCount() {
        return this.toasts.size;
    }

    // Get toast by ID
    getToast(toastId) {
        return this.toasts.get(toastId);
    }

    // Update toast message
    updateMessage(toastId, newMessage) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        const messageElement = toast.element.querySelector('.text-sm.font-medium');
        if (messageElement) {
            messageElement.textContent = newMessage;
            toast.message = newMessage;
        }
    }
}

export default ToastManager;
