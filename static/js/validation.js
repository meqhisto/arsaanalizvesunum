// Form validasyon script'i
document.addEventListener('DOMContentLoaded', function() {
    // Bootstrap form validasyonunu etkinleştir
    var forms = document.querySelectorAll('.needs-validation');

    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });

    // Metrekare fiyatı otomatik hesaplama
    var fiyatInput = document.getElementById('fiyat');
    var metrekareInput = document.getElementById('metrekare');

    if (fiyatInput && metrekareInput) {
        function hesaplaMetrekareFiyat() {
            var fiyat = parseFloat(fiyatInput.value);
            var metrekare = parseFloat(metrekareInput.value);

            if (!isNaN(fiyat) && !isNaN(metrekare) && metrekare > 0) {
                var metrekareFiyat = fiyat / metrekare;
                console.log("Metrekare fiyatı: " + metrekareFiyat.toFixed(2) + " TL/m²");
            }
        }

        fiyatInput.addEventListener('input', hesaplaMetrekareFiyat);
        metrekareInput.addEventListener('input', hesaplaMetrekareFiyat);
    }

    // Sayısal girişler için doğrulama
    var numberInputs = document.querySelectorAll('input[type="number"]');

    numberInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value !== '') {
                var value = parseFloat(this.value);
                if (!isNaN(value)) {
                    // Minimum değer kontrolü
                    if (value < parseFloat(this.min)) {
                        this.value = this.min;
                    }
                }
            }
        });
    });

    // Form temizleme işlevi
    const clearFormBtn = document.getElementById('clearForm');
    if (clearFormBtn) {
        clearFormBtn.addEventListener('click', function() {
            const form = document.getElementById('arsaForm');
            form.reset();
            form.classList.remove('was-validated');
            // Checkbox'ları temizle
            form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = false;
            });
            alert('Form temizlendi!');
        });
    }

    // Artı/Eksi yönetimi için global diziler
    let artilar = [];
    let eksiler = [];

    // Artı ekleme fonksiyonu
    window.ekleArti = function() {
        const input = document.getElementById('yeniArti');
        const arti = input.value.trim();
        if (arti) {
            artilar.push(arti);
            guncelleArtilarListesi();
            input.value = '';
            document.getElementById('artilarInput').value = JSON.stringify(artilar);
        }
    };

    // Eksi ekleme fonksiyonu
    window.ekleEksi = function() {
        const input = document.getElementById('yeniEksi');
        const eksi = input.value.trim();
        if (eksi) {
            eksiler.push(eksi);
            guncelleEksilerListesi();
            input.value = '';
            document.getElementById('eksilerInput').value = JSON.stringify(eksiler);
        }
    };

    // Artı silme fonksiyonu
    window.silArti = function(index) {
        artilar.splice(index, 1);
        guncelleArtilarListesi();
        document.getElementById('artilarInput').value = JSON.stringify(artilar);
    };

    // Eksi silme fonksiyonu
    window.silEksi = function(index) {
        eksiler.splice(index, 1);
        guncelleEksilerListesi();
        document.getElementById('eksilerInput').value = JSON.stringify(eksiler);
    };

    // Artılar listesini güncelleme
    function guncelleArtilarListesi() {
        const liste = document.getElementById('artilarListesi');
        liste.innerHTML = artilar.map((arti, index) => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>${arti}</span>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="silArti(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `).join('');
    }

    // Eksiler listesini güncelleme
    function guncelleEksilerListesi() {
        const liste = document.getElementById('eksilerListesi');
        liste.innerHTML = eksiler.map((eksi, index) => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>${eksi}</span>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="silEksi(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `).join('');
    }
});