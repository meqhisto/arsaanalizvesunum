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

    });

// SWOT yönetimi için fonksiyonlar
window.ekleSwot = function(type) {
        const elements = {
            'strength': {
                inputId: 'yeniStrength',
                listId: 'strengthList',
                hiddenId: 'strengthsInput',
                btnClass: 'btn-success'
            },
            'weakness': {
                inputId: 'yeniWeakness',
                listId: 'weaknessList',
                hiddenId: 'weaknessesInput',
                btnClass: 'btn-danger'
            },
            'opportunity': {
                inputId: 'yeniOpportunity',
                listId: 'opportunityList',
                hiddenId: 'opportunitiesInput',
                btnClass: 'btn-info'
            },
            'threat': {
                inputId: 'yeniThreat',
                listId: 'threatList',
                hiddenId: 'threatsInput',
                btnClass: 'btn-warning'
            }
        };

        const element = elements[type];
        const yeniItem = document.getElementById(element.inputId).value.trim();

        if (yeniItem) {
            const liste = document.getElementById(element.listId);
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            listItem.innerHTML = `
                ${yeniItem}
                <button class="btn btn-sm ${element.btnClass}" onclick="this.parentElement.remove(); updateSwotList('${type}');">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            liste.appendChild(listItem);
            document.getElementById(element.inputId).value = '';
            updateSwotList(type);
        }
    }

    function updateSwotList(type) {
        const elements = {
            'strength': {
                listId: 'strengthList',
                hiddenId: 'strengthsInput'
            },
            'weakness': {
                listId: 'weaknessList',
                hiddenId: 'weaknessesInput'
            },
            'opportunity': {
                listId: 'opportunityList',
                hiddenId: 'opportunitiesInput'
            },
            'threat': {
                listId: 'threatList',
                hiddenId: 'threatsInput'
            }
        };

        const element = elements[type];
        const items = [];
        document.querySelectorAll(`#${element.listId} .list-group-item`).forEach(item => {
            items.push(item.textContent.trim());
        });
        document.getElementById(element.hiddenId).value = JSON.stringify(items);
    }
});