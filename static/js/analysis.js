// Analysis Module - Handles analysis-specific functionality
import { UIManager } from '@components/ui-manager';
import { NotificationManager } from '@components/notification-manager';
import { LoadingManager } from '@components/loading-manager';

class AnalysisManager {
  constructor() {
    this.ui = new UIManager();
    this.notifications = new NotificationManager();
    this.loading = new LoadingManager();
    this.currentAnalysis = null;
    this.charts = new Map();
    
    this.init();
  }

  init() {
    this.bindEvents();
    this.initializeCharts();
    this.loadAnalysisList();
  }

  bindEvents() {
    // Analysis form submission
    document.addEventListener('submit', (e) => {
      if (e.target.id === 'analysisForm') {
        e.preventDefault();
        this.handleAnalysisSubmission(e.target);
      }
    });

    // Analysis actions
    document.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      
      switch (action) {
        case 'view-analysis':
          this.viewAnalysis(e.target.dataset.analysisId);
          break;
        case 'edit-analysis':
          this.editAnalysis(e.target.dataset.analysisId);
          break;
        case 'delete-analysis':
          this.deleteAnalysis(e.target.dataset.analysisId);
          break;
        case 'generate-report':
          this.generateReport(e.target.dataset.analysisId, e.target.dataset.format);
          break;
        case 'calculate-price':
          this.calculatePrice();
          break;
        case 'run-swot':
          this.runSwotAnalysis();
          break;
      }
    });

    // Real-time price calculation
    const priceInputs = document.querySelectorAll('.price-input');
    priceInputs.forEach(input => {
      input.addEventListener('input', this.debounce(() => {
        this.calculatePrice();
      }, 500));
    });

    // SWOT analysis inputs
    const swotInputs = document.querySelectorAll('.swot-input');
    swotInputs.forEach(input => {
      input.addEventListener('change', () => {
        this.updateSwotScore();
      });
    });
  }

  // Handle analysis form submission
  async handleAnalysisSubmission(form) {
    if (!this.validateAnalysisForm(form)) {
      return;
    }

    this.loading.show('Analiz kaydediliyor...');

    try {
      const formData = new FormData(form);
      const response = await fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.notifications.success('Analiz başarıyla kaydedildi');
        
        // Update analysis list
        this.loadAnalysisList();
        
        // Redirect to analysis detail
        if (result.analysis_id) {
          setTimeout(() => {
            window.location.href = `/analysis/detail/${result.analysis_id}`;
          }, 1000);
        }
      } else {
        this.notifications.error(result.message || 'Analiz kaydedilemedi');
      }
    } catch (error) {
      console.error('Analysis submission error:', error);
      this.notifications.error('Bağlantı hatası. Lütfen tekrar deneyin.');
    } finally {
      this.loading.hide();
    }
  }

  // Validate analysis form
  validateAnalysisForm(form) {
    const requiredFields = ['arsa_adi', 'il', 'ilce', 'alan_m2'];
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

  // Calculate price estimation
  async calculatePrice() {
    const form = document.getElementById('analysisForm');
    if (!form) return;

    const formData = new FormData(form);
    const priceContainer = document.getElementById('priceEstimation');
    
    if (!priceContainer) return;

    this.loading.showOnElement(priceContainer, {
      message: 'Fiyat hesaplanıyor...',
      size: 'sm'
    });

    try {
      const response = await fetch('/analysis/calculate-price', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.updatePriceDisplay(result.data);
      } else {
        this.notifications.warning('Fiyat hesaplanamadı');
      }
    } catch (error) {
      console.error('Price calculation error:', error);
    } finally {
      this.loading.hideOnElement(priceContainer);
    }
  }

  // Update price display
  updatePriceDisplay(priceData) {
    const container = document.getElementById('priceEstimation');
    if (!container) return;

    const { estimated_price, confidence, price_range } = priceData;

    container.innerHTML = `
      <div class="card card-modern">
        <div class="card-header">
          <h6 class="mb-0">Fiyat Tahmini</h6>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-4">
              <div class="text-center">
                <h4 class="text-primary">${this.formatCurrency(estimated_price)}</h4>
                <small class="text-muted">Tahmini Değer</small>
              </div>
            </div>
            <div class="col-md-4">
              <div class="text-center">
                <h5 class="text-success">%${confidence}</h5>
                <small class="text-muted">Güven Oranı</small>
              </div>
            </div>
            <div class="col-md-4">
              <div class="text-center">
                <small class="text-muted">Fiyat Aralığı</small>
                <div>${this.formatCurrency(price_range.min)} - ${this.formatCurrency(price_range.max)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Run SWOT analysis
  async runSwotAnalysis() {
    const form = document.getElementById('analysisForm');
    if (!form) return;

    const swotContainer = document.getElementById('swotAnalysis');
    if (!swotContainer) return;

    this.loading.showOnElement(swotContainer, {
      message: 'SWOT analizi yapılıyor...'
    });

    try {
      const formData = new FormData(form);
      const response = await fetch('/analysis/swot-analysis', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.updateSwotDisplay(result.data);
      } else {
        this.notifications.warning('SWOT analizi yapılamadı');
      }
    } catch (error) {
      console.error('SWOT analysis error:', error);
    } finally {
      this.loading.hideOnElement(swotContainer);
    }
  }

  // Update SWOT display
  updateSwotDisplay(swotData) {
    const container = document.getElementById('swotAnalysis');
    if (!container) return;

    const { strengths, weaknesses, opportunities, threats, score } = swotData;

    container.innerHTML = `
      <div class="card card-modern">
        <div class="card-header d-flex justify-content-between align-items-center">
          <h6 class="mb-0">SWOT Analizi</h6>
          <span class="badge bg-primary">Puan: ${score}/100</span>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6 mb-3">
              <h6 class="text-success">Güçlü Yönler</h6>
              <ul class="list-unstyled">
                ${strengths.map(item => `<li><i class="fas fa-plus text-success me-2"></i>${item}</li>`).join('')}
              </ul>
            </div>
            <div class="col-md-6 mb-3">
              <h6 class="text-warning">Zayıf Yönler</h6>
              <ul class="list-unstyled">
                ${weaknesses.map(item => `<li><i class="fas fa-minus text-warning me-2"></i>${item}</li>`).join('')}
              </ul>
            </div>
            <div class="col-md-6">
              <h6 class="text-info">Fırsatlar</h6>
              <ul class="list-unstyled">
                ${opportunities.map(item => `<li><i class="fas fa-arrow-up text-info me-2"></i>${item}</li>`).join('')}
              </ul>
            </div>
            <div class="col-md-6">
              <h6 class="text-danger">Tehditler</h6>
              <ul class="list-unstyled">
                ${threats.map(item => `<li><i class="fas fa-exclamation-triangle text-danger me-2"></i>${item}</li>`).join('')}
              </ul>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Generate report
  async generateReport(analysisId, format) {
    this.loading.show(`${format.toUpperCase()} raporu oluşturuluyor...`);

    try {
      const response = await fetch(`/analysis/generate-report/${analysisId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ format: format })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analiz_raporu_${analysisId}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        this.notifications.success('Rapor başarıyla oluşturuldu');
      } else {
        this.notifications.error('Rapor oluşturulamadı');
      }
    } catch (error) {
      console.error('Report generation error:', error);
      this.notifications.error('Rapor oluşturma hatası');
    } finally {
      this.loading.hide();
    }
  }

  // Load analysis list
  async loadAnalysisList() {
    const listContainer = document.getElementById('analysisList');
    if (!listContainer) return;

    this.loading.showSkeleton(listContainer, {
      rows: 5,
      height: '60px'
    });

    try {
      const response = await fetch('/analysis/list', {
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      const result = await response.json();

      if (result.success) {
        this.renderAnalysisList(result.data);
      }
    } catch (error) {
      console.error('Analysis list loading error:', error);
    } finally {
      this.loading.hideSkeleton(listContainer);
    }
  }

  // Render analysis list
  renderAnalysisList(analyses) {
    const container = document.getElementById('analysisList');
    if (!container) return;

    if (analyses.length === 0) {
      container.innerHTML = `
        <div class="text-center py-5">
          <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
          <h5 class="text-muted">Henüz analiz bulunmuyor</h5>
          <p class="text-muted">İlk analizinizi oluşturmak için yukarıdaki formu kullanın.</p>
        </div>
      `;
      return;
    }

    const listHtml = analyses.map(analysis => `
      <div class="card card-modern mb-3">
        <div class="card-body">
          <div class="row align-items-center">
            <div class="col-md-6">
              <h6 class="mb-1">${analysis.arsa_adi}</h6>
              <small class="text-muted">${analysis.il} / ${analysis.ilce}</small>
            </div>
            <div class="col-md-3">
              <small class="text-muted">Alan</small>
              <div>${analysis.alan_m2} m²</div>
            </div>
            <div class="col-md-3 text-end">
              <div class="btn-group">
                <button class="btn btn-sm btn-outline-primary" data-action="view-analysis" data-analysis-id="${analysis.id}">
                  <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-secondary" data-action="edit-analysis" data-analysis-id="${analysis.id}">
                  <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" data-action="delete-analysis" data-analysis-id="${analysis.id}">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `).join('');

    container.innerHTML = listHtml;
  }

  // Initialize charts
  initializeCharts() {
    // Chart.js initialization will be added here
    console.log('Charts initialized');
  }

  // Utility methods
  formatCurrency(amount) {
    return new Intl.NumberFormat('tr-TR', {
      style: 'currency',
      currency: 'TRY'
    }).format(amount);
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
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.body.classList.contains('analysis-page')) {
    window.AnalysisManager = new AnalysisManager();
  }
});

export default AnalysisManager;
