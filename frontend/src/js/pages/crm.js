// frontend/src/js/pages/crm.js

export class CRMPage {
    constructor(apiClient, toastManager) {
        this.apiClient = apiClient;
        this.toastManager = toastManager;
        this.currentTab = 'contacts';
        this.currentPage = 1;
        this.searchQuery = '';
    }

    async render() {
        return `
            <div class="crm-container">
                <!-- Page Header -->
                <div class="flex justify-between items-center mb-8">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900">CRM</h1>
                        <p class="text-gray-600 mt-2">Müşteri ilişkileri yönetimi</p>
                    </div>
                    <button id="add-contact-btn" class="btn btn-primary">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        Yeni Kişi
                    </button>
                </div>

                <!-- Tabs -->
                <div class="border-b border-gray-200 mb-6">
                    <nav class="-mb-px flex space-x-8">
                        <button class="tab-button active" data-tab="contacts">
                            <span class="mr-2">👥</span>
                            Kişiler
                        </button>
                        <button class="tab-button" data-tab="companies">
                            <span class="mr-2">🏢</span>
                            Şirketler
                        </button>
                        <button class="tab-button" data-tab="deals">
                            <span class="mr-2">💼</span>
                            Anlaşmalar
                        </button>
                        <button class="tab-button" data-tab="tasks">
                            <span class="mr-2">✅</span>
                            Görevler
                        </button>
                    </nav>
                </div>

                <!-- Search and Filters -->
                <div class="flex flex-col sm:flex-row gap-4 mb-6">
                    <div class="flex-1">
                        <div class="relative">
                            <input type="text" id="search-input" placeholder="Ara..." 
                                   class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                </svg>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <select id="filter-select" class="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500">
                            <option value="">Tüm Durumlar</option>
                            <option value="active">Aktif</option>
                            <option value="inactive">Pasif</option>
                        </select>
                        <button id="export-btn" class="btn btn-outline">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            Dışa Aktar
                        </button>
                    </div>
                </div>

                <!-- Content Area -->
                <div id="content-area" class="bg-white rounded-lg shadow-sm border border-gray-200">
                    <!-- Content will be loaded here -->
                </div>

                <!-- Pagination -->
                <div id="pagination-container" class="mt-6 flex justify-between items-center">
                    <div class="text-sm text-gray-700">
                        <span id="pagination-info">-</span>
                    </div>
                    <div class="flex space-x-2">
                        <button id="prev-page" class="btn btn-outline btn-sm" disabled>Önceki</button>
                        <button id="next-page" class="btn btn-outline btn-sm" disabled>Sonraki</button>
                    </div>
                </div>
            </div>

            <!-- Add/Edit Modal -->
            <div id="contact-modal" class="modal-backdrop hidden">
                <div class="modal-container">
                    <div class="modal-content">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-medium text-gray-900" id="modal-title">Yeni Kişi</h3>
                        </div>
                        <form id="contact-form" class="px-6 py-4">
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="form-group">
                                    <label for="first_name">Ad</label>
                                    <input type="text" id="first_name" name="first_name" required>
                                </div>
                                <div class="form-group">
                                    <label for="last_name">Soyad</label>
                                    <input type="text" id="last_name" name="last_name" required>
                                </div>
                                <div class="form-group">
                                    <label for="email">E-posta</label>
                                    <input type="email" id="email" name="email">
                                </div>
                                <div class="form-group">
                                    <label for="phone">Telefon</label>
                                    <input type="tel" id="phone" name="phone">
                                </div>
                                <div class="form-group md:col-span-2">
                                    <label for="company">Şirket</label>
                                    <input type="text" id="company" name="company">
                                </div>
                                <div class="form-group md:col-span-2">
                                    <label for="notes">Notlar</label>
                                    <textarea id="notes" name="notes" rows="3"></textarea>
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
            await this.loadTabContent('contacts');
            
        } catch (error) {
            console.error('CRM page initialization error:', error);
            this.toastManager.error('CRM sayfası yüklenirken hata oluştu');
        }
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tab = e.target.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });

        // Search
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchQuery = e.target.value;
                    this.currentPage = 1;
                    this.loadTabContent(this.currentTab);
                }, 300);
            });
        }

        // Filter
        const filterSelect = document.getElementById('filter-select');
        if (filterSelect) {
            filterSelect.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadTabContent(this.currentTab);
            });
        }

        // Add contact button
        const addContactBtn = document.getElementById('add-contact-btn');
        if (addContactBtn) {
            addContactBtn.addEventListener('click', () => {
                this.openContactModal();
            });
        }

        // Modal events
        this.setupModalEventListeners();

        // Pagination
        this.setupPaginationEventListeners();
    }

    setupModalEventListeners() {
        const modal = document.getElementById('contact-modal');
        const cancelBtn = document.getElementById('cancel-btn');
        const saveBtn = document.getElementById('save-btn');
        const form = document.getElementById('contact-form');

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeContactModal();
            });
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeContactModal();
                }
            });
        }

        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveContact();
            });
        }

        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveContact();
            });
        }
    }

    setupPaginationEventListeners() {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.loadTabContent(this.currentTab);
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.currentPage++;
                this.loadTabContent(this.currentTab);
            });
        }
    }

    async switchTab(tab) {
        // Update active tab
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Update current tab
        this.currentTab = tab;
        this.currentPage = 1;
        this.searchQuery = '';

        // Clear search
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.value = '';
        }

        // Load content
        await this.loadTabContent(tab);
    }

    async loadTabContent(tab) {
        const contentArea = document.getElementById('content-area');
        if (!contentArea) return;

        try {
            // Show loading
            contentArea.innerHTML = '<div class="flex justify-center items-center h-64"><div class="loading-spinner w-8 h-8"></div></div>';

            let data;
            switch (tab) {
                case 'contacts':
                    data = await this.loadContacts();
                    contentArea.innerHTML = this.renderContactsTable(data.items || []);
                    break;
                case 'companies':
                    data = await this.loadCompanies();
                    contentArea.innerHTML = this.renderCompaniesTable(data.items || []);
                    break;
                case 'deals':
                    data = await this.loadDeals();
                    contentArea.innerHTML = this.renderDealsTable(data.items || []);
                    break;
                case 'tasks':
                    data = await this.loadTasks();
                    contentArea.innerHTML = this.renderTasksTable(data.items || []);
                    break;
            }

            // Update pagination
            this.updatePagination(data.meta || {});

        } catch (error) {
            console.error(`Error loading ${tab}:`, error);
            contentArea.innerHTML = '<div class="text-center text-red-600 py-8">Veri yüklenirken hata oluştu</div>';
        }
    }

    async loadContacts() {
        const params = {};
        if (this.searchQuery) params.q = this.searchQuery;
        
        const filterValue = document.getElementById('filter-select')?.value;
        if (filterValue) params.status = filterValue;

        return await this.apiClient.getPaginated('/crm/contacts', this.currentPage, 20, params);
    }

    async loadCompanies() {
        const params = {};
        if (this.searchQuery) params.q = this.searchQuery;
        
        return await this.apiClient.getPaginated('/crm/companies', this.currentPage, 20, params);
    }

    async loadDeals() {
        const params = {};
        if (this.searchQuery) params.q = this.searchQuery;
        
        return await this.apiClient.getPaginated('/crm/deals', this.currentPage, 20, params);
    }

    async loadTasks() {
        const params = {};
        if (this.searchQuery) params.q = this.searchQuery;
        
        return await this.apiClient.getPaginated('/crm/tasks', this.currentPage, 20, params);
    }

    renderContactsTable(contacts) {
        if (!contacts.length) {
            return '<div class="text-center text-gray-500 py-8">Henüz kişi bulunmuyor</div>';
        }

        return `
            <div class="overflow-x-auto">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Ad Soyad</th>
                            <th>E-posta</th>
                            <th>Telefon</th>
                            <th>Şirket</th>
                            <th>Durum</th>
                            <th>İşlemler</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${contacts.map(contact => `
                            <tr>
                                <td class="font-medium">${contact.first_name || ''} ${contact.last_name || ''}</td>
                                <td>${contact.email || '-'}</td>
                                <td>${contact.phone || '-'}</td>
                                <td>${contact.company || '-'}</td>
                                <td>
                                    <span class="badge ${contact.is_active ? 'badge-success' : 'badge-secondary'}">
                                        ${contact.is_active ? 'Aktif' : 'Pasif'}
                                    </span>
                                </td>
                                <td>
                                    <div class="flex space-x-2">
                                        <button class="text-blue-600 hover:text-blue-800" onclick="window.crmPage.editContact(${contact.id})">
                                            Düzenle
                                        </button>
                                        <button class="text-red-600 hover:text-red-800" onclick="window.crmPage.deleteContact(${contact.id})">
                                            Sil
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    renderCompaniesTable(companies) {
        // Similar implementation for companies
        return '<div class="text-center text-gray-500 py-8">Şirketler tablosu yakında eklenecek</div>';
    }

    renderDealsTable(deals) {
        // Similar implementation for deals
        return '<div class="text-center text-gray-500 py-8">Anlaşmalar tablosu yakında eklenecek</div>';
    }

    renderTasksTable(tasks) {
        // Similar implementation for tasks
        return '<div class="text-center text-gray-500 py-8">Görevler tablosu yakında eklenecek</div>';
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

    openContactModal(contact = null) {
        const modal = document.getElementById('contact-modal');
        const title = document.getElementById('modal-title');
        const form = document.getElementById('contact-form');

        if (contact) {
            title.textContent = 'Kişiyi Düzenle';
            this.fillContactForm(contact);
        } else {
            title.textContent = 'Yeni Kişi';
            form.reset();
        }

        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    closeContactModal() {
        const modal = document.getElementById('contact-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    fillContactForm(contact) {
        const form = document.getElementById('contact-form');
        if (!form) return;

        Object.keys(contact).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = contact[key] || '';
            }
        });
    }

    async saveContact() {
        const form = document.getElementById('contact-form');
        if (!form) return;

        const formData = new FormData(form);
        const contactData = Object.fromEntries(formData.entries());

        try {
            const response = await this.apiClient.post('/crm/contacts', contactData);
            
            if (response.success) {
                this.toastManager.success('Kişi başarıyla kaydedildi');
                this.closeContactModal();
                await this.loadTabContent('contacts');
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('Save contact error:', error);
            this.toastManager.error('Kişi kaydedilirken hata oluştu');
        }
    }

    async editContact(contactId) {
        try {
            const response = await this.apiClient.get(`/crm/contacts/${contactId}`);
            if (response.success) {
                this.openContactModal(response.data);
            }
        } catch (error) {
            console.error('Edit contact error:', error);
            this.toastManager.error('Kişi bilgileri yüklenirken hata oluştu');
        }
    }

    async deleteContact(contactId) {
        if (!confirm('Bu kişiyi silmek istediğinizden emin misiniz?')) {
            return;
        }

        try {
            const response = await this.apiClient.delete(`/crm/contacts/${contactId}`);
            if (response.success) {
                this.toastManager.success('Kişi başarıyla silindi');
                await this.loadTabContent('contacts');
            }
        } catch (error) {
            console.error('Delete contact error:', error);
            this.toastManager.error('Kişi silinirken hata oluştu');
        }
    }
}

// Make CRM page methods globally accessible for onclick handlers
window.crmPage = null;

export default CRMPage;
