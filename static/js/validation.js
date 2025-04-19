document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll(".needs-validation");
    forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            // Tüm SWOT listelerini güncelle
            ["strength", "weakness", "opportunity", "threat"].forEach(
                updateSwotList,
            );
            form.classList.add("was-validated");
        });
    });

    // SWOT ekleme fonksiyonu
    window.ekleSwot = function (type) {
        const input = document.getElementById(
            `yeni${type.charAt(0).toUpperCase() + type.slice(1)}`,
        );
        const list = document.getElementById(`${type}List`);
        const hiddenInput = document.getElementById(`${type}sInput`);

        if (input.value.trim()) {
            const newItem = document.createElement("div");
            newItem.className =
                "list-group-item d-flex justify-content-between";
            newItem.innerHTML = `
                ${input.value}
                <button class="btn btn-sm btn-danger" onclick="removeSwotItem(this, '${type}')">×</button>
            `;
            list.appendChild(newItem);
            input.value = "";
            updateSwotList(type);

            // Başlangıçta boş liste oluştur
            if (!hiddenInput.value) {
                hiddenInput.value = '[]';
            }
        }
    };

    // SWOT öğesi silme
    window.removeSwotItem = function (button, type) {
        button.closest(".list-group-item").remove();
        updateSwotList(type);
    };
    // SWOT listesini JSON'a dönüştür
    function updateSwotList(type) {
        const list = document.getElementById(`${type}List`);
        const hiddenInput = document.getElementById(`${type}sInput`);
        const items = Array.from(list.children).map((item) =>
            item.textContent.replace("×", "").trim(),
        );
        hiddenInput.value = JSON.stringify(items);
        console.log(`${type} updated:`, hiddenInput.value); // Debug için log
    }

    // Metrekare fiyatı otomatik hesaplama
    const fiyatInput = document.getElementById("fiyat");
    const metrekareInput = document.getElementById("metrekare");

    if (fiyatInput && metrekareInput) {
        function hesaplaMetrekareFiyat() {
            const fiyat = parseFloat(fiyatInput.value);
            const metrekare = parseFloat(metrekareInput.value);

            if (!isNaN(fiyat) && !isNaN(metrekare) && metrekare > 0) {
                const metrekareFiyat = fiyat / metrekare;
                console.log(
                    `Metrekare Fiyatı: ${metrekareFiyat.toFixed(2)} TL/m²`,
                );
            }
        }

        fiyatInput.addEventListener("input", hesaplaMetrekareFiyat);
        metrekareInput.addEventListener("input", hesaplaMetrekareFiyat);
    }

    // Sayısal girişler için doğrulama
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach((input) => {
        input.addEventListener("blur", () => {
            if (input.value !== "") {
                let value = parseFloat(input.value);
                if (!isNaN(value)) {
                    if (value < parseFloat(input.min)) {
                        input.value = input.min;
                    }
                    if (input.max && value > parseFloat(input.max)) {
                        input.value = input.max;
                    }
                }
            }
        });
    });

    // Form temizleme
    document.getElementById("clearForm").addEventListener("click", () => {
        const form = document.getElementById("arsaForm");
        form.reset();
        form.classList.remove("was-validated");

        // SWOT listelerini temizle
        ["strength", "weakness", "opportunity", "threat"].forEach((type) => {
            document.getElementById(`${type}List`).innerHTML = "";
            document.getElementById(`${type}sInput`).value = "[]";
        });

        // Checkbox'ları temizle
        form.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
            checkbox.checked = false;
        });

        alert("Form başarıyla temizlendi!");
    });

    // Parsel bilgisi getirme işlemi (örnek)
    document.getElementById("parselsorgu").addEventListener("click", () => {
        // Buraya API entegrasyonu veya mock veri çekme işlemi eklenebilir
        alert("Parsel sorgulama özelliği henüz aktif değil!");
    });

    // Bölge fiyatı getirme işlemi (örnek)
    document.getElementById("bolgeFiyatGetir").addEventListener("click", () => {
        // Buraya API entegrasyonu veya mock veri çekme işlemi eklenebilir
        alert("Bölge fiyatı getirme özelliği henüz aktif değil!");
    });
});
