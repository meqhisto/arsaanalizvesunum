// frontend/src/js/utils/router.js

export class Router {
    constructor() {
        this.routes = new Map();
        this.currentRoute = null;
        this.beforeRouteChange = null;
        this.afterRouteChange = null;
    }

    // Add a route
    addRoute(path, handler) {
        this.routes.set(path, handler);
    }

    // Remove a route
    removeRoute(path) {
        this.routes.delete(path);
    }

    // Navigate to a route
    navigate(path, replace = false) {
        if (this.currentRoute === path) {
            return; // Already on this route
        }

        // Call before route change hook
        if (this.beforeRouteChange) {
            const shouldContinue = this.beforeRouteChange(this.currentRoute, path);
            if (shouldContinue === false) {
                return; // Navigation cancelled
            }
        }

        // Update browser history
        if (replace) {
            window.history.replaceState({ path }, '', path);
        } else {
            window.history.pushState({ path }, '', path);
        }

        // Handle the route
        this.handleRoute(path);
    }

    // Handle current route
    handleRoute(path = null) {
        const currentPath = path || window.location.pathname;
        
        // Find matching route
        const handler = this.routes.get(currentPath);
        
        if (handler) {
            // Update current route
            const previousRoute = this.currentRoute;
            this.currentRoute = currentPath;
            
            // Execute route handler
            try {
                handler();
                
                // Update active navigation
                this.updateActiveNavigation(currentPath);
                
                // Call after route change hook
                if (this.afterRouteChange) {
                    this.afterRouteChange(previousRoute, currentPath);
                }
            } catch (error) {
                console.error('Route handler error:', error);
                this.handleRouteError(error, currentPath);
            }
        } else {
            // Handle 404
            this.handle404(currentPath);
        }
    }

    // Handle route errors
    handleRouteError(error, path) {
        console.error(`Error handling route ${path}:`, error);
        
        // Show error message
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="text-center py-12">
                    <div class="text-red-600 text-6xl mb-4">⚠️</div>
                    <h2 class="text-2xl font-bold text-gray-900 mb-2">Sayfa Yüklenemedi</h2>
                    <p class="text-gray-600 mb-4">Bu sayfayı yüklerken bir hata oluştu.</p>
                    <button onclick="window.location.reload()" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                        Sayfayı Yenile
                    </button>
                </div>
            `;
        }
    }

    // Handle 404 errors
    handle404(path) {
        console.warn(`Route not found: ${path}`);
        
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="text-center py-12">
                    <div class="text-gray-400 text-6xl mb-4">🔍</div>
                    <h2 class="text-2xl font-bold text-gray-900 mb-2">Sayfa Bulunamadı</h2>
                    <p class="text-gray-600 mb-4">Aradığınız sayfa mevcut değil.</p>
                    <button onclick="window.app.router.navigate('/dashboard')" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                        Ana Sayfaya Dön
                    </button>
                </div>
            `;
        }
        
        // Redirect to dashboard after a delay
        setTimeout(() => {
            this.navigate('/dashboard', true);
        }, 3000);
    }

    // Update active navigation styling
    updateActiveNavigation(currentPath) {
        // Remove active class from all nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('bg-blue-50', 'text-blue-600', 'border-blue-600');
            link.classList.add('text-gray-700');
        });

        // Add active class to current nav link
        const activeLink = document.querySelector(`.nav-link[href="${currentPath}"]`);
        if (activeLink) {
            activeLink.classList.remove('text-gray-700');
            activeLink.classList.add('bg-blue-50', 'text-blue-600', 'border-blue-600');
        }
    }

    // Get current route
    getCurrentRoute() {
        return this.currentRoute;
    }

    // Set before route change hook
    setBeforeRouteChange(callback) {
        this.beforeRouteChange = callback;
    }

    // Set after route change hook
    setAfterRouteChange(callback) {
        this.afterRouteChange = callback;
    }

    // Go back in history
    goBack() {
        window.history.back();
    }

    // Go forward in history
    goForward() {
        window.history.forward();
    }

    // Replace current route
    replace(path) {
        this.navigate(path, true);
    }

    // Get route parameters (for future use with parameterized routes)
    getRouteParams(pattern, path) {
        const patternParts = pattern.split('/');
        const pathParts = path.split('/');
        const params = {};

        if (patternParts.length !== pathParts.length) {
            return null;
        }

        for (let i = 0; i < patternParts.length; i++) {
            const patternPart = patternParts[i];
            const pathPart = pathParts[i];

            if (patternPart.startsWith(':')) {
                // Parameter
                const paramName = patternPart.slice(1);
                params[paramName] = pathPart;
            } else if (patternPart !== pathPart) {
                // Mismatch
                return null;
            }
        }

        return params;
    }

    // Add parameterized route support (for future enhancement)
    addParameterizedRoute(pattern, handler) {
        // Store pattern for later matching
        this.routes.set(pattern, {
            handler,
            isParameterized: true,
            pattern
        });
    }

    // Enhanced route matching with parameters
    findMatchingRoute(path) {
        // First try exact match
        if (this.routes.has(path)) {
            return {
                handler: this.routes.get(path),
                params: {}
            };
        }

        // Try parameterized routes
        for (const [pattern, routeData] of this.routes.entries()) {
            if (routeData.isParameterized) {
                const params = this.getRouteParams(pattern, path);
                if (params !== null) {
                    return {
                        handler: routeData.handler,
                        params
                    };
                }
            }
        }

        return null;
    }
}

export default Router;
