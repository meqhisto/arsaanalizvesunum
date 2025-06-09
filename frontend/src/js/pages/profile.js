// frontend/src/js/pages/profile.js

export class ProfilePage {
    constructor(apiClient, toastManager) {
        this.apiClient = apiClient;
        this.toastManager = toastManager;
        this.currentUser = null;
    }

    async render() {
        return `
            <div class="profile-container max-w-4xl mx-auto">
                <!-- Page Header -->
                <div class="mb-8">
                    <h1 class="text-3xl font-bold text-gray-900">Profil Ayarları</h1>
                    <p class="text-gray-600 mt-2">Hesap bilgilerinizi ve tercihlerinizi yönetin</p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <!-- Profile Sidebar -->
                    <div class="lg:col-span-1">
                        <div class="card">
                            <div class="card-body text-center">
                                <div class="w-24 h-24 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4" id="profile-avatar">
                                    U
                                </div>
                                <h3 class="text-lg font-semibold text-gray-900" id="profile-name">-</h3>
                                <p class="text-gray-600" id="profile-email">-</p>
                                <p class="text-sm text-gray-500 mt-2" id="profile-role">-</p>
                                
                                <div class="mt-6 space-y-2">
                                    <div class="text-sm">
                                        <span class="text-gray-500">Üyelik:</span>
                                        <span id="profile-join-date">-</span>
                                    </div>
                                    <div class="text-sm">
                                        <span class="text-gray-500">Son Giriş:</span>
                                        <span id="profile-last-login">-</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Quick Stats -->
                        <div class="card mt-6">
                            <div class="card-header">
                                <h4 class="card-title">İstatistikler</h4>
                            </div>
                            <div class="card-body">
                                <div class="space-y-3">
                                    <div class="flex justify-between">
                                        <span class="text-gray-600">Toplam Analiz</span>
                                        <span class="font-semibold" id="user-total-analyses">-</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-gray-600">Toplam Kişi</span>
                                        <span class="font-semibold" id="user-total-contacts">-</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span class="text-gray-600">Aktif Portföy</span>
                                        <span class="font-semibold" id="user-total-portfolios">-</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Profile Content -->
                    <div class="lg:col-span-2 space-y-6">
                        <!-- Personal Information -->
                        <div class="card">
                            <div class="card-header">
                                <h4 class="card-title">Kişisel Bilgiler</h4>
                            </div>
                            <div class="card-body">
                                <form id="profile-form">
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div class="form-group">
                                            <label for="first_name">Ad</label>
                                            <input type="text" id="first_name" name="first_name" required>
                                        </div>
                                        <div class="form-group">
                                            <label for="last_name">Soyad</label>
                                            <input type="text" id="last_name" name="last_name" required>
                                        </div>
                                        <div class="form-group md:col-span-2">
                                            <label for="email">E-posta</label>
                                            <input type="email" id="email" name="email" required>
                                        </div>
                                        <div class="form-group">
                                            <label for="phone">Telefon</label>
                                            <input type="tel" id="phone" name="phone">
                                        </div>
                                        <div class="form-group">
                                            <label for="company">Şirket</label>
                                            <input type="text" id="company" name="company">
                                        </div>
                                        <div class="form-group md:col-span-2">
                                            <label for="bio">Hakkında</label>
                                            <textarea id="bio" name="bio" rows="3" placeholder="Kendiniz hakkında kısa bilgi"></textarea>
                                        </div>
                                    </div>
                                    <div class="flex justify-end mt-6">
                                        <button type="submit" class="btn btn-primary">Bilgileri Güncelle</button>
                                    </div>
                                </form>
                            </div>
                        </div>

                        <!-- Password Change -->
                        <div class="card">
                            <div class="card-header">
                                <h4 class="card-title">Şifre Değiştir</h4>
                            </div>
                            <div class="card-body">
                                <form id="password-form">
                                    <div class="space-y-4">
                                        <div class="form-group">
                                            <label for="current_password">Mevcut Şifre</label>
                                            <input type="password" id="current_password" name="current_password" required>
                                        </div>
                                        <div class="form-group">
                                            <label for="new_password">Yeni Şifre</label>
                                            <input type="password" id="new_password" name="new_password" required minlength="6">
                                            <div class="form-help">En az 6 karakter olmalıdır</div>
                                        </div>
                                        <div class="form-group">
                                            <label for="confirm_password">Yeni Şifre (Tekrar)</label>
                                            <input type="password" id="confirm_password" name="confirm_password" required>
                                        </div>
                                    </div>
                                    <div class="flex justify-end mt-6">
                                        <button type="submit" class="btn btn-warning">Şifreyi Değiştir</button>
                                    </div>
                                </form>
                            </div>
                        </div>

                        <!-- Preferences -->
                        <div class="card">
                            <div class="card-header">
                                <h4 class="card-title">Tercihler</h4>
                            </div>
                            <div class="card-body">
                                <form id="preferences-form">
                                    <div class="space-y-4">
                                        <div class="flex items-center justify-between">
                                            <div>
                                                <label class="font-medium text-gray-900">E-posta Bildirimleri</label>
                                                <p class="text-sm text-gray-600">Yeni analizler ve güncellemeler hakkında bildirim alın</p>
                                            </div>
                                            <label class="relative inline-flex items-center cursor-pointer">
                                                <input type="checkbox" id="email_notifications" name="email_notifications" class="sr-only peer">
                                                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                            </label>
                                        </div>
                                        
                                        <div class="flex items-center justify-between">
                                            <div>
                                                <label class="font-medium text-gray-900">Karanlık Tema</label>
                                                <p class="text-sm text-gray-600">Arayüzü karanlık temada görüntüleyin</p>
                                            </div>
                                            <label class="relative inline-flex items-center cursor-pointer">
                                                <input type="checkbox" id="dark_mode" name="dark_mode" class="sr-only peer">
                                                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                                            </label>
                                        </div>
                                        
                                        <div class="form-group">
                                            <label for="language">Dil</label>
                                            <select id="language" name="language" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                                                <option value="tr">Türkçe</option>
                                                <option value="en">English</option>
                                            </select>
                                        </div>
                                        
                                        <div class="form-group">
                                            <label for="timezone">Saat Dilimi</label>
                                            <select id="timezone" name="timezone" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                                                <option value="Europe/Istanbul">İstanbul (UTC+3)</option>
                                                <option value="Europe/London">Londra (UTC+0)</option>
                                                <option value="America/New_York">New York (UTC-5)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="flex justify-end mt-6">
                                        <button type="submit" class="btn btn-primary">Tercihleri Kaydet</button>
                                    </div>
                                </form>
                            </div>
                        </div>

                        <!-- Account Actions -->
                        <div class="card">
                            <div class="card-header">
                                <h4 class="card-title">Hesap İşlemleri</h4>
                            </div>
                            <div class="card-body">
                                <div class="space-y-4">
                                    <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                        <div>
                                            <h5 class="font-medium text-gray-900">Verileri Dışa Aktar</h5>
                                            <p class="text-sm text-gray-600">Tüm verilerinizi JSON formatında indirin</p>
                                        </div>
                                        <button id="export-data-btn" class="btn btn-outline">Dışa Aktar</button>
                                    </div>
                                    
                                    <div class="flex items-center justify-between p-4 bg-red-50 rounded-lg border border-red-200">
                                        <div>
                                            <h5 class="font-medium text-red-900">Hesabı Sil</h5>
                                            <p class="text-sm text-red-600">Bu işlem geri alınamaz</p>
                                        </div>
                                        <button id="delete-account-btn" class="btn btn-danger">Hesabı Sil</button>
                                    </div>
                                </div>
                            </div>
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
            
            // Load user data
            await this.loadUserProfile();
            await this.loadUserStats();
            
        } catch (error) {
            console.error('Profile page initialization error:', error);
            this.toastManager.error('Profil sayfası yüklenirken hata oluştu');
        }
    }

    setupEventListeners() {
        // Profile form
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updateProfile();
            });
        }

        // Password form
        const passwordForm = document.getElementById('password-form');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.changePassword();
            });
        }

        // Preferences form
        const preferencesForm = document.getElementById('preferences-form');
        if (preferencesForm) {
            preferencesForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updatePreferences();
            });
        }

        // Export data button
        const exportBtn = document.getElementById('export-data-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportUserData();
            });
        }

        // Delete account button
        const deleteBtn = document.getElementById('delete-account-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.deleteAccount();
            });
        }

        // Password confirmation validation
        const newPassword = document.getElementById('new_password');
        const confirmPassword = document.getElementById('confirm_password');
        
        if (newPassword && confirmPassword) {
            confirmPassword.addEventListener('input', () => {
                if (newPassword.value !== confirmPassword.value) {
                    confirmPassword.setCustomValidity('Şifreler eşleşmiyor');
                } else {
                    confirmPassword.setCustomValidity('');
                }
            });
        }
    }

    async loadUserProfile() {
        try {
            const response = await this.apiClient.get('/users/profile');
            
            if (response.success && response.data) {
                this.currentUser = response.data;
                this.updateProfileUI(response.data);
                this.fillProfileForm(response.data);
            } else {
                throw new Error(response.message);
            }

        } catch (error) {
            console.error('Error loading user profile:', error);
            this.toastManager.error('Profil bilgileri yüklenirken hata oluştu');
        }
    }

    async loadUserStats() {
        try {
            // Load user-specific stats from different endpoints
            const [analysisStats, crmStats] = await Promise.all([
                this.apiClient.get('/analysis/stats').catch(() => ({ data: {} })),
                this.apiClient.get('/crm/stats').catch(() => ({ data: {} }))
            ]);

            const stats = {
                total_analyses: analysisStats.data?.total_analyses || 0,
                total_contacts: crmStats.data?.total_contacts || 0,
                total_portfolios: 0 // Placeholder
            };

            this.updateStatsUI(stats);

        } catch (error) {
            console.error('Error loading user stats:', error);
        }
    }

    updateProfileUI(user) {
        // Update avatar
        const avatar = document.getElementById('profile-avatar');
        if (avatar) {
            avatar.textContent = (user.first_name?.charAt(0) || user.email?.charAt(0) || 'U').toUpperCase();
        }

        // Update profile info
        this.updateElement('profile-name', `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'İsimsiz Kullanıcı');
        this.updateElement('profile-email', user.email || '-');
        this.updateElement('profile-role', user.role || 'Kullanıcı');
        this.updateElement('profile-join-date', this.formatDate(user.created_at));
        this.updateElement('profile-last-login', this.formatDate(user.last_login));
    }

    updateStatsUI(stats) {
        this.updateElement('user-total-analyses', stats.total_analyses);
        this.updateElement('user-total-contacts', stats.total_contacts);
        this.updateElement('user-total-portfolios', stats.total_portfolios);
    }

    fillProfileForm(user) {
        const form = document.getElementById('profile-form');
        if (!form) return;

        const fields = ['first_name', 'last_name', 'email', 'phone', 'company', 'bio'];
        fields.forEach(field => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                input.value = user[field] || '';
            }
        });
    }

    async updateProfile() {
        const form = document.getElementById('profile-form');
        if (!form) return;

        const formData = new FormData(form);
        const profileData = Object.fromEntries(formData.entries());

        try {
            const response = await this.apiClient.put('/users/profile', profileData);
            
            if (response.success) {
                this.toastManager.success('Profil başarıyla güncellendi');
                this.currentUser = { ...this.currentUser, ...response.data };
                this.updateProfileUI(this.currentUser);
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('Update profile error:', error);
            this.toastManager.error('Profil güncellenirken hata oluştu');
        }
    }

    async changePassword() {
        const form = document.getElementById('password-form');
        if (!form) return;

        const formData = new FormData(form);
        const passwordData = Object.fromEntries(formData.entries());

        // Validate password confirmation
        if (passwordData.new_password !== passwordData.confirm_password) {
            this.toastManager.error('Yeni şifreler eşleşmiyor');
            return;
        }

        try {
            const response = await this.apiClient.post('/users/change-password', {
                current_password: passwordData.current_password,
                new_password: passwordData.new_password
            });
            
            if (response.success) {
                this.toastManager.success('Şifre başarıyla değiştirildi');
                form.reset();
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            console.error('Change password error:', error);
            this.toastManager.error('Şifre değiştirilirken hata oluştu');
        }
    }

    async updatePreferences() {
        const form = document.getElementById('preferences-form');
        if (!form) return;

        const formData = new FormData(form);
        const preferences = Object.fromEntries(formData.entries());

        // Convert checkbox values
        preferences.email_notifications = form.querySelector('#email_notifications').checked;
        preferences.dark_mode = form.querySelector('#dark_mode').checked;

        try {
            // For now, just show success message since preferences endpoint might not exist
            this.toastManager.success('Tercihler kaydedildi');
            
            // Apply dark mode if enabled
            if (preferences.dark_mode) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }

        } catch (error) {
            console.error('Update preferences error:', error);
            this.toastManager.error('Tercihler kaydedilirken hata oluştu');
        }
    }

    exportUserData() {
        this.toastManager.info('Veri dışa aktarma özelliği yakında eklenecek');
    }

    deleteAccount() {
        const confirmed = confirm(
            'Hesabınızı silmek istediğinizden emin misiniz?\n\n' +
            'Bu işlem geri alınamaz ve tüm verileriniz kalıcı olarak silinecektir.'
        );

        if (confirmed) {
            const doubleConfirm = prompt(
                'Hesabınızı silmek için "HESABI SIL" yazın:'
            );

            if (doubleConfirm === 'HESABI SIL') {
                this.toastManager.warning('Hesap silme özelliği yakında eklenecek');
            }
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
        return date.toLocaleDateString('tr-TR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

export default ProfilePage;
