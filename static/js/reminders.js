document.addEventListener('DOMContentLoaded', function() {
    // Hatırlatıcı bildirimi göstermek için DOM elementleri
    const reminderBadge = document.getElementById('reminder-badge');
    const reminderList = document.getElementById('reminder-list');
    
    // Hatırlatıcıları belirli aralıklarla kontrol et
    checkReminders();
    
    // Her 60 saniyede bir hatırlatıcıları kontrol et
    setInterval(checkReminders, 60000);
    
    function checkReminders() {
        fetch('/crm/tasks/check-reminders')
            .then(response => response.json())
            .then(data => {
                if (data.reminders && data.reminders.length > 0) {
                    updateReminderBadge(data.reminders.length);
                    updateReminderDropdown(data.reminders);
                    
                    // Yeni hatırlatıcılar varsa masaüstü bildirimi gönder
                    if (Notification.permission === "granted") {
                        showDesktopNotification(data.reminders[0]);
                    }
                } else {
                    // Hatırlatıcı yoksa, badge'i gizle
                    if (reminderBadge) {
                        reminderBadge.style.display = 'none';
                    }
                    
                    // Dropdown içeriğini temizle
                    if (reminderList) {
                        reminderList.innerHTML = '<li><span class="dropdown-item text-center">Aktif hatırlatıcı yok</span></li>';
                    }
                }
            })
            .catch(error => console.error('Hatırlatıcılar kontrol edilirken hata:', error));
    }
    
    function updateReminderBadge(count) {
        if (reminderBadge) {
            reminderBadge.textContent = count;
            reminderBadge.style.display = 'inline-block';
        }
    }
    
    function updateReminderDropdown(reminders) {
        if (reminderList) {
            reminderList.innerHTML = '';
            
            reminders.forEach(reminder => {
                const reminderItem = document.createElement('li');
                
                // Zamanı şimdi oluştururken özel olarak biçimlendirme
                const reminderTime = reminder.time;
                
                // Hatırlatıcı öğesini oluştur
                let reminderHtml = `
                    <div class="dropdown-item d-flex align-items-center py-2">
                        <div class="me-3">
                            <i class="bi bi-bell-fill text-warning fs-4"></i>
                        </div>
                        <div class="small">
                            <div class="fw-bold">${reminder.title}</div>
                            <div class="text-muted">${reminder.message}</div>
                            <div class="text-primary mt-1">${reminderTime}</div>
                `;
                
                // İlgili bağlantıları ekle
                if (reminder.task_url) {
                    reminderHtml += `<a href="${reminder.task_url}" class="btn btn-sm btn-outline-primary mt-2">Görevi Görüntüle</a>`;
                }
                
                // HTML'i tamamla
                reminderHtml += `
                        </div>
                    </div>
                    <div class="dropdown-divider"></div>
                `;
                
                reminderItem.innerHTML = reminderHtml;
                reminderList.appendChild(reminderItem);
            });
        }
    }
    
    function showDesktopNotification(reminder) {
        // Web bildirimlerine izin verilmiş mi kontrol et
        if (Notification.permission === "granted") {
            const notification = new Notification("CRM Hatırlatıcı", {
                body: reminder.title + "\n" + reminder.message,
                icon: "/static/favicon.ico"
            });
            
            // Bildirime tıklandığında ilgili göreve yönlendir
            if (reminder.task_url) {
                notification.onclick = function() {
                    window.open(reminder.task_url);
                };
            }
        }
        // İzin istenmemişse iste
        else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    showDesktopNotification(reminder);
                }
            });
        }
    }
    
    // İlk kez bildirim izni iste
    if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        document.getElementById('notification-permission-btn')?.addEventListener('click', function() {
            Notification.requestPermission().then(function(permission) {
                if(permission === "granted") {
                    alert("Bildirim izni verildi. Artık hatırlatıcılar için bildirim alacaksınız.");
                }
            });
        });
    }
});
