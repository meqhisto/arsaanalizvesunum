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
    
    // Sayısal değerlerin formatlanması
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
});
