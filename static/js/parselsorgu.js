// Parselsorgu ve Bölge Fiyat işlemleri için JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Parsel Bilgilerini Getir butonu
    const parselsorguBtn = document.getElementById('parselsorgu');
    // Bölge Fiyat Bilgilerini Getir butonu
    const bolgeFiyatGetirBtn = document.getElementById('bolgeFiyatGetir');
    // Yükleniyor göstergesi
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Parsel Bilgilerini Getir butonu tıklama olayı
    if (parselsorguBtn) {
        parselsorguBtn.addEventListener('click', function() {
            // Form alanlarını al
            const il = document.getElementById('il').value;
            const ilce = document.getElementById('ilce').value;
            const mahalle = document.getElementById('mahalle').value;
            const ada = document.getElementById('ada').value;
            const parsel = document.getElementById('parsel').value;
            
            // Alanların dolu olup olmadığını kontrol et
            if (!il || !ilce || !mahalle || !ada || !parsel) {
                alert('Lütfen tüm parsel bilgilerini doldurunuz.');
                return;
            }
            
            // Yükleniyor göstergesini göster
            loadingOverlay.style.display = 'flex';
            
            // AJAX isteği gönder
            fetch('/parselsorgu', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    il: il,
                    ilce: ilce,
                    mahalle: mahalle,
                    ada: ada,
                    parsel: parsel
                }),
            })
            .then(response => response.json())
            .then(data => {
                // Yükleniyor göstergesini gizle
                loadingOverlay.style.display = 'none';
                
                if (data.error) {
                    alert('Hata: ' + data.error);
                    return;
                }
                
                // Metrekare alanını doldur
                if (data.alan) {
                    document.getElementById('metrekare').value = data.alan;
                }
                
                // Başarı mesajı göster
                alert('Parsel bilgileri başarıyla getirildi.');
            })
            .catch(error => {
                // Yükleniyor göstergesini gizle
                loadingOverlay.style.display = 'none';
                
                console.error('Hata:', error);
                alert('Parsel bilgileri getirilirken bir hata oluştu.');
            });
        });
    }
    
    // Bölge Fiyat Bilgilerini Getir butonu tıklama olayı
    if (bolgeFiyatGetirBtn) {
        bolgeFiyatGetirBtn.addEventListener('click', function() {
            // Form alanlarını al
            const il = document.getElementById('il').value;
            const ilce = document.getElementById('ilce').value;
            const mahalle = document.getElementById('mahalle').value;
            const imarDurumu = document.getElementById('imar_durumu').value;
            
            // Alanların dolu olup olmadığını kontrol et
            if (!il || !ilce || !mahalle) {
                alert('Lütfen il, ilçe ve mahalle bilgilerini doldurunuz.');
                return;
            }
            
            // Yükleniyor göstergesini göster
            loadingOverlay.style.display = 'flex';
            
            // AJAX isteği gönder
            fetch('/bolge-fiyat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    il: il,
                    ilce: ilce,
                    mahalle: mahalle,
                    imar_durumu: imarDurumu
                }),
            })
            .then(response => response.json())
            .then(data => {
                // Yükleniyor göstergesini gizle
                loadingOverlay.style.display = 'none';
                
                if (data.error) {
                    alert('Hata: ' + data.error);
                    return;
                }
                
                // Bölge fiyat alanını doldur
                if (data.ortalama_metrekare_fiyat) {
                    document.getElementById('bolge_fiyat').value = data.ortalama_metrekare_fiyat.toFixed(2);
                }
                
                // Sonuç bilgilerini göster
                const bolgeFiyatSonuc = document.getElementById('bolgeFiyatSonuc');
                if (bolgeFiyatSonuc) {
                    bolgeFiyatSonuc.innerHTML = `
                        <div class="alert alert-info">
                            <strong>Bölge Fiyat Bilgileri:</strong><br>
                            Ortalama m² Fiyatı: ${data.ortalama_metrekare_fiyat.toFixed(2)} TL/m²<br>
                            Minimum m² Fiyatı: ${data.min_metrekare_fiyat.toFixed(2)} TL/m²<br>
                            Maksimum m² Fiyatı: ${data.max_metrekare_fiyat.toFixed(2)} TL/m²<br>
                            İncelenen İlan Sayısı: ${data.ilan_sayisi}
                        </div>
                    `;
                }
                
                // Başarı mesajı göster
                alert('Bölge fiyat bilgileri başarıyla getirildi.');
            })
            .catch(error => {
                // Yükleniyor göstergesini gizle
                loadingOverlay.style.display = 'none';
                
                console.error('Hata:', error);
                alert('Bölge fiyat bilgileri getirilirken bir hata oluştu.');
            });
        });
    }
    
    // İmar durumu değiştiğinde TAKS/KAKS alanlarını göster/gizle
    const imarDurumuSelect = document.getElementById('imar_durumu');
    const taksKaksRow = document.getElementById('taksKaksRow');
    
    if (imarDurumuSelect && taksKaksRow) {
        // Sayfa yüklendiğinde kontrol et
        if (imarDurumuSelect.value === 'konut' || imarDurumuSelect.value === 'ticari' || imarDurumuSelect.value === 'karma') {
            taksKaksRow.style.display = 'flex';
        } else {
            taksKaksRow.style.display = 'none';
        }
        
        // İmar durumu değiştiğinde kontrol et
        imarDurumuSelect.addEventListener('change', function() {
            if (this.value === 'konut' || this.value === 'ticari' || this.value === 'karma') {
                taksKaksRow.style.display = 'flex';
            } else {
                taksKaksRow.style.display = 'none';
            }
        });
    }
});
