// Main JavaScript Entry Point
import 'bootstrap';
import '../css/main.css';

// Import utilities and components
import { UIManager } from '@components/ui-manager';
import { NotificationManager } from '@components/notification-manager';
import { LoadingManager } from '@components/loading-manager';
import { FormValidator } from '@components/form-validator';

// Global app configuration
window.ArsaApp = {
  version: '1.1.3',
  debug: process.env.NODE_ENV === 'development',
  apiBaseUrl: '/api',
  
  // Core managers
  ui: null,
  notifications: null,
  loading: null,
  validator: null,
  
  // Initialize the application
  init() {
    console.log(`🚀 Arsa Analiz Platform v${this.version} initializing...`);
    
    // Initialize core managers
    this.ui = new UIManager();
    this.notifications = new NotificationManager();
    this.loading = new LoadingManager();
    this.validator = new FormValidator();
    
    // Initialize components
    this.initializeComponents();
    this.bindGlobalEvents();
    
    console.log('✅ Application initialized successfully');
  },
  
  // Initialize all components
  initializeComponents() {
    // Initialize tooltips
    this.ui.initTooltips();
    
    // Initialize modals
    this.ui.initModals();
    
    // Initialize forms
    this.validator.initForms();
    
    // Initialize navigation
    this.initNavigation();
    
    // Initialize theme
    this.initTheme();
  },
  
  // Bind global event listeners
  bindGlobalEvents() {
    // Handle AJAX errors globally
    document.addEventListener('ajaxError', () => {
      this.notifications.error('Bir hata oluştu. Lütfen tekrar deneyin.');
      this.loading.hide();
    });
    
    // Handle form submissions
    document.addEventListener('submit', (e) => {
      if (e.target.classList.contains('ajax-form')) {
        e.preventDefault();
        this.handleAjaxForm(e.target);
      }
    });
    
    // Handle clicks on elements with data-action
    document.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      if (action && this[action]) {
        e.preventDefault();
        this[action](e.target);
      }
    });
  },
  
  // Initialize navigation
  initNavigation() {
    // Active menu highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
      if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
        // Also activate parent menu if exists
        const parentMenu = link.closest('.nav-item.dropdown');
        if (parentMenu) {
          parentMenu.querySelector('.nav-link').classList.add('active');
        }
      }
    });

    // Mobile sidebar toggle
    this.initMobileSidebar();
  },

  // Initialize mobile sidebar
  initMobileSidebar() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('sidebar-mobile-visible');
        sidebar.classList.toggle('sidebar-mobile-hidden');
      });

      // Close sidebar when clicking outside on mobile
      document.addEventListener('click', (e) => {
        if (window.innerWidth < 1024 &&
            !sidebar.contains(e.target) &&
            !sidebarToggle.contains(e.target) &&
            sidebar.classList.contains('sidebar-mobile-visible')) {
          sidebar.classList.add('sidebar-mobile-hidden');
          sidebar.classList.remove('sidebar-mobile-visible');
        }
      });
    }
  },
  
  // Initialize theme system
  initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.setTheme(savedTheme);
    
    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
      });
    }
  },
  
  // Set theme
  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle icon
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      const icon = themeToggle.querySelector('i');
      if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
      }
    }
  },
  
  // Handle AJAX form submissions
  async handleAjaxForm(form) {
    if (!this.validator.validateForm(form)) {
      return;
    }
    
    this.loading.show();
    
    try {
      const formData = new FormData(form);
      const response = await fetch(form.action, {
        method: form.method || 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      const result = await response.json();
      
      if (result.success) {
        this.notifications.success(result.message || 'İşlem başarıyla tamamlandı');
        
        // Handle redirect
        if (result.redirect) {
          setTimeout(() => {
            window.location.href = result.redirect;
          }, 1000);
        }
        
        // Handle form reset
        if (result.reset_form) {
          form.reset();
        }
        
        // Handle modal close
        if (result.close_modal) {
          const modal = form.closest('.modal');
          if (modal) {
            bootstrap.Modal.getInstance(modal)?.hide();
          }
        }
      } else {
        this.notifications.error(result.message || 'İşlem sırasında bir hata oluştu');
      }
    } catch (error) {
      console.error('Form submission error:', error);
      this.notifications.error('Bağlantı hatası. Lütfen tekrar deneyin.');
    } finally {
      this.loading.hide();
    }
  },
  
  // Utility methods
  utils: {
    // Format currency
    formatCurrency(amount) {
      return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY'
      }).format(amount);
    },
    
    // Format date
    formatDate(date) {
      return new Intl.DateTimeFormat('tr-TR').format(new Date(date));
    },
    
    // Debounce function
    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },
    
    // Generate random ID
    generateId() {
      return Math.random().toString(36).substring(2, 11);
    }
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.ArsaApp.init();
});

// Export for module usage
export default window.ArsaApp;
