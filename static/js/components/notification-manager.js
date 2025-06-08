// Notification Manager - Handles all types of notifications
export class NotificationManager {
  constructor() {
    this.container = null;
    this.notifications = new Map();
    this.defaultDuration = 5000;
    this.maxNotifications = 5;
    
    this.init();
  }

  // Initialize notification system
  init() {
    this.createContainer();
    this.bindEvents();
  }

  // Create notification container
  createContainer() {
    if (this.container) return;

    this.container = document.createElement('div');
    this.container.id = 'notification-container';
    this.container.className = 'notification-container position-fixed top-0 end-0 p-3';
    this.container.style.zIndex = '9999';
    
    document.body.appendChild(this.container);
  }

  // Bind global events
  bindEvents() {
    // Listen for custom notification events
    document.addEventListener('notification', (e) => {
      const { type, message, options } = e.detail;
      this[type](message, options);
    });
  }

  // Show success notification
  success(message, options = {}) {
    return this.show(message, 'success', {
      icon: 'fas fa-check-circle',
      ...options
    });
  }

  // Show error notification
  error(message, options = {}) {
    return this.show(message, 'danger', {
      icon: 'fas fa-exclamation-circle',
      duration: 8000, // Errors stay longer
      ...options
    });
  }

  // Show warning notification
  warning(message, options = {}) {
    return this.show(message, 'warning', {
      icon: 'fas fa-exclamation-triangle',
      ...options
    });
  }

  // Show info notification
  info(message, options = {}) {
    return this.show(message, 'info', {
      icon: 'fas fa-info-circle',
      ...options
    });
  }

  // Show custom notification
  show(message, type = 'info', options = {}) {
    const config = {
      duration: this.defaultDuration,
      closable: true,
      icon: null,
      title: null,
      actions: [],
      persistent: false,
      ...options
    };

    // Limit number of notifications
    if (this.notifications.size >= this.maxNotifications) {
      const oldestId = this.notifications.keys().next().value;
      this.hide(oldestId);
    }

    const notificationId = this.generateId();
    const notification = this.createNotification(notificationId, message, type, config);
    
    this.container.appendChild(notification);
    this.notifications.set(notificationId, {
      element: notification,
      config: config
    });

    // Animate in
    requestAnimationFrame(() => {
      notification.classList.add('show');
    });

    // Auto-hide if not persistent
    if (!config.persistent && config.duration > 0) {
      setTimeout(() => {
        this.hide(notificationId);
      }, config.duration);
    }

    return notificationId;
  }

  // Create notification element
  createNotification(id, message, type, config) {
    const notification = document.createElement('div');
    notification.id = `notification-${id}`;
    notification.className = `notification alert alert-${type} alert-dismissible fade`;
    notification.setAttribute('role', 'alert');

    let iconHtml = '';
    if (config.icon) {
      iconHtml = `<i class="${config.icon} me-2"></i>`;
    }

    let titleHtml = '';
    if (config.title) {
      titleHtml = `<div class="notification-title fw-bold">${config.title}</div>`;
    }

    let actionsHtml = '';
    if (config.actions && config.actions.length > 0) {
      const actionButtons = config.actions.map(action => 
        `<button type="button" class="btn btn-sm btn-outline-${type} me-2" data-action="${action.action}">
          ${action.text}
        </button>`
      ).join('');
      
      actionsHtml = `<div class="notification-actions mt-2">${actionButtons}</div>`;
    }

    let closeButtonHtml = '';
    if (config.closable) {
      closeButtonHtml = `
        <button type="button" class="btn-close" data-notification-id="${id}"></button>
      `;
    }

    notification.innerHTML = `
      <div class="d-flex align-items-start">
        <div class="flex-grow-1">
          ${iconHtml}${titleHtml}
          <div class="notification-message">${message}</div>
          ${actionsHtml}
        </div>
        ${closeButtonHtml}
      </div>
    `;

    // Bind events
    this.bindNotificationEvents(notification, id, config);

    return notification;
  }

  // Bind notification-specific events
  bindNotificationEvents(notification, id, config) {
    // Close button
    const closeBtn = notification.querySelector('.btn-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.hide(id);
      });
    }

    // Action buttons
    const actionButtons = notification.querySelectorAll('[data-action]');
    actionButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const actionName = e.target.dataset.action;
        const action = config.actions.find(a => a.action === actionName);
        
        if (action && action.handler) {
          action.handler(id, notification);
        }

        // Hide notification after action unless specified otherwise
        if (!action.keepOpen) {
          this.hide(id);
        }
      });
    });

    // Auto-hide on click (if configured)
    if (config.clickToClose) {
      notification.addEventListener('click', () => {
        this.hide(id);
      });
    }
  }

  // Hide notification
  hide(notificationId) {
    const notificationData = this.notifications.get(notificationId);
    if (!notificationData) return;

    const { element } = notificationData;
    
    // Animate out
    element.classList.remove('show');
    element.classList.add('hiding');

    // Remove after animation
    setTimeout(() => {
      if (element.parentNode) {
        element.parentNode.removeChild(element);
      }
      this.notifications.delete(notificationId);
    }, 300);
  }

  // Hide all notifications
  hideAll() {
    this.notifications.forEach((_, id) => {
      this.hide(id);
    });
  }

  // Show loading notification
  showLoading(message = 'İşlem devam ediyor...', options = {}) {
    return this.show(message, 'info', {
      icon: 'fas fa-spinner fa-spin',
      persistent: true,
      closable: false,
      ...options
    });
  }

  // Show progress notification
  showProgress(message, progress = 0, options = {}) {
    const progressHtml = `
      <div class="progress mt-2" style="height: 6px;">
        <div class="progress-bar" role="progressbar" style="width: ${progress}%"></div>
      </div>
    `;

    return this.show(message + progressHtml, 'info', {
      persistent: true,
      closable: false,
      ...options
    });
  }

  // Update progress notification
  updateProgress(notificationId, progress, message = null) {
    const notificationData = this.notifications.get(notificationId);
    if (!notificationData) return;

    const { element } = notificationData;
    const progressBar = element.querySelector('.progress-bar');
    
    if (progressBar) {
      progressBar.style.width = `${progress}%`;
    }

    if (message) {
      const messageElement = element.querySelector('.notification-message');
      if (messageElement) {
        // Extract message without progress bar HTML
        const messageText = message.split('<div class="progress')[0];
        messageElement.innerHTML = messageText + progressBar.parentElement.outerHTML;
      }
    }

    // Auto-hide when complete
    if (progress >= 100) {
      setTimeout(() => {
        this.hide(notificationId);
      }, 2000);
    }
  }

  // Show confirmation notification with actions
  confirm(message, options = {}) {
    const config = {
      title: 'Onay Gerekli',
      type: 'warning',
      persistent: true,
      actions: [
        {
          text: 'İptal',
          action: 'cancel',
          handler: options.onCancel || (() => {})
        },
        {
          text: 'Onayla',
          action: 'confirm',
          handler: options.onConfirm || (() => {})
        }
      ],
      ...options
    };

    return this.show(message, config.type, config);
  }

  // Generate unique ID
  generateId() {
    return Math.random().toString(36).substr(2, 9);
  }

  // Get notification count
  getCount() {
    return this.notifications.size;
  }

  // Check if notification exists
  exists(notificationId) {
    return this.notifications.has(notificationId);
  }

  // Destroy notification manager
  destroy() {
    this.hideAll();
    
    if (this.container && this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    
    this.notifications.clear();
  }
}
