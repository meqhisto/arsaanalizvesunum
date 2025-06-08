// frontend/src/js/pages/portfolio.js

export class PortfolioPage {
    constructor(apiClient, toastManager) {
        this.apiClient = apiClient;
        this.toastManager = toastManager;
    }

    async render() {
        return `
            <div class="portfolio-container">
                <!-- Page Header -->
                <div class="flex justify-between items-center mb-8">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900">Portföy Yönetimi</h1>
                        <p class="text-gray-600 mt-2">Analiz portföylerini organize edin ve yönetin</p>
                    </div>
                    <button id="new-portfolio-btn" class="btn btn-primary">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        Yeni Portföy
                    </button>
                </div>

                <!-- Portfolio Stats -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="stat-card">
                        <div class="stat-icon bg-blue-500">📁</div>
                        <div class="stat-value" id="total-portfolios">-</div>
                        <div class="stat-label">Toplam Portföy</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-green-500">📊</div>
                        <div class="stat-value" id="total-analyses-in-portfolios">-</div>
                        <div class="stat-label">Toplam Analiz</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon bg-purple-500">💰</div>
                        <div class="stat-value" id="total-portfolio-value">-</div>
                        <div class="stat-label">Toplam Değer</div>
                    </div>
                </div>

                <!-- Search and Filters -->
                <div class="card mb-6">
                    <div class="card-body">
                        <div class="flex flex-col md:flex-row gap-4">
                            <div class="flex-1">
                                <input type="text" id="search-input" placeholder="Portföy ara..." 
                                       class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <select id="sort-select" class="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                                    <option value="created_desc">En Yeni</option>
                                    <option value="created_asc">En Eski</option>
                                    <option value="name_asc">İsim A-Z</option>
                                    <option value="name_desc">İsim Z-A</option>
                                    <option value="value_desc">Değer (Yüksek-Düşük)</option>
                                    <option value="value_asc">Değer (Düşük-Yüksek)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Portfolio Grid -->
                <div id="portfolios-container" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <!-- Portfolios will be loaded here -->
                </div>

                <!-- Empty State -->
                <div id="empty-state" class="hidden text-center py-12">
                    <div class="text-gray-400 text-6xl mb-4">📁</div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Henüz portföy bulunmuyor</h3>
                    <p class="text-gray-600 mb-4">İlk portföyünüzü oluşturmak için başlayın</p>
                    <button class="btn btn-primary">Yeni Portföy Oluştur</button>
                </div>

                <!-- Pagination -->
                <div class="mt-8 flex justify-center">
                    <div class="flex space-x-2">
                        <button id="prev-page" class="btn btn-outline btn-sm">Önceki</button>
                        <span id="page-info" class="flex items-center px-4 text-sm text-gray-600">-</span>
                        <button id="next-page" class="btn btn-outline btn-sm">Sonraki</button>
                    </div>
                </div>
            </div>

            <!-- Portfolio Modal -->
            <div id="portfolio-modal" class="modal-backdrop hidden">
                <div class="modal-container">
                    <div class="modal-content">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-medium text-gray-900" id="modal-title">Yeni Portföy</h3>
                        </div>
                        <form id="portfolio-form" class="px-6 py-4">
                            <div class="space-y-4">
                                <div class="form-group">
                                    <label for="portfolio-name">Portföy Adı</label>
                                    <input type="text" id="portfolio-name" name="name" required 
                                           placeholder="Portföy adını girin">
                                </div>
                                <div class="form-group">
                                    <label for="portfolio-description">Açıklama</label>
                                    <textarea id="portfolio-description" name="description" rows="3" 
                                              placeholder="Portföy açıklaması (isteğe bağlı)"></textarea>
                                </div>
                                <div class="form-group">
                                    <label for="portfolio-tags">Etiketler</label>
                                    <input type="text" id="portfolio-tags" name="tags" 
                                           placeholder="Etiketleri virgülle ayırın">
                                    <div class="form-help">Örnek: konut, ticari, yatırım</div>
                                </div>
                            </div>
                        </form>
                        <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
                            <button id="cancel-btn" class="btn btn-outline">İptal</button>
                            <button id="save-btn" class="btn btn-primary">Kaydet</button>
                        </div>
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
            await this.loadPortfolios();
            await this.loadStats();
            
        } catch (error) {
            console.error('Portfolio page initialization error:', error);
            this.toastManager.error('Portföy sayfası yüklenirken hata oluştu');
        }
    }

    setupEventListeners() {
        // New portfolio button
        const newPortfolioBtn = document.getElementById('new-portfolio-btn');
        if (newPortfolioBtn) {
            newPortfolioBtn.addEventListener('click', () => {
                this.openPortfolioModal();
            });
        }

        // Search
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.loadPortfolios();
                }, 300);
            });
        }

        // Sort
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                this.loadPortfolios();
            });
        }

        // Modal events
        this.setupModalEventListeners();
    }

    setupModalEventListeners() {
        const modal = document.getElementById('portfolio-modal');
        const cancelBtn = document.getElementById('cancel-btn');
        const saveBtn = document.getElementById('save-btn');
        const form = document.getElementById('portfolio-form');

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closePortfolioModal();
            });
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closePortfolioModal();
                }
            });
        }

        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.savePortfolio();
            });
        }

        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.savePortfolio();
            });
        }
    }

    async loadPortfolios() {
        const container = document.getElementById('portfolios-container');
        const emptyState = document.getElementById('empty-state');
        
        if (!container) return;

        try {
            // Show loading
            container.innerHTML = this.renderLoadingCards();

            // Get search and sort values
            const searchQuery = document.getElementById('search-input')?.value || '';
            const sortBy = document.getElementById('sort-select')?.value || 'created_desc';

            const params = {};
            if (searchQuery) params.q = searchQuery;
            if (sortBy) params.sort = sortBy;

            const response = await this.apiClient.getPaginated('/portfolio', 1, 12, params);
            
            if (response.success) {
                const portfolios = response.data || [];
                
                if (portfolios.length === 0) {
                    container.innerHTML = '';
                    emptyState.classList.remove('hidden');
                } else {
                    emptyState.classList.add('hidden');
                    container.innerHTML = portfolios.map(portfolio => 
                        this.renderPortfolioCard(portfolio)
                    ).join('');
                }
            } else {
                throw new Error(response.message);
            }

        } catch (error) {
            console.error('Error loading portfolios:', error);
            container.innerHTML = '<div class="col-span-full text-center text-red-600 py-8">Portföyler yüklenirken hata oluştu</div>';
        }
    }

    async loadStats() {
        try {
            // For now, use placeholder data since portfolio stats endpoint might not exist
            const stats = {
                total_portfolios: 0,
                total_analyses: 0,
                total_value: 0
            };

            this.updateStats(stats);

        } catch (error) {
            console.error('Error loading portfolio stats:', error);
        }
    }

    updateStats(stats) {
        this.updateElement('total-portfolios', stats.total_portfolios || 0);
        this.updateElement('total-analyses-in-portfolios', stats.total_analyses || 0);
        this.updateElement('total-portfolio-value', this.formatCurrency(stats.total_value || 0));
    }

    renderLoadingCards() {
        return Array(6).fill(0).map(() => `
            <div class="card animate-pulse">
                <div class="card-body">
                    <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div class="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                    <div class="space-y-2">
                        <div class="h-3 bg-gray-200 rounded"></div>
                        <div class="h-3 bg-gray-200 rounded w-5/6"></div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderPortfolioCard(portfolio) {
        const analysisCount = portfolio.analysis_count || 0;
        const totalValue = portfolio.total_value || 0;
        const createdDate = this.formatDate(portfolio.created_at);
        const tags = portfolio.tags ? portfolio.tags.split(',').map(tag => tag.trim()) : [];

        return `
            <div class="card hover:shadow-lg transition-shadow cursor-pointer" onclick="window.portfolioPage.viewPortfolio(${portfolio.id})">
                <div class="card-body">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 truncate">${portfolio.name || 'Başlıksız Portföy'}</h3>
                        <div class="flex space-x-1">
                            <button class="text-gray-400 hover:text-blue-600" onclick="event.stopPropagation(); window.portfolioPage.editPortfolio(${portfolio.id})">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                                </svg>
                            </button>
                            <button class="text-gray-400 hover:text-red-600" onclick="event.stopPropagation(); window.portfolioPage.deletePortfolio(${portfolio.id})">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                    
                    <p class="text-gray-600 text-sm mb-4 line-clamp-2">${portfolio.description || 'Açıklama bulunmuyor'}</p>
                    
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <span class="text-xs text-gray-500">Analiz Sayısı</span>
                            <p class="font-semibold text-blue-600">${analysisCount}</p>
                        </div>
                        <div>
                            <span class="text-xs text-gray-500">Toplam Değer</span>
                            <p class="font-semibold text-green-600">${this.formatCurrency(totalValue)}</p>
                        </div>
                    </div>
                    
                    ${tags.length > 0 ? `
                        <div class="mb-4">
                            <div class="flex flex-wrap gap-1">
                                ${tags.slice(0, 3).map(tag => `
                                    <span class="badge badge-secondary text-xs">${tag}</span>
                                `).join('')}
                                ${tags.length > 3 ? `<span class="text-xs text-gray-500">+${tags.length - 3}</span>` : ''}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="text-xs text-gray-500">
                        Oluşturulma: ${createdDate}
                    </div>
                </div>
            </div>
        `;
    }

    openPortfolioModal(portfolio = null) {
        const modal = document.getElementById('portfolio-modal');
        const title = document.getElementById('modal-title');
        const form = document.getElementById('portfolio-form');

        if (portfolio) {
            title.textContent = 'Portföyü Düzenle';
            this.fillPortfolioForm(portfolio);
        } else {
            title.textContent = 'Yeni Portföy';
            form.reset();
        }

        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    closePortfolioModal() {
        const modal = document.getElementById('portfolio-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    fillPortfolioForm(portfolio) {
        document.getElementById('portfolio-name').value = portfolio.name || '';
        document.getElementById('portfolio-description').value = portfolio.description || '';
        document.getElementById('portfolio-tags').value = portfolio.tags || '';
    }

    async savePortfolio() {
        const form = document.getElementById('portfolio-form');
        if (!form) return;

        const formData = new FormData(form);
        const portfolioData = Object.fromEntries(formData.entries());

        try {
            const response = await this.apiClient.post('/portfolio', portfolioData);
            
            if (response.success) {
                this.toastManager.success('Portföy başarıyla kaydedildi');
                this.closePortfolioModal();
                await this.loadPortfolios();
                await this.loadStats();
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('Save portfolio error:', error);
            this.toastManager.error('Portföy kaydedilirken hata oluştu');
        }
    }

    // Action methods
    viewPortfolio(portfolioId) {
        this.toastManager.info(`Portföy ${portfolioId} detay sayfası yakında eklenecek`);
    }

    async editPortfolio(portfolioId) {
        try {
            const response = await this.apiClient.get(`/portfolio/${portfolioId}`);
            if (response.success) {
                this.openPortfolioModal(response.data);
            }
        } catch (error) {
            console.error('Edit portfolio error:', error);
            this.toastManager.error('Portföy bilgileri yüklenirken hata oluştu');
        }
    }

    async deletePortfolio(portfolioId) {
        if (!confirm('Bu portföyü silmek istediğinizden emin misiniz?')) {
            return;
        }

        try {
            const response = await this.apiClient.delete(`/portfolio/${portfolioId}`);
            if (response.success) {
                this.toastManager.success('Portföy başarıyla silindi');
                await this.loadPortfolios();
                await this.loadStats();
            }
        } catch (error) {
            console.error('Delete portfolio error:', error);
            this.toastManager.error('Portföy silinirken hata oluştu');
        }
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

// Make portfolio page methods globally accessible
window.portfolioPage = null;

export default PortfolioPage;
