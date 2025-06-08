// CRM Module - Handles CRM-specific functionality
import { UIManager } from '@components/ui-manager';
import { NotificationManager } from '@components/notification-manager';
import { LoadingManager } from '@components/loading-manager';

class CRMManager {
  constructor() {
    this.ui = new UIManager();
    this.notifications = new NotificationManager();
    this.loading = new LoadingManager();
    this.currentContact = null;
    this.currentDeal = null;
    this.filters = {
      status: 'all',
      assignee: 'all',
      dateRange: 'all'
    };
    
    this.init();
  }

  init() {
    this.bindEvents();
    this.initializeFilters();
    this.loadDashboardData();
  }

  bindEvents() {
    // Contact management
    document.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      
      switch (action) {
        case 'add-contact':
          this.showContactModal();
          break;
        case 'edit-contact':
          this.editContact(e.target.dataset.contactId);
          break;
        case 'delete-contact':
          this.deleteContact(e.target.dataset.contactId);
          break;
        case 'add-deal':
          this.showDealModal(e.target.dataset.contactId);
          break;
        case 'edit-deal':
          this.editDeal(e.target.dataset.dealId);
          break;
        case 'update-deal-status':
          this.updateDealStatus(e.target.dataset.dealId, e.target.dataset.status);
          break;
        case 'add-task':
          this.showTaskModal(e.target.dataset.contactId, e.target.dataset.dealId);
          break;
        case 'complete-task':
          this.completeTask(e.target.dataset.taskId);
          break;
        case 'add-note':
          this.showNoteModal(e.target.dataset.contactId);
          break;
        case 'send-email':
          this.showEmailModal(e.target.dataset.contactId);
          break;
      }
    });

    // Form submissions
    document.addEventListener('submit', (e) => {
      const formId = e.target.id;
      
      switch (formId) {
        case 'contactForm':
          e.preventDefault();
          this.handleContactSubmission(e.target);
          break;
        case 'dealForm':
          e.preventDefault();
          this.handleDealSubmission(e.target);
          break;
        case 'taskForm':
          e.preventDefault();
          this.handleTaskSubmission(e.target);
          break;
        case 'noteForm':
          e.preventDefault();
          this.handleNoteSubmission(e.target);
          break;
      }
    });

    // Search functionality
    const searchInput = document.getElementById('crmSearch');
    if (searchInput) {
      searchInput.addEventListener('input', this.debounce((e) => {
        this.performSearch(e.target.value);
      }, 300));
    }

    // Filter changes
    document.addEventListener('change', (e) => {
      if (e.target.classList.contains('crm-filter')) {
        this.updateFilters();
      }
    });
  }

  // Show contact modal
  showContactModal(contactId = null) {
    const modal = document.getElementById('contactModal');
    if (!modal) return;

    if (contactId) {
      this.loadContactData(contactId);
    } else {
      this.resetContactForm();
    }

    this.ui.showModal('contactModal');
  }

  // Handle contact form submission
  async handleContactSubmission(form) {
    if (!this.validateContactForm(form)) {
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    this.loading.showButtonLoading(submitBtn, { text: 'Kaydediliyor...' });

    try {
      const formData = new FormData(form);
      const contactId = form.querySelector('[name="contact_id"]')?.value;
      const url = contactId ? `/crm/contacts/${contactId}/update` : '/crm/contacts/create';
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.notifications.success(contactId ? 'Kişi güncellendi' : 'Kişi eklendi');
        this.ui.hideModal('contactModal');
        this.refreshContactsList();
      } else {
        this.notifications.error(result.message || 'İşlem başarısız');
      }
    } catch (error) {
      console.error('Contact submission error:', error);
      this.notifications.error('Bağlantı hatası');
    } finally {
      this.loading.hideButtonLoading(submitBtn);
    }
  }

  // Validate contact form
  validateContactForm(form) {
    const requiredFields = ['ad', 'soyad', 'telefon'];
    let isValid = true;

    requiredFields.forEach(fieldName => {
      const field = form.querySelector(`[name="${fieldName}"]`);
      if (field && !field.value.trim()) {
        this.notifications.warning(`${field.placeholder || fieldName} alanı zorunludur`);
        field.focus();
        isValid = false;
        return false;
      }
    });

    // Email validation
    const emailField = form.querySelector('[name="email"]');
    if (emailField && emailField.value) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(emailField.value)) {
        this.notifications.warning('Geçerli bir e-posta adresi giriniz');
        emailField.focus();
        isValid = false;
      }
    }

    return isValid;
  }

  // Show deal modal
  showDealModal(contactId = null, dealId = null) {
    const modal = document.getElementById('dealModal');
    if (!modal) return;

    if (dealId) {
      this.loadDealData(dealId);
    } else {
      this.resetDealForm();
      if (contactId) {
        const contactField = modal.querySelector('[name="contact_id"]');
        if (contactField) contactField.value = contactId;
      }
    }

    this.ui.showModal('dealModal');
  }

  // Handle deal submission
  async handleDealSubmission(form) {
    if (!this.validateDealForm(form)) {
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    this.loading.showButtonLoading(submitBtn, { text: 'Kaydediliyor...' });

    try {
      const formData = new FormData(form);
      const dealId = form.querySelector('[name="deal_id"]')?.value;
      const url = dealId ? `/crm/deals/${dealId}/update` : '/crm/deals/create';
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.notifications.success(dealId ? 'Fırsat güncellendi' : 'Fırsat eklendi');
        this.ui.hideModal('dealModal');
        this.refreshDealsList();
      } else {
        this.notifications.error(result.message || 'İşlem başarısız');
      }
    } catch (error) {
      console.error('Deal submission error:', error);
      this.notifications.error('Bağlantı hatası');
    } finally {
      this.loading.hideButtonLoading(submitBtn);
    }
  }

  // Validate deal form
  validateDealForm(form) {
    const requiredFields = ['baslik', 'deger', 'contact_id'];
    let isValid = true;

    requiredFields.forEach(fieldName => {
      const field = form.querySelector(`[name="${fieldName}"]`);
      if (field && !field.value.trim()) {
        this.notifications.warning(`${field.placeholder || fieldName} alanı zorunludur`);
        field.focus();
        isValid = false;
        return false;
      }
    });

    return isValid;
  }

  // Update deal status
  async updateDealStatus(dealId, newStatus) {
    this.loading.show('Durum güncelleniyor...');

    try {
      const response = await fetch(`/crm/deals/${dealId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ status: newStatus })
      });

      const result = await response.json();

      if (result.success) {
        this.notifications.success('Durum güncellendi');
        this.refreshDealsList();
      } else {
        this.notifications.error('Durum güncellenemedi');
      }
    } catch (error) {
      console.error('Status update error:', error);
      this.notifications.error('Bağlantı hatası');
    } finally {
      this.loading.hide();
    }
  }

  // Perform search
  async performSearch(query) {
    if (query.length < 2) {
      this.loadDashboardData();
      return;
    }

    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;

    this.loading.showSkeleton(resultsContainer, {
      rows: 3,
      height: '50px'
    });

    try {
      const response = await fetch(`/crm/search?q=${encodeURIComponent(query)}`, {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.renderSearchResults(result.data);
      }
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      this.loading.hideSkeleton(resultsContainer);
    }
  }

  // Render search results
  renderSearchResults(results) {
    const container = document.getElementById('searchResults');
    if (!container) return;

    if (results.contacts.length === 0 && results.deals.length === 0) {
      container.innerHTML = `
        <div class="text-center py-3">
          <i class="fas fa-search fa-2x text-muted mb-2"></i>
          <p class="text-muted">Sonuç bulunamadı</p>
        </div>
      `;
      return;
    }

    let html = '';

    if (results.contacts.length > 0) {
      html += '<h6>Kişiler</h6>';
      results.contacts.forEach(contact => {
        html += `
          <div class="card card-modern mb-2">
            <div class="card-body py-2">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <strong>${contact.ad} ${contact.soyad}</strong>
                  <br><small class="text-muted">${contact.telefon}</small>
                </div>
                <button class="btn btn-sm btn-outline-primary" data-action="edit-contact" data-contact-id="${contact.id}">
                  <i class="fas fa-edit"></i>
                </button>
              </div>
            </div>
          </div>
        `;
      });
    }

    if (results.deals.length > 0) {
      html += '<h6 class="mt-3">Fırsatlar</h6>';
      results.deals.forEach(deal => {
        html += `
          <div class="card card-modern mb-2">
            <div class="card-body py-2">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <strong>${deal.baslik}</strong>
                  <br><small class="text-muted">${this.formatCurrency(deal.deger)}</small>
                </div>
                <span class="badge bg-${this.getStatusColor(deal.durum)}">${deal.durum}</span>
              </div>
            </div>
          </div>
        `;
      });
    }

    container.innerHTML = html;
  }

  // Load dashboard data
  async loadDashboardData() {
    const dashboardContainer = document.getElementById('crmDashboard');
    if (!dashboardContainer) return;

    this.loading.showSkeleton(dashboardContainer, {
      rows: 4,
      height: '80px'
    });

    try {
      const response = await fetch('/crm/dashboard-data', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.renderDashboard(result.data);
      }
    } catch (error) {
      console.error('Dashboard loading error:', error);
    } finally {
      this.loading.hideSkeleton(dashboardContainer);
    }
  }

  // Render dashboard
  renderDashboard(data) {
    const container = document.getElementById('crmDashboard');
    if (!container) return;

    const { stats, recent_contacts, recent_deals, tasks } = data;

    container.innerHTML = `
      <div class="row mb-4">
        <div class="col-md-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <h3 class="text-primary">${stats.total_contacts}</h3>
              <small class="text-muted">Toplam Kişi</small>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <h3 class="text-success">${stats.active_deals}</h3>
              <small class="text-muted">Aktif Fırsat</small>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <h3 class="text-info">${this.formatCurrency(stats.total_value)}</h3>
              <small class="text-muted">Toplam Değer</small>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <h3 class="text-warning">${stats.pending_tasks}</h3>
              <small class="text-muted">Bekleyen Görev</small>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Utility methods
  formatCurrency(amount) {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount);
  }

  getStatusColor(status) {
    const colors = {
      'Yeni': 'primary',
      'Devam Ediyor': 'warning',
      'Kazanıldı': 'success',
      'Kaybedildi': 'danger'
    };
    return colors[status] || 'secondary';
  }

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
  }

  // Initialize filters
  initializeFilters() {
    // Filter initialization logic
  }

  // Update filters
  updateFilters() {
    // Filter update logic
  }

  // Refresh lists
  refreshContactsList() {
    // Refresh contacts list
  }

  refreshDealsList() {
    // Refresh deals list
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.body.classList.contains('crm-page')) {
    window.CRMManager = new CRMManager();
  }
});

export default CRMManager;
