// frontend/src/js/app.js
import '../css/main.scss';
import { ApiClient } from './api/client';
import { AuthService } from './api/auth';
import { Router } from './utils/router';
import { UIManager } from './utils/ui-manager';
import { ToastManager } from './utils/toast-manager';

// Import page components
import { DashboardPage } from './pages/dashboard';
import { CRMPage } from './pages/crm';
import { AnalysisPage } from './pages/analysis';
import { PortfolioPage } from './pages/portfolio';
import { ProfilePage } from './pages/profile';

class App {
    constructor() {
        this.apiClient = new ApiClient();
        this.authService = new AuthService(this.apiClient);
        this.router = new Router();
        this.uiManager = new UIManager();
        this.toastManager = new ToastManager();
        
        this.currentUser = null;
        this.isInitialized = false;
        
        this.init();
    }

    async init() {
        try {
            // Show loading screen
            this.showLoading();
            
            // Initialize services
            await this.initializeServices();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Setup routing
            this.setupRouting();
            
            // Check authentication
            await this.checkAuthentication();
            
            // Hide loading screen
            this.hideLoading();
            
            this.isInitialized = true;
            
            console.log('App initialized successfully');
        } catch (error) {
            console.error('App initialization failed:', error);
            this.toastManager.error('Uygulama başlatılamadı. Lütfen sayfayı yenileyin.');
            this.hideLoading();
        }
    }

    async initializeServices() {
        // Initialize API client with base configuration
        this.apiClient.setBaseURL('/api/v1');
        
        // Setup request/response interceptors
        this.setupApiInterceptors();
    }

    setupApiInterceptors() {
        // Request interceptor for adding auth token
        this.apiClient.addRequestInterceptor((config) => {
            const token = this.authService.getAccessToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });

        // Response interceptor for handling auth errors
        this.apiClient.addResponseInterceptor(
            (response) => response,
            async (error) => {
                if (error.response?.status === 401) {
                    // Try to refresh token
                    const refreshed = await this.authService.refreshToken();
                    if (refreshed) {
                        // Retry the original request
                        const originalRequest = error.config;
                        const token = this.authService.getAccessToken();
                        originalRequest.headers.Authorization = `Bearer ${token}`;
                        return this.apiClient.request(originalRequest);
                    } else {
                        // Redirect to login
                        this.handleLogout();
                    }
                }
                return Promise.reject(error);
            }
        );
    }

    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }

        // User menu toggle
        const userMenuButton = document.getElementById('user-menu-button');
        const userMenu = document.getElementById('user-menu');
        if (userMenuButton && userMenu) {
            userMenuButton.addEventListener('click', () => {
                userMenu.classList.toggle('hidden');
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!userMenuButton.contains(e.target) && !userMenu.contains(e.target)) {
                    userMenu.classList.add('hidden');
                }
            });
        }

        // Handle browser back/forward
        window.addEventListener('popstate', () => {
            this.router.handleRoute();
        });
    }

    setupRouting() {
        // Define routes
        this.router.addRoute('/', () => this.loadPage(DashboardPage));
        this.router.addRoute('/dashboard', () => this.loadPage(DashboardPage));
        this.router.addRoute('/crm', () => this.loadPage(CRMPage));
        this.router.addRoute('/analysis', () => this.loadPage(AnalysisPage));
        this.router.addRoute('/portfolio', () => this.loadPage(PortfolioPage));
        this.router.addRoute('/profile', () => this.loadPage(ProfilePage));

        // Handle initial route
        this.router.handleRoute();
    }

    async checkAuthentication() {
        const token = this.authService.getAccessToken();
        
        if (token) {
            try {
                // Verify token and get user info
                const userResponse = await this.apiClient.get('/users/profile');
                if (userResponse.success) {
                    this.currentUser = userResponse.data;
                    this.showApp();
                    this.updateUserUI();
                    return;
                }
            } catch (error) {
                console.log('Token verification failed:', error);
                this.authService.clearTokens();
            }
        }
        
        // Show login if not authenticated
        this.showLogin();
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const loginData = {
            email: formData.get('email'),
            password: formData.get('password'),
            remember_me: formData.get('remember_me') === 'on'
        };

        const loginButton = document.getElementById('login-button');
        const errorDiv = document.getElementById('login-error');
        
        try {
            loginButton.disabled = true;
            loginButton.textContent = 'Giriş yapılıyor...';
            errorDiv.classList.add('hidden');

            const result = await this.authService.login(loginData);
            
            if (result.success) {
                this.currentUser = result.data.user;
                this.hideLogin();
                this.showApp();
                this.updateUserUI();
                this.toastManager.success('Başarıyla giriş yaptınız!');
                this.router.navigate('/dashboard');
            } else {
                throw new Error(result.message || 'Giriş başarısız');
            }
        } catch (error) {
            console.error('Login error:', error);
            errorDiv.textContent = error.message || 'Giriş sırasında bir hata oluştu';
            errorDiv.classList.remove('hidden');
        } finally {
            loginButton.disabled = false;
            loginButton.textContent = 'Giriş Yap';
        }
    }

    async handleLogout() {
        try {
            await this.authService.logout();
        } catch (error) {
            console.error('Logout error:', error);
        }
        
        this.currentUser = null;
        this.authService.clearTokens();
        this.showLogin();
        this.toastManager.info('Çıkış yaptınız');
    }

    async loadPage(PageClass) {
        if (!this.currentUser) {
            this.showLogin();
            return;
        }

        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        try {
            // Show loading state
            mainContent.innerHTML = '<div class="flex justify-center items-center h-64"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>';

            // Create and render page
            const page = new PageClass(this.apiClient, this.toastManager);
            const content = await page.render();
            mainContent.innerHTML = content;

            // Set global page reference for onclick handlers
            if (PageClass.name === 'CRMPage') {
                window.crmPage = page;
            } else if (PageClass.name === 'AnalysisPage') {
                window.analysisPage = page;
            } else if (PageClass.name === 'PortfolioPage') {
                window.portfolioPage = page;
            }

            // Initialize page
            if (page.init) {
                await page.init();
            }
        } catch (error) {
            console.error('Page load error:', error);
            mainContent.innerHTML = '<div class="text-center text-red-600">Sayfa yüklenirken hata oluştu</div>';
            this.toastManager.error('Sayfa yüklenirken hata oluştu');
        }
    }

    updateUserUI() {
        if (!this.currentUser) return;

        // Update user avatar
        const userAvatar = document.getElementById('user-avatar');
        if (userAvatar) {
            userAvatar.textContent = this.currentUser.first_name?.charAt(0) || 'U';
        }

        // Update navigation menu
        this.updateNavigationMenu();
        
        // Update user menu
        this.updateUserMenu();
    }

    updateNavigationMenu() {
        const navMenu = document.getElementById('nav-menu');
        if (!navMenu) return;

        const menuItems = [
            { href: '/dashboard', text: 'Dashboard', icon: '📊' },
            { href: '/crm', text: 'CRM', icon: '👥' },
            { href: '/analysis', text: 'Analiz', icon: '📈' },
            { href: '/portfolio', text: 'Portföy', icon: '📁' }
        ];

        navMenu.innerHTML = menuItems.map(item => `
            <a href="${item.href}" class="nav-link flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-md transition-colors">
                <span class="mr-2">${item.icon}</span>
                ${item.text}
            </a>
        `).join('');

        // Add click handlers for navigation
        navMenu.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.router.navigate(link.getAttribute('href'));
            });
        });
    }

    updateUserMenu() {
        const userMenu = document.getElementById('user-menu');
        if (!userMenu) return;

        userMenu.innerHTML = `
            <a href="/profile" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Profil</a>
            <button id="logout-button" class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Çıkış Yap</button>
        `;

        // Add event listeners
        const profileLink = userMenu.querySelector('a[href="/profile"]');
        if (profileLink) {
            profileLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.router.navigate('/profile');
                userMenu.classList.add('hidden');
            });
        }

        const logoutButton = document.getElementById('logout-button');
        if (logoutButton) {
            logoutButton.addEventListener('click', () => {
                this.handleLogout();
                userMenu.classList.add('hidden');
            });
        }
    }

    showLoading() {
        const loadingScreen = document.getElementById('loading-screen');
        const app = document.getElementById('app');
        if (loadingScreen) loadingScreen.classList.remove('hidden');
        if (app) app.classList.add('hidden');
    }

    hideLoading() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) loadingScreen.classList.add('hidden');
    }

    showApp() {
        const app = document.getElementById('app');
        const loginModal = document.getElementById('login-modal');
        if (app) app.classList.remove('hidden');
        if (loginModal) loginModal.classList.add('hidden');
    }

    showLogin() {
        const app = document.getElementById('app');
        const loginModal = document.getElementById('login-modal');
        if (app) app.classList.add('hidden');
        if (loginModal) loginModal.classList.remove('hidden');
    }

    hideLogin() {
        const loginModal = document.getElementById('login-modal');
        if (loginModal) loginModal.classList.add('hidden');
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

export default App;
