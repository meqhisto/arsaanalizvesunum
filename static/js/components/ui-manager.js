// UI Manager - Handles all UI interactions and components
export class UIManager {
  constructor() {
    this.modals = new Map();
    this.tooltips = new Map();
    this.dropdowns = new Map();
  }

  // Initialize tooltips
  initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
      const tooltip = new bootstrap.Tooltip(tooltipTriggerEl);
      this.tooltips.set(tooltipTriggerEl, tooltip);
    });
  }

  // Initialize modals
  initModals() {
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(modalEl => {
      const modal = new bootstrap.Modal(modalEl);
      this.modals.set(modalEl.id, modal);
      
      // Add event listeners
      modalEl.addEventListener('shown.bs.modal', () => {
        // Focus first input when modal opens
        const firstInput = modalEl.querySelector('input, textarea, select');
        if (firstInput) {
          firstInput.focus();
        }
      });
    });
  }

  // Show modal by ID
  showModal(modalId, data = null) {
    const modal = this.modals.get(modalId);
    if (modal) {
      // Populate modal with data if provided
      if (data) {
        this.populateModal(modalId, data);
      }
      modal.show();
    }
  }

  // Hide modal by ID
  hideModal(modalId) {
    const modal = this.modals.get(modalId);
    if (modal) {
      modal.hide();
    }
  }

  // Populate modal with data
  populateModal(modalId, data) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) return;

    Object.keys(data).forEach(key => {
      const element = modalElement.querySelector(`[name="${key}"], #${key}, .${key}`);
      if (element) {
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
          element.value = data[key];
        } else if (element.tagName === 'SELECT') {
          element.value = data[key];
        } else {
          element.textContent = data[key];
        }
      }
    });
  }

  // Create and show confirmation dialog
  showConfirmDialog(options = {}) {
    const defaults = {
      title: 'Onay',
      message: 'Bu işlemi gerçekleştirmek istediğinizden emin misiniz?',
      confirmText: 'Evet',
      cancelText: 'Hayır',
      confirmClass: 'btn-danger',
      onConfirm: () => {},
      onCancel: () => {}
    };

    const config = { ...defaults, ...options };

    // Create modal HTML
    const modalHtml = `
      <div class="modal fade" id="confirmModal" tabindex="-1">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">${config.title}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
              <p>${config.message}</p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                ${config.cancelText}
              </button>
              <button type="button" class="btn ${config.confirmClass}" id="confirmBtn">
                ${config.confirmText}
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Remove existing confirm modal
    const existingModal = document.getElementById('confirmModal');
    if (existingModal) {
      existingModal.remove();
    }

    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Initialize and show modal
    const modalElement = document.getElementById('confirmModal');
    const modal = new bootstrap.Modal(modalElement);

    // Bind events
    const confirmBtn = modalElement.querySelector('#confirmBtn');
    confirmBtn.addEventListener('click', () => {
      config.onConfirm();
      modal.hide();
    });

    modalElement.addEventListener('hidden.bs.modal', () => {
      modalElement.remove();
    });

    modal.show();
  }

  // Show loading overlay
  showLoading(message = 'Yükleniyor...') {
    this.hideLoading(); // Remove existing loading

    const loadingHtml = `
      <div id="loadingOverlay" class="loading-overlay">
        <div class="loading-content">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <div class="loading-text mt-2">${message}</div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', loadingHtml);
  }

  // Hide loading overlay
  hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
      loadingOverlay.remove();
    }
  }

  // Animate element
  animate(element, animation, duration = 1000) {
    return new Promise(resolve => {
      element.style.animationDuration = `${duration}ms`;
      element.classList.add('animate__animated', `animate__${animation}`);

      element.addEventListener('animationend', () => {
        element.classList.remove('animate__animated', `animate__${animation}`);
        resolve();
      }, { once: true });
    });
  }

  // Smooth scroll to element
  scrollTo(element, offset = 0) {
    const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
    if (targetElement) {
      const targetPosition = targetElement.offsetTop - offset;
      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    }
  }

  // Toggle element visibility
  toggle(element, show = null) {
    const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
    if (targetElement) {
      if (show === null) {
        targetElement.classList.toggle('d-none');
      } else {
        targetElement.classList.toggle('d-none', !show);
      }
    }
  }

  // Update element content
  updateContent(selector, content, isHtml = false) {
    const element = document.querySelector(selector);
    if (element) {
      if (isHtml) {
        element.innerHTML = content;
      } else {
        element.textContent = content;
      }
    }
  }

  // Add CSS class with animation
  addClass(element, className, duration = 300) {
    const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
    if (targetElement) {
      targetElement.style.transition = `all ${duration}ms ease`;
      targetElement.classList.add(className);
    }
  }

  // Remove CSS class with animation
  removeClass(element, className, duration = 300) {
    const targetElement = typeof element === 'string' ? document.querySelector(element) : element;
    if (targetElement) {
      targetElement.style.transition = `all ${duration}ms ease`;
      targetElement.classList.remove(className);
    }
  }

  // Create toast notification
  createToast(message, type = 'info', duration = 5000) {
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
      <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
        <div class="d-flex">
          <div class="toast-body">
            ${message}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
    `;

    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
      document.body.appendChild(toastContainer);
    }

    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
      toastElement.remove();
    });

    toast.show();
    return toast;
  }

  // Cleanup method
  destroy() {
    // Dispose of all tooltips
    this.tooltips.forEach(tooltip => tooltip.dispose());
    this.tooltips.clear();

    // Dispose of all modals
    this.modals.forEach(modal => modal.dispose());
    this.modals.clear();

    // Remove loading overlay
    this.hideLoading();
  }
}
