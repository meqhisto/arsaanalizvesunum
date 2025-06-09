// frontend/src/js/api/auth.js

export class AuthService {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.tokenKey = 'access_token';
        this.refreshTokenKey = 'refresh_token';
        this.userKey = 'user_data';
        
        // Token refresh promise to prevent multiple simultaneous refresh attempts
        this.refreshPromise = null;
    }

    // Login user
    async login(credentials) {
        try {
            const response = await this.apiClient.post('/auth/login', credentials);
            
            if (response.success && response.data) {
                // Store tokens
                this.setAccessToken(response.data.access_token);
                this.setRefreshToken(response.data.refresh_token);
                
                // Store user data
                if (response.data.user) {
                    this.setUserData(response.data.user);
                }
                
                return response;
            }
            
            throw new Error(response.message || 'Login failed');
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    // Register user
    async register(userData) {
        try {
            const response = await this.apiClient.post('/auth/register', userData);
            
            if (response.success && response.data) {
                // Store tokens if registration includes auto-login
                if (response.data.access_token) {
                    this.setAccessToken(response.data.access_token);
                    this.setRefreshToken(response.data.refresh_token);
                    
                    if (response.data.user) {
                        this.setUserData(response.data.user);
                    }
                }
                
                return response;
            }
            
            throw new Error(response.message || 'Registration failed');
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    // Logout user
    async logout() {
        try {
            // Call logout endpoint to invalidate token on server
            await this.apiClient.post('/auth/logout');
        } catch (error) {
            console.error('Logout API error:', error);
            // Continue with local logout even if API call fails
        } finally {
            // Clear local storage
            this.clearTokens();
        }
    }

    // Refresh access token
    async refreshToken() {
        // Prevent multiple simultaneous refresh attempts
        if (this.refreshPromise) {
            return this.refreshPromise;
        }

        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            return false;
        }

        this.refreshPromise = this._performTokenRefresh(refreshToken);
        
        try {
            const result = await this.refreshPromise;
            return result;
        } finally {
            this.refreshPromise = null;
        }
    }

    async _performTokenRefresh(refreshToken) {
        try {
            const response = await this.apiClient.post('/auth/refresh', {
                refresh_token: refreshToken
            });

            if (response.success && response.data) {
                // Update access token
                this.setAccessToken(response.data.access_token);
                
                // Update refresh token if provided
                if (response.data.refresh_token) {
                    this.setRefreshToken(response.data.refresh_token);
                }
                
                return true;
            }
            
            // Refresh failed, clear tokens
            this.clearTokens();
            return false;
        } catch (error) {
            console.error('Token refresh error:', error);
            this.clearTokens();
            return false;
        }
    }

    // Change password
    async changePassword(currentPassword, newPassword) {
        try {
            const response = await this.apiClient.post('/users/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });
            
            return response;
        } catch (error) {
            console.error('Change password error:', error);
            throw error;
        }
    }

    // Request password reset
    async requestPasswordReset(email) {
        try {
            const response = await this.apiClient.post('/auth/password-reset-request', {
                email: email
            });
            
            return response;
        } catch (error) {
            console.error('Password reset request error:', error);
            throw error;
        }
    }

    // Reset password with token
    async resetPassword(token, newPassword) {
        try {
            const response = await this.apiClient.post('/auth/password-reset', {
                token: token,
                new_password: newPassword
            });
            
            return response;
        } catch (error) {
            console.error('Password reset error:', error);
            throw error;
        }
    }

    // Token management
    getAccessToken() {
        return localStorage.getItem(this.tokenKey);
    }

    setAccessToken(token) {
        if (token) {
            localStorage.setItem(this.tokenKey, token);
        } else {
            localStorage.removeItem(this.tokenKey);
        }
    }

    getRefreshToken() {
        return localStorage.getItem(this.refreshTokenKey);
    }

    setRefreshToken(token) {
        if (token) {
            localStorage.setItem(this.refreshTokenKey, token);
        } else {
            localStorage.removeItem(this.refreshTokenKey);
        }
    }

    // User data management
    getUserData() {
        const userData = localStorage.getItem(this.userKey);
        return userData ? JSON.parse(userData) : null;
    }

    setUserData(userData) {
        if (userData) {
            localStorage.setItem(this.userKey, JSON.stringify(userData));
        } else {
            localStorage.removeItem(this.userKey);
        }
    }

    // Clear all auth data
    clearTokens() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.refreshTokenKey);
        localStorage.removeItem(this.userKey);
    }

    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getAccessToken();
    }

    // Check if token is expired (basic check)
    isTokenExpired() {
        const token = this.getAccessToken();
        if (!token) return true;

        try {
            // Decode JWT token (basic decode, not verification)
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Date.now() / 1000;
            
            return payload.exp < currentTime;
        } catch (error) {
            console.error('Token decode error:', error);
            return true;
        }
    }

    // Get current user info
    getCurrentUser() {
        return this.getUserData();
    }

    // Update user profile
    async updateProfile(profileData) {
        try {
            const response = await this.apiClient.put('/users/profile', profileData);
            
            if (response.success && response.data) {
                // Update stored user data
                this.setUserData(response.data);
            }
            
            return response;
        } catch (error) {
            console.error('Profile update error:', error);
            throw error;
        }
    }

    // Get user profile from server
    async fetchProfile() {
        try {
            const response = await this.apiClient.get('/users/profile');
            
            if (response.success && response.data) {
                this.setUserData(response.data);
            }
            
            return response;
        } catch (error) {
            console.error('Fetch profile error:', error);
            throw error;
        }
    }

    // Auto-refresh token before expiration
    startTokenRefreshTimer() {
        const token = this.getAccessToken();
        if (!token) return;

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const expirationTime = payload.exp * 1000; // Convert to milliseconds
            const currentTime = Date.now();
            const timeUntilExpiry = expirationTime - currentTime;
            
            // Refresh token 5 minutes before expiration
            const refreshTime = Math.max(timeUntilExpiry - (5 * 60 * 1000), 0);
            
            if (refreshTime > 0) {
                setTimeout(() => {
                    this.refreshToken();
                }, refreshTime);
            }
        } catch (error) {
            console.error('Token refresh timer error:', error);
        }
    }
}

export default AuthService;
