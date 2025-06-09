// frontend/src/js/pages/dashboard.js
import { Chart, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

export class DashboardPage {
    constructor(apiClient, toastManager) {
        this.apiClient = apiClient;
        this.toastManager = toastManager;
        this.charts = new Map();
        this.refreshInterval = null;
    }

    async render() {
        return `
            <div class="dashboard-container">
                <!-- Page Header -->
                <div class="mb-8">
                    <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
                    <p class="text-gray-600 mt-2">Arsa analiz ve CRM sisteminizin genel görünümü</p>
                </div>

                <!-- Stats Grid -->
                <div class="dashboard-grid mb-8">
                    <div class="stat-card">
                        <div class="stat-icon bg-blue-500">
                            📊
                        </div>
                        <div class="stat-value" id="total-analyses">-</div>
                        <div class="stat-label">Toplam Analiz</div>
                        <div class="stat-change positive" id="analyses-change">-</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-green-500">
                            👥
                        </div>
                        <div class="stat-value" id="total-contacts">-</div>
                        <div class="stat-label">Toplam Kişi</div>
                        <div class="stat-change positive" id="contacts-change">-</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-purple-500">
                            💼
                        </div>
                        <div class="stat-value" id="active-deals">-</div>
                        <div class="stat-label">Aktif Anlaşma</div>
                        <div class="stat-change positive" id="deals-change">-</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-yellow-500">
                            📁
                        </div>
                        <div class="stat-value" id="total-portfolios">-</div>
                        <div class="stat-label">Portföy Sayısı</div>
                        <div class="stat-change positive" id="portfolios-change">-</div>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <!-- Analysis Chart -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Aylık Analiz Trendi</h3>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="analysis-chart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>

                    <!-- CRM Chart -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">CRM İstatistikleri</h3>
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="crm-chart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Activities -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Recent Analyses -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Son Analizler</h3>
                            <a href="/analysis" class="text-blue-600 hover:text-blue-800 text-sm">Tümünü Gör</a>
                        </div>
                        <div class="card-body">
                            <div id="recent-analyses" class="space-y-3">
                                <!-- Recent analyses will be loaded here -->
                            </div>
                        </div>
                    </div>

                    <!-- Recent Tasks -->
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">Yaklaşan Görevler</h3>
                            <a href="/crm" class="text-blue-600 hover:text-blue-800 text-sm">Tümünü Gör</a>
                        </div>
                        <div class="card-body">
                            <div id="upcoming-tasks" class="space-y-3">
                                <!-- Upcoming tasks will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="fixed bottom-6 right-6 z-40">
                    <div class="relative">
                        <button id="quick-actions-btn" class="bg-blue-600 text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg hover:bg-blue-700 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                            </svg>
                        </button>
                        
                        <div id="quick-actions-menu" class="hidden absolute bottom-16 right-0 bg-white rounded-lg shadow-lg border border-gray-200 py-2 w-48">
                            <a href="/analysis" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                📊 Yeni Analiz
                            </a>
                            <a href="/crm" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                👤 Yeni Kişi
                            </a>
                            <a href="/portfolio" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                                📁 Yeni Portföy
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async init() {
        try {
            // Load dashboard data
            await this.loadDashboardData();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Start auto-refresh
            this.startAutoRefresh();
            
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.toastManager.error('Dashboard verileri yüklenirken hata oluştu');
        }
    }

    async loadDashboardData() {
        try {
            // Load stats in parallel
            const [analysisStats, crmStats, recentData] = await Promise.all([
                this.loadAnalysisStats(),
                this.loadCRMStats(),
                this.loadRecentData()
            ]);

            // Update UI with loaded data
            this.updateStatsUI(analysisStats, crmStats);
            this.updateChartsUI(analysisStats, crmStats);
            this.updateRecentActivities(recentData);

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            throw error;
        }
    }

    async loadAnalysisStats() {
        try {
            const response = await this.apiClient.get('/analysis/stats');
            return response.data || {};
        } catch (error) {
            console.error('Error loading analysis stats:', error);
            return {};
        }
    }

    async loadCRMStats() {
        try {
            const response = await this.apiClient.get('/crm/stats');
            return response.data || {};
        } catch (error) {
            console.error('Error loading CRM stats:', error);
            return {};
        }
    }

    async loadRecentData() {
        try {
            const [analyses, tasks] = await Promise.all([
                this.apiClient.getPaginated('/analysis', 1, 5),
                this.apiClient.getPaginated('/crm/tasks', 1, 5, { status: 'pending' })
            ]);

            return {
                analyses: analyses.data || [],
                tasks: tasks.data || []
            };
        } catch (error) {
            console.error('Error loading recent data:', error);
            return { analyses: [], tasks: [] };
        }
    }

    updateStatsUI(analysisStats, crmStats) {
        // Update analysis stats
        this.updateElement('total-analyses', analysisStats.total_analyses || 0);
        this.updateElement('analyses-change', this.formatChange(analysisStats.monthly_change));

        // Update CRM stats
        this.updateElement('total-contacts', crmStats.total_contacts || 0);
        this.updateElement('contacts-change', this.formatChange(crmStats.contacts_change));
        
        this.updateElement('active-deals', crmStats.active_deals || 0);
        this.updateElement('deals-change', this.formatChange(crmStats.deals_change));

        // Update portfolio stats (placeholder)
        this.updateElement('total-portfolios', analysisStats.total_portfolios || 0);
        this.updateElement('portfolios-change', this.formatChange(analysisStats.portfolios_change));
    }

    updateChartsUI(analysisStats, crmStats) {
        // Create analysis trend chart
        this.createAnalysisChart(analysisStats.monthly_data || []);
        
        // Create CRM stats chart
        this.createCRMChart(crmStats);
    }

    createAnalysisChart(monthlyData) {
        const ctx = document.getElementById('analysis-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.has('analysis')) {
            this.charts.get('analysis').destroy();
        }

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: monthlyData.map(item => item.month) || ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz'],
                datasets: [{
                    label: 'Analiz Sayısı',
                    data: monthlyData.map(item => item.count) || [12, 19, 15, 25, 22, 30],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        this.charts.set('analysis', chart);
    }

    createCRMChart(crmStats) {
        const ctx = document.getElementById('crm-chart');
        if (!ctx) return;

        // Destroy existing chart
        if (this.charts.has('crm')) {
            this.charts.get('crm').destroy();
        }

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Kişiler', 'Şirketler', 'Anlaşmalar', 'Görevler'],
                datasets: [{
                    data: [
                        crmStats.total_contacts || 0,
                        crmStats.total_companies || 0,
                        crmStats.total_deals || 0,
                        crmStats.total_tasks || 0
                    ],
                    backgroundColor: [
                        '#10b981',
                        '#8b5cf6',
                        '#f59e0b',
                        '#ef4444'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });

        this.charts.set('crm', chart);
    }

    updateRecentActivities(recentData) {
        // Update recent analyses
        const analysesContainer = document.getElementById('recent-analyses');
        if (analysesContainer) {
            analysesContainer.innerHTML = this.renderRecentAnalyses(recentData.analyses);
        }

        // Update upcoming tasks
        const tasksContainer = document.getElementById('upcoming-tasks');
        if (tasksContainer) {
            tasksContainer.innerHTML = this.renderUpcomingTasks(recentData.tasks);
        }
    }

    renderRecentAnalyses(analyses) {
        if (!analyses.length) {
            return '<p class="text-gray-500 text-sm">Henüz analiz bulunmuyor</p>';
        }

        return analyses.map(analysis => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                    <h4 class="font-medium text-gray-900">${analysis.title || 'Başlıksız Analiz'}</h4>
                    <p class="text-sm text-gray-600">${this.formatDate(analysis.created_at)}</p>
                </div>
                <span class="badge badge-primary">${analysis.status || 'Aktif'}</span>
            </div>
        `).join('');
    }

    renderUpcomingTasks(tasks) {
        if (!tasks.length) {
            return '<p class="text-gray-500 text-sm">Yaklaşan görev bulunmuyor</p>';
        }

        return tasks.map(task => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                    <h4 class="font-medium text-gray-900">${task.title || 'Başlıksız Görev'}</h4>
                    <p class="text-sm text-gray-600">${this.formatDate(task.due_date)}</p>
                </div>
                <span class="badge ${this.getTaskBadgeClass(task.priority)}">${task.priority || 'Normal'}</span>
            </div>
        `).join('');
    }

    setupEventListeners() {
        // Quick actions menu
        const quickActionsBtn = document.getElementById('quick-actions-btn');
        const quickActionsMenu = document.getElementById('quick-actions-menu');
        
        if (quickActionsBtn && quickActionsMenu) {
            quickActionsBtn.addEventListener('click', () => {
                quickActionsMenu.classList.toggle('hidden');
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!quickActionsBtn.contains(e.target) && !quickActionsMenu.contains(e.target)) {
                    quickActionsMenu.classList.add('hidden');
                }
            });
        }

        // Quick action links
        document.querySelectorAll('#quick-actions-menu a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const href = link.getAttribute('href');
                if (window.app && window.app.router) {
                    window.app.router.navigate(href);
                }
                quickActionsMenu.classList.add('hidden');
            });
        });
    }

    startAutoRefresh() {
        // Refresh dashboard data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 5 * 60 * 1000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    formatChange(change) {
        if (!change) return '-';
        const sign = change > 0 ? '+' : '';
        return `${sign}${change}%`;
    }

    formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('tr-TR');
    }

    getTaskBadgeClass(priority) {
        switch (priority?.toLowerCase()) {
            case 'high':
            case 'yüksek':
                return 'badge-danger';
            case 'medium':
            case 'orta':
                return 'badge-warning';
            case 'low':
            case 'düşük':
                return 'badge-success';
            default:
                return 'badge-secondary';
        }
    }

    // Cleanup
    destroy() {
        this.stopAutoRefresh();
        
        // Destroy charts
        for (const chart of this.charts.values()) {
            chart.destroy();
        }
        this.charts.clear();
    }
}

export default DashboardPage;
