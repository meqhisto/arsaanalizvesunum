document.addEventListener('DOMContentLoaded', function() {
    // Hatırlatıcı ayarları gösterme/gizleme
    const reminderEnabledToggle = document.getElementById('reminder_enabled');
    const reminderSettings = document.getElementById('reminder_settings');
    
    if (reminderEnabledToggle && reminderSettings) {
        reminderEnabledToggle.addEventListener('change', function() {
            reminderSettings.style.display = this.checked ? 'block' : 'none';
        });
    }
    
    // Tekrarlanan görev ayarları gösterme/gizleme
    const recurringToggle = document.getElementById('is_recurring');
    const recurringSettings = document.getElementById('recurring_settings');
    
    if (recurringToggle && recurringSettings) {
        recurringToggle.addEventListener('change', function() {
            recurringSettings.style.display = this.checked ? 'block' : 'none';
        });
    }
    
    // Due date değiştiğinde hatırlatma zamanını otomatik ayarlama
    const dueDate = document.getElementById('due_date');
    const reminderTime = document.getElementById('reminder_time');
    
    if (dueDate && reminderTime) {
        dueDate.addEventListener('change', function() {
            if (reminderEnabledToggle && reminderEnabledToggle.checked && this.value && !reminderTime.value) {
                // Son tarihin 1 gün öncesini hatırlatıcı zamanı olarak ayarla
                const date = new Date(this.value);
                date.setDate(date.getDate() - 1);
                
                // Tarihi YYYY-MM-DDThh:mm formatına dönüştür
                const year = date.getFullYear();
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                const day = date.getDate().toString().padStart(2, '0');
                const hours = date.getHours().toString().padStart(2, '0');
                const minutes = date.getMinutes().toString().padStart(2, '0');
                
                reminderTime.value = `${year}-${month}-${day}T${hours}:${minutes}`;
            }
        });
    }
});
