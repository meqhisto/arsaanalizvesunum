// frontend/src/js/pages/analysis.js

export class AnalysisPage {
    constructor(apiClient, toastManager) {
        this.apiClient = apiClient;
        this.toastManager = toastManager;
    }

    async render() {
        return `
            <div class="analysis-container">
                <!-- Page Header -->
                <div class="flex justify-between items-center mb-8">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900">Arsa Analizi</h1>
                        <p class="text-gray-600 mt-2">Gayrimenkul analiz ve değerlendirme sistemi</p>
                    </div>
                    <button id="new-analysis-btn" class="btn btn-primary">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        Yeni Analiz
                    </button>
                </div>

                <!-- Quick Stats -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div class="stat-card">
                        <div class="stat-icon bg-blue-500">📊</div>
                        <div class="stat-value" id="total-analyses">-</div>
                        <div class="stat-label">Toplam Analiz</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-green-500">✅</div>
                        <div class="stat-value" id="completed-analyses">-</div>
                        <div class="stat-label">Tamamlanan</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-yellow-500">⏳</div>
                        <div class="stat-value" id="pending-analyses">-</div>
                        <div class="stat-label">Bekleyen</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-purple-500">💰</div>
                        <div class="stat-value" id="avg-value">-</div>
                        <div class="stat-label">Ort. Değer</div>
                    </div>
                </div>

                <!-- Filters and Search -->
                <div class="card mb-6">
                    <div class="card-body">
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Arama</label>
                                <input type="text" id="search-input" placeholder="Analiz ara..." 
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Durum</label>
                                <select id="status-filter" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                                    <option value="">Tüm Durumlar</option>
                                    <option value="draft">Taslak</option>
                                    <option value="in_progress">Devam Ediyor</option>
                                    <option value="completed">Tamamlandı</option>
                                    <option value="archived">Arşivlendi</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Tarih Aralığı</label>
                                <input type="date" id="date-from" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div class="flex items-end">
                                <button id="filter-btn" class="btn btn-primary w-full">Filtrele</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Analysis List -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Analizler</h3>
                        <div class="flex space-x-2">
                            <button id="grid-view-btn" class="p-2 text-gray-400 hover:text-gray-600">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
                                </svg>
                            </button>
                            <button id="list-view-btn" class="p-2 text-blue-600">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="analyses-container">
                            <!-- Analyses will be loaded here -->
                        </div>
                    </div>
                </div>

                <!-- Pagination -->
                <div class="mt-6 flex justify-between items-center">
                    <div class="text-sm text-gray-700">
                        <span id="pagination-info">-</span>
                    </div>
                    <div class="flex space-x-2">
                        <button id="prev-page" class="btn btn-outline btn-sm">Önceki</button>
                        <button id="next-page" class="btn btn-outline btn-sm">Sonraki</button>
                    </div>
                </div>
            </div>
        `;
    }

    async init() {
        try {
            // Setup event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadAnalyses();
            await this.loadStats();
            
        } catch (error) {
            console.error('Analysis page initialization error:', error);
            this.toastManager.error('Analiz sayfası yüklenirken hata oluştu');
        }
    }

    setupEventListeners() {
        // New analysis button
        const newAnalysisBtn = document.getElementById('new-analysis-btn');
        if (newAnalysisBtn) {
            newAnalysisBtn.addEventListener('click', () => {
                this.toastManager.info('Yeni analiz özelliği yakında eklenecek');
            });
        }

        // Search and filters
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.loadAnalyses();
                }, 300);
            });
        }

        const filterBtn = document.getElementById('filter-btn');
        if (filterBtn) {
            filterBtn.addEventListener('click', () => {
                this.loadAnalyses();
            });
        }

        // View toggle buttons
        const gridViewBtn = document.getElementById('grid-view-btn');
        const listViewBtn = document.getElementById('list-view-btn');
        
        if (gridViewBtn) {
            gridViewBtn.addEventListener('click', () => {
                this.switchView('grid');
            });
        }
        
        if (listViewBtn) {
            listViewBtn.addEventListener('click', () => {
                this.switchView('list');
            });
        }
    }

    async loadAnalyses() {
        const container = document.getElementById('analyses-container');
        if (!container) return;

        try {
            // Show loading
            container.innerHTML = '<div class="flex justify-center items-center h-32"><div class="loading-spinner w-8 h-8"></div></div>';

            // Get filter values
            const searchQuery = document.getElementById('search-input')?.value || '';
            const statusFilter = document.getElementById('status-filter')?.value || '';
            const dateFrom = document.getElementById('date-from')?.value || '';

            const params = {};
            if (searchQuery) params.q = searchQuery;
            if (statusFilter) params.status = statusFilter;
            if (dateFrom) params.date_from = dateFrom;

            const response = await this.apiClient.getPaginated('/analysis', 1, 20, params);
            
            if (response.success) {
                container.innerHTML = this.renderAnalysesList(response.data || []);
                this.updatePagination(response.meta || {});
            } else {
                throw new Error(response.message);
            }

        } catch (error) {
            console.error('Error loading analyses:', error);
            container.innerHTML = '<div class="text-center text-red-600 py-8">Analizler yüklenirken hata oluştu</div>';
        }
    }

    async loadStats() {
        try {
            const response = await this.apiClient.get('/analysis/stats');
            
            if (response.success && response.data) {
                this.updateStats(response.data);
            }

        } catch (error) {
            console.error('Error loading analysis stats:', error);
        }
    }

    updateStats(stats) {
        this.updateElement('total-analyses', stats.total_analyses || 0);
        this.updateElement('completed-analyses', stats.completed_analyses || 0);
        this.updateElement('pending-analyses', stats.pending_analyses || 0);
        this.updateElement('avg-value', this.formatCurrency(stats.average_value || 0));
    }

    renderAnalysesList(analyses) {
        if (!analyses.length) {
            return `
                <div class="text-center py-12">
                    <div class="text-gray-400 text-6xl mb-4">📊</div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Henüz analiz bulunmuyor</h3>
                    <p class="text-gray-600 mb-4">İlk analizinizi oluşturmak için başlayın</p>
                    <button class="btn btn-primary">Yeni Analiz Oluştur</button>
                </div>
            `;
        }

        return `
            <div class="space-y-4">
                ${analyses.map(analysis => this.renderAnalysisCard(analysis)).join('')}
            </div>
        `;
    }

    renderAnalysisCard(analysis) {
        const statusBadge = this.getStatusBadge(analysis.status);
        const createdDate = this.formatDate(analysis.created_at);

        return `
            <div class="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h4 class="text-lg font-semibold text-gray-900">${analysis.title || 'Başlıksız Analiz'}</h4>
                        <p class="text-gray-600 text-sm">${analysis.location || 'Konum belirtilmemiş'}</p>
                    </div>
                    ${statusBadge}
                </div>
                
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                        <span class="text-sm text-gray-500">Alan</span>
                        <p class="font-medium">${analysis.area || '-'} m²</p>
                    </div>
                    <div>
                        <span class="text-sm text-gray-500">Değer</span>
                        <p class="font-medium">${this.formatCurrency(analysis.estimated_value)}</p>
                    </div>
                    <div>
                        <span class="text-sm text-gray-500">Tarih</span>
                        <p class="font-medium">${createdDate}</p>
                    </div>
                    <div>
                        <span class="text-sm text-gray-500">Tip</span>
                        <p class="font-medium">${analysis.property_type || '-'}</p>
                    </div>
                </div>
                
                <div class="flex justify-between items-center">
                    <div class="text-sm text-gray-500">
                        Son güncelleme: ${this.formatDate(analysis.updated_at)}
                    </div>
                    <div class="flex space-x-2">
                        <button class="btn btn-outline btn-sm" onclick="window.analysisPage.viewAnalysis(${analysis.id})">
                            Görüntüle
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="window.analysisPage.editAnalysis(${analysis.id})">
                            Düzenle
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getStatusBadge(status) {
        const statusConfig = {
            'draft': { class: 'badge-secondary', text: 'Taslak' },
            'in_progress': { class: 'badge-warning', text: 'Devam Ediyor' },
            'completed': { class: 'badge-success', text: 'Tamamlandı' },
            'archived': { class: 'badge-secondary', text: 'Arşivlendi' }
        };

        const config = statusConfig[status] || statusConfig['draft'];
        return `<span class="badge ${config.class}">${config.text}</span>`;
    }

    switchView(viewType) {
        // Update button states
        const gridBtn = document.getElementById('grid-view-btn');
        const listBtn = document.getElementById('list-view-btn');

        if (viewType === 'grid') {
            gridBtn.classList.add('text-blue-600');
            gridBtn.classList.remove('text-gray-400');
            listBtn.classList.add('text-gray-400');
            listBtn.classList.remove('text-blue-600');
        } else {
            listBtn.classList.add('text-blue-600');
            listBtn.classList.remove('text-gray-400');
            gridBtn.classList.add('text-gray-400');
            gridBtn.classList.remove('text-blue-600');
        }

        // Reload with new view
        this.loadAnalyses();
    }

    updatePagination(meta) {
        const paginationInfo = document.getElementById('pagination-info');
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');

        if (paginationInfo && meta.pagination) {
            const { page, per_page, total } = meta.pagination;
            const start = (page - 1) * per_page + 1;
            const end = Math.min(page * per_page, total);
            paginationInfo.textContent = `${start}-${end} / ${total}`;
        }

        if (prevBtn) {
            prevBtn.disabled = !meta.pagination?.has_prev;
        }

        if (nextBtn) {
            nextBtn.disabled = !meta.pagination?.has_next;
        }
    }

    // Action methods
    viewAnalysis(analysisId) {
        this.toastManager.info(`Analiz ${analysisId} görüntüleme özelliği yakında eklenecek`);
    }

    editAnalysis(analysisId) {
        this.toastManager.info(`Analiz ${analysisId} düzenleme özelliği yakında eklenecek`);
    }

    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('tr-TR');
    }

    formatCurrency(amount) {
        if (!amount) return '-';
        return new Intl.NumberFormat('tr-TR', {
            style: 'currency',
            currency: 'TRY'
        }).format(amount);
    }
}

// Make analysis page methods globally accessible
window.analysisPage = null;

export default AnalysisPage;
