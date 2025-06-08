// frontend/src/js/api/client.js
import axios from 'axios';

export class ApiClient {
    constructor() {
        this.baseURL = '';
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        
        // Create axios instance
        this.client = axios.create({
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });
        
        this.setupInterceptors();
    }

    setBaseURL(baseURL) {
        this.baseURL = baseURL;
        this.client.defaults.baseURL = baseURL;
    }

    setupInterceptors() {
        // Request interceptor
        this.client.interceptors.request.use(
            (config) => {
                // Apply custom request interceptors
                for (const interceptor of this.requestInterceptors) {
                    config = interceptor(config);
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor
        this.client.interceptors.response.use(
            (response) => {
                // Apply custom response interceptors
                for (const interceptor of this.responseInterceptors) {
                    response = interceptor[0](response);
                }
                return response.data; // Return only the data part
            },
            async (error) => {
                // Apply custom error interceptors
                for (const interceptor of this.responseInterceptors) {
                    if (interceptor[1]) {
                        try {
                            return await interceptor[1](error);
                        } catch (e) {
                            // Continue to next interceptor if this one fails
                        }
                    }
                }
                
                // Format error response
                const errorResponse = {
                    success: false,
                    message: 'Network error',
                    status: error.response?.status || 0,
                    data: null
                };

                if (error.response?.data) {
                    errorResponse.message = error.response.data.message || errorResponse.message;
                    errorResponse.errors = error.response.data.errors;
                    errorResponse.error_code = error.response.data.error_code;
                }

                return Promise.reject(errorResponse);
            }
        );
    }

    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    addResponseInterceptor(successInterceptor, errorInterceptor) {
        this.responseInterceptors.push([successInterceptor, errorInterceptor]);
    }

    // HTTP Methods
    async get(url, config = {}) {
        try {
            return await this.client.get(url, config);
        } catch (error) {
            throw error;
        }
    }

    async post(url, data = {}, config = {}) {
        try {
            return await this.client.post(url, data, config);
        } catch (error) {
            throw error;
        }
    }

    async put(url, data = {}, config = {}) {
        try {
            return await this.client.put(url, data, config);
        } catch (error) {
            throw error;
        }
    }

    async patch(url, data = {}, config = {}) {
        try {
            return await this.client.patch(url, data, config);
        } catch (error) {
            throw error;
        }
    }

    async delete(url, config = {}) {
        try {
            return await this.client.delete(url, config);
        } catch (error) {
            throw error;
        }
    }

    // Direct axios instance access for complex requests
    async request(config) {
        try {
            return await this.client.request(config);
        } catch (error) {
            throw error;
        }
    }

    // File upload helper
    async uploadFile(url, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);

        const config = {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        };

        if (onProgress) {
            config.onUploadProgress = (progressEvent) => {
                const percentCompleted = Math.round(
                    (progressEvent.loaded * 100) / progressEvent.total
                );
                onProgress(percentCompleted);
            };
        }

        try {
            return await this.client.post(url, formData, config);
        } catch (error) {
            throw error;
        }
    }

    // Batch requests helper
    async batch(requests) {
        try {
            const promises = requests.map(request => {
                const { method, url, data, config } = request;
                return this[method.toLowerCase()](url, data, config);
            });
            
            return await Promise.allSettled(promises);
        } catch (error) {
            throw error;
        }
    }

    // Pagination helper
    async getPaginated(url, page = 1, perPage = 20, params = {}) {
        const queryParams = {
            page,
            per_page: perPage,
            ...params
        };

        const queryString = new URLSearchParams(queryParams).toString();
        const fullUrl = `${url}?${queryString}`;

        try {
            return await this.get(fullUrl);
        } catch (error) {
            throw error;
        }
    }

    // Search helper
    async search(url, query, filters = {}) {
        const params = {
            q: query,
            ...filters
        };

        const queryString = new URLSearchParams(params).toString();
        const fullUrl = `${url}?${queryString}`;

        try {
            return await this.get(fullUrl);
        } catch (error) {
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        try {
            return await this.get('/health');
        } catch (error) {
            return {
                success: false,
                message: 'API is not available',
                status: 'down'
            };
        }
    }

    // Get API info
    async getApiInfo() {
        try {
            return await this.get('/');
        } catch (error) {
            throw error;
        }
    }
}

export default ApiClient;
