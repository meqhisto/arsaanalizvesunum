// Admin Module - Handles admin-specific functionality
import { UIManager } from '@components/ui-manager';
import { NotificationManager } from '@components/notification-manager';
import { LoadingManager } from '@components/loading-manager';

class AdminManager {
  constructor() {
    this.ui = new UIManager();
    this.notifications = new NotificationManager();
    this.loading = new LoadingManager();
    this.currentUser = null;
    this.currentOffice = null;
    
    this.init();
  }

  init() {
    this.bindEvents();
    this.loadDashboardStats();
    this.initializeDataTables();
  }

  bindEvents() {
    // User management
    document.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      
      switch (action) {
        case 'add-user':
          this.showUserModal();
          break;
        case 'edit-user':
          this.editUser(e.target.dataset.userId);
          break;
        case 'delete-user':
          this.deleteUser(e.target.dataset.userId);
          break;
        case 'toggle-user-status':
          this.toggleUserStatus(e.target.dataset.userId);
          break;
        case 'reset-password':
          this.resetUserPassword(e.target.dataset.userId);
          break;
        case 'add-office':
          this.showOfficeModal();
          break;
        case 'edit-office':
          this.editOffice(e.target.dataset.officeId);
          break;
        case 'delete-office':
          this.deleteOffice(e.target.dataset.officeId);
          break;
        case 'view-logs':
          this.viewSystemLogs();
          break;
        case 'backup-database':
          this.backupDatabase();
          break;
        case 'export-data':
          this.exportData(e.target.dataset.type);
          break;
      }
    });

    // Form submissions
    document.addEventListener('submit', (e) => {
      const formId = e.target.id;
      
      switch (formId) {
        case 'userForm':
          e.preventDefault();
          this.handleUserSubmission(e.target);
          break;
        case 'officeForm':
          e.preventDefault();
          this.handleOfficeSubmission(e.target);
          break;
        case 'settingsForm':
          e.preventDefault();
          this.handleSettingsSubmission(e.target);
          break;
      }
    });

    // Search functionality
    const userSearch = document.getElementById('userSearch');
    if (userSearch) {
      userSearch.addEventListener('input', this.debounce((e) => {
        this.searchUsers(e.target.value);
      }, 300));
    }
  }

  // Show user modal
  showUserModal(userId = null) {
    const modal = document.getElementById('userModal');
    if (!modal) return;

    if (userId) {
      this.loadUserData(userId);
    } else {
      this.resetUserForm();
    }

    this.ui.showModal('userModal');
  }

  // Handle user form submission
  async handleUserSubmission(form) {
    if (!this.validateUserForm(form)) {
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    this.loading.showButtonLoading(submitBtn, { text: 'Kaydediliyor...' });

    try {
      const formData = new FormData(form);
      const userId = form.querySelector('[name="user_id"]')?.value;
      const url = userId ? `/admin/users/${userId}/update` : '/admin/users/create';
      
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.notifications.success(userId ? 'Kullanıcı güncellendi' : 'Kullanıcı eklendi');
        this.ui.hideModal('userModal');
        this.refreshUsersList();
      } else {
        this.notifications.error(result.message || 'İşlem başarısız');
      }
    } catch (error) {
      console.error('User submission error:', error);
      this.notifications.error('Bağlantı hatası');
    } finally {
      this.loading.hideButtonLoading(submitBtn);
    }
  }

  // Validate user form
  validateUserForm(form) {
    const requiredFields = ['username', 'email', 'role'];
    let isValid = true;

    // Check if it's a new user (password required)
    const userId = form.querySelector('[name="user_id"]')?.value;
    if (!userId) {
      requiredFields.push('password');
    }

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

    // Password validation for new users
    const passwordField = form.querySelector('[name="password"]');
    if (passwordField && passwordField.value && passwordField.value.length < 6) {
      this.notifications.warning('Şifre en az 6 karakter olmalıdır');
      passwordField.focus();
      isValid = false;
    }

    return isValid;
  }

  // Toggle user status
  async toggleUserStatus(userId) {
    this.ui.showConfirmDialog({
      title: 'Kullanıcı Durumu',
      message: 'Kullanıcının durumunu değiştirmek istediğinizden emin misiniz?',
      onConfirm: async () => {
        this.loading.show('Durum güncelleniyor...');

        try {
          const response = await fetch(`/admin/users/${userId}/toggle-status`, {
            method: 'POST',
            headers: {
              'X-Requested-With': 'XMLHttpRequest'
            }
          });

          const result = await response.json();

          if (result.success) {
            this.notifications.success('Kullanıcı durumu güncellendi');
            this.refreshUsersList();
          } else {
            this.notifications.error('Durum güncellenemedi');
          }
        } catch (error) {
          console.error('Status toggle error:', error);
          this.notifications.error('Bağlantı hatası');
        } finally {
          this.loading.hide();
        }
      }
    });
  }

  // Reset user password
  async resetUserPassword(userId) {
    this.ui.showConfirmDialog({
      title: 'Şifre Sıfırlama',
      message: 'Kullanıcının şifresini sıfırlamak istediğinizden emin misiniz? Yeni şifre e-posta ile gönderilecektir.',
      onConfirm: async () => {
        this.loading.show('Şifre sıfırlanıyor...');

        try {
          const response = await fetch(`/admin/users/${userId}/reset-password`, {
            method: 'POST',
            headers: {
              'X-Requested-With': 'XMLHttpRequest'
            }
          });

          const result = await response.json();

          if (result.success) {
            this.notifications.success('Şifre sıfırlandı ve e-posta gönderildi');
          } else {
            this.notifications.error('Şifre sıfırlanamadı');
          }
        } catch (error) {
          console.error('Password reset error:', error);
          this.notifications.error('Bağlantı hatası');
        } finally {
          this.loading.hide();
        }
      }
    });
  }

  // Load dashboard stats
  async loadDashboardStats() {
    const statsContainer = document.getElementById('adminStats');
    if (!statsContainer) return;

    this.loading.showSkeleton(statsContainer, {
      rows: 2,
      columns: 4,
      height: '80px',
      width: ['100%', '100%', '100%', '100%']
    });

    try {
      const response = await fetch('/admin/dashboard-stats', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.renderDashboardStats(result.data);
      }
    } catch (error) {
      console.error('Dashboard stats loading error:', error);
    } finally {
      this.loading.hideSkeleton(statsContainer);
    }
  }

  // Render dashboard stats
  renderDashboardStats(stats) {
    const container = document.getElementById('adminStats');
    if (!container) return;

    container.innerHTML = `
      <div class="row">
        <div class="col-md-3 mb-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <i class="fas fa-users fa-2x text-primary mb-2"></i>
              <h3 class="text-primary">${stats.total_users}</h3>
              <small class="text-muted">Toplam Kullanıcı</small>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <i class="fas fa-building fa-2x text-success mb-2"></i>
              <h3 class="text-success">${stats.total_offices}</h3>
              <small class="text-muted">Toplam Ofis</small>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <i class="fas fa-chart-line fa-2x text-info mb-2"></i>
              <h3 class="text-info">${stats.total_analyses}</h3>
              <small class="text-muted">Toplam Analiz</small>
            </div>
          </div>
        </div>
        <div class="col-md-3 mb-3">
          <div class="card card-modern text-center">
            <div class="card-body">
              <i class="fas fa-user-check fa-2x text-warning mb-2"></i>
              <h3 class="text-warning">${stats.active_users}</h3>
              <small class="text-muted">Aktif Kullanıcı</small>
            </div>
          </div>
        </div>
      </div>
      
      <div class="row mt-4">
        <div class="col-md-6">
          <div class="card card-modern">
            <div class="card-header">
              <h6 class="mb-0">Son Aktiviteler</h6>
            </div>
            <div class="card-body">
              <div class="list-group list-group-flush">
                ${stats.recent_activities.map(activity => `
                  <div class="list-group-item border-0 px-0">
                    <div class="d-flex justify-content-between align-items-start">
                      <div>
                        <small class="text-muted">${activity.user}</small>
                        <div>${activity.action}</div>
                      </div>
                      <small class="text-muted">${this.formatDate(activity.created_at)}</small>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card card-modern">
            <div class="card-header">
              <h6 class="mb-0">Sistem Durumu</h6>
            </div>
            <div class="card-body">
              <div class="row">
                <div class="col-6">
                  <div class="text-center">
                    <div class="text-success">
                      <i class="fas fa-check-circle fa-2x"></i>
                    </div>
                    <small class="text-muted">Veritabanı</small>
                  </div>
                </div>
                <div class="col-6">
                  <div class="text-center">
                    <div class="text-success">
                      <i class="fas fa-check-circle fa-2x"></i>
                    </div>
                    <small class="text-muted">Sunucu</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Export data
  async exportData(type) {
    this.loading.show(`${type} verileri dışa aktarılıyor...`);

    try {
      const response = await fetch(`/admin/export/${type}`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${type}_export_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        this.notifications.success('Veriler başarıyla dışa aktarıldı');
      } else {
        this.notifications.error('Dışa aktarma başarısız');
      }
    } catch (error) {
      console.error('Export error:', error);
      this.notifications.error('Dışa aktarma hatası');
    } finally {
      this.loading.hide();
    }
  }

  // View system logs
  async viewSystemLogs() {
    const modal = document.getElementById('logsModal');
    if (!modal) return;

    this.ui.showModal('logsModal');
    
    const logsContainer = modal.querySelector('.logs-content');
    this.loading.showSkeleton(logsContainer, {
      rows: 10,
      height: '30px'
    });

    try {
      const response = await fetch('/admin/logs', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        logsContainer.innerHTML = `
          <pre class="bg-dark text-light p-3 rounded" style="max-height: 400px; overflow-y: auto;">
            ${result.data.logs}
          </pre>
        `;
      }
    } catch (error) {
      console.error('Logs loading error:', error);
    } finally {
      this.loading.hideSkeleton(logsContainer);
    }
  }

  // Initialize data tables
  initializeDataTables() {
    // DataTables initialization for admin tables
    const tables = document.querySelectorAll('.admin-table');
    tables.forEach(table => {
      // Initialize DataTable if available
      if (typeof $ !== 'undefined' && $.fn.DataTable) {
        $(table).DataTable({
          responsive: true,
          language: {
            url: '//cdn.datatables.net/plug-ins/1.10.24/i18n/Turkish.json'
          }
        });
      }
    });
  }

  // Utility methods
  formatDate(dateString) {
    return new Intl.DateTimeFormat('tr-TR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
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

  // Placeholder methods for missing functionality
  loadUserData(userId) {
    // Load user data for editing
  }

  resetUserForm() {
    // Reset user form
  }

  refreshUsersList() {
    // Refresh users list
  }

  searchUsers(query) {
    // Search users
  }

  showOfficeModal(officeId = null) {
    // Show office modal
  }

  editOffice(officeId) {
    // Edit office
  }

  deleteOffice(officeId) {
    // Delete office
  }

  handleOfficeSubmission(form) {
    // Handle office form submission
  }

  handleSettingsSubmission(form) {
    // Handle settings form submission
  }

  backupDatabase() {
    // Backup database
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.body.classList.contains('admin-page')) {
    window.AdminManager = new AdminManager();
  }
});

export default AdminManager;
