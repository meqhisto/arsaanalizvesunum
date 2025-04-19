
// Favoriler işlemleri
document.addEventListener('DOMContentLoaded', function() {
    const saveAsFavoriteBtn = document.getElementById('saveAsFavorite');
    const favoritesListDiv = document.getElementById('favoritesList');
    
    // Local storage'dan favorileri al
    function getFavorites() {
        return JSON.parse(localStorage.getItem('arsaFavoriler')) || [];
    }

    // Favori ekle
    saveAsFavoriteBtn.addEventListener('click', function() {
        const formData = new FormData(document.getElementById('arsaForm'));
        const favorite = {
            il: formData.get('il'),
            ilce: formData.get('ilce'),
            mahalle: formData.get('mahalle'),
            metrekare: formData.get('metrekare'),
            fiyat: formData.get('fiyat'),
            timestamp: new Date().toLocaleString()
        };
        
        const favorites = getFavorites();
        favorites.push(favorite);
        localStorage.setItem('arsaFavoriler', JSON.stringify(favorites));
        
        updateFavoritesList();
        alert('Favori olarak kaydedildi!');
    });

    // Favoriler listesini güncelle
    function updateFavoritesList() {
        const favorites = getFavorites();
        favoritesListDiv.innerHTML = '';
        
        favorites.forEach((fav, index) => {
            const favItem = document.createElement('div');
            favItem.className = 'favorite-item';
            favItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center border-bottom p-2">
                    <div>
                        <strong>${fav.il}, ${fav.ilce}</strong> - ${fav.mahalle}<br>
                        ${fav.metrekare}m² - ${Number(fav.fiyat).toLocaleString('tr-TR')} TL
                    </div>
                    <button class="btn btn-sm btn-danger" onclick="removeFavorite(${index})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
            favoritesListDiv.appendChild(favItem);
        });
    }

    // Favori silme fonksiyonu
    window.removeFavorite = function(index) {
        const favorites = getFavorites();
        favorites.splice(index, 1);
        localStorage.setItem('arsaFavoriler', JSON.stringify(favorites));
        updateFavoritesList();
    };

    // Sayfa yüklendiğinde favorileri göster
    updateFavoritesList();
});
