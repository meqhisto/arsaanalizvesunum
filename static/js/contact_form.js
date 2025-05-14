document.addEventListener('DOMContentLoaded', function() {
    // Değer puanı göstergesini güncelle
    const valueScoreInput = document.getElementById('value_score');
    const valueScoreDisplay = document.getElementById('value_score_display');
    
    if (valueScoreInput && valueScoreDisplay) {
        valueScoreInput.addEventListener('input', function() {
            valueScoreDisplay.textContent = this.value;
        });
    }
    
    // Etiketleri yönetme
    const tagsInput = document.getElementById('tags_input');
    const addTagBtn = document.getElementById('add_tag_btn');
    const tagsContainer = document.getElementById('tags_container');
    const tagsHiddenInput = document.getElementById('tags');
    
    // Mevcut etiketleri yükle
    let tags = [];
    try {
        tags = JSON.parse(tagsHiddenInput.value);
    } catch (e) {
        tags = [];
    }
    
    // Etiketleri görüntüle
    function renderTags() {
        tagsContainer.innerHTML = '';
        tags.forEach((tag, index) => {
            const tagElement = document.createElement('span');
            tagElement.className = 'badge bg-light text-dark me-2 mb-2';
            tagElement.innerHTML = `${tag} <button type="button" class="btn-close btn-close-sm ms-1" aria-label="Kaldır" data-index="${index}"></button>`;
            tagsContainer.appendChild(tagElement);
        });
        
        // Etiket silme butonlarına olay dinleyicileri ekle
        document.querySelectorAll('#tags_container .btn-close').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                tags.splice(index, 1);
                tagsHiddenInput.value = JSON.stringify(tags);
                renderTags();
            });
        });
        
        // Gizli input'u güncelle
        tagsHiddenInput.value = JSON.stringify(tags);
    }
    
    // Yeni etiket ekleme
    function addTag() {
        const tagValue = tagsInput.value.trim();
        if (tagValue && !tags.includes(tagValue)) {
            tags.push(tagValue);
            tagsInput.value = '';
            renderTags();
        }
    }
    
    // Olay dinleyicileri
    if (addTagBtn) {
        addTagBtn.addEventListener('click', addTag);
    }
    
    if (tagsInput) {
        tagsInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addTag();
            }
        });
    }
    
    // İlk yükleme
    renderTags();
});
