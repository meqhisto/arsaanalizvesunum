document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll(".needs-validation");
    forms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            let isValid = form.checkValidity(); // Bootstrap validasyonu

            // Ek Özel Validasyonlar
            const adaInput = form.querySelector('#ada');
            const parselInput = form.querySelector('#parsel');
            const koordinatlarInput = form.querySelector('#koordinatlar');
            const notlarInput = form.querySelector('#notlar');
            const nitelikInput = form.querySelector('#nitelik'); // Nitelik input'u
            const taksKaksContainer = document.getElementById('taks-kaks-container'); // TAKS/KAKS container

            // Ada/Parsel (Sadece sayı)
            const adaParselRegex = /^\d+$/;
            if (adaInput && adaInput.value.trim() && !adaParselRegex.test(adaInput.value.trim())) {
                isValid = false;
                adaInput.classList.add('is-invalid'); // Hata stili ekle
                // Özel hata mesajı gösterilebilir (örn. bir div içinde)
                alert('Ada numarası sadece sayı içermelidir.');
            } else if (adaInput) {
                 adaInput.classList.remove('is-invalid'); // Hata yoksa stili kaldır
            }

            if (parselInput && parselInput.value.trim() && !adaParselRegex.test(parselInput.value.trim())) {
                isValid = false;
                parselInput.classList.add('is-invalid');
                alert('Parsel numarası sadece sayı içermelidir.');
            } else if (parselInput) {
                 parselInput.classList.remove('is-invalid');
            }

            // Koordinatlar (örn: 40.7128, -74.0060)
            // Daha esnek bir regex: ondalık veya tam sayı, arada virgül, boşluk olabilir
            const koordinatRegex = /^\s*[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)\s*,\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)\s*$/;
            // Koordinat alanı boş değilse ve formata uymuyorsa hata ver
            if (koordinatlarInput && koordinatlarInput.value.trim() && !koordinatRegex.test(koordinatlarInput.value.trim())) {
                isValid = false;
                koordinatlarInput.classList.add('is-invalid');
                alert('Koordinatlar geçerli bir formatta (örn. 40.7128, -74.0060) olmalıdır.');
            } else if (koordinatlarInput) {
                 koordinatlarInput.classList.remove('is-invalid');
            }

            // Notlar (Maksimum 1000 karakter)
            const maxNotlarLength = 1000;
            if (notlarInput && notlarInput.value.length > maxNotlarLength) {
                isValid = false;
                notlarInput.classList.add('is-invalid');
                alert(`Notlar alanı en fazla ${maxNotlarLength} karakter olmalıdır.`);
            } else if (notlarInput) {
                 notlarInput.classList.remove('is-invalid');
            }

            // TAKS/KAKS alanlarının görünürlüğüne göre validasyon (Eğer görünürse zorunlu değil, ama girilmişse geçerli olmalı)
            if (taksKaksContainer && taksKaksContainer.style.display !== 'none') {
                 const taksInput = form.querySelector('#taks');
                 const kaksInput = form.querySelector('#kaks');
                 // Gerekirse TAKS/KAKS için ek validasyonlar buraya eklenebilir
                 // Örneğin, boş olmamalı veya belirli bir aralıkta olmalı gibi
                 // if (!taksInput.value) { isValid = false; taksInput.classList.add('is-invalid'); }
                 // if (!kaksInput.value) { isValid = false; kaksInput.classList.add('is-invalid'); }
            }


            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
                // Genel bir hata mesajı da gösterilebilir
                // alert('Lütfen formdaki hataları düzeltin.');
            } else {
                 // Tüm SWOT listelerini güncelle (sadece form geçerliyse)
                ["strength", "weakness", "opportunity", "threat"].forEach(
                    updateSwotList,
                );
            }

            form.classList.add("was-validated"); // Bootstrap stillerini uygula
        });
    });

    // --- SWOT Analizi Geliştirmeleri Başlangıç ---

    // Önceden Tanımlanmış SWOT Seçenekleri
    const predefinedSwot = {
        strength: ["Merkezi Konum", "Gelişen Bölge", "Ulaşım Kolaylığı", "Yüksek İmar Hakkı", "Altyapı Tamamlanmış"],
        weakness: ["Yüksek Maliyet", "İmar Sorunları", "Altyapı Eksikliği", "Ulaşım Zorluğu", "Rekabet Yoğunluğu"],
        opportunity: ["Bölgesel Gelişim Projeleri", "Yeni Ulaşım Hatları", "Artan Talep", "Turizm Potansiyeli", "Devlet Teşvikleri"],
        threat: ["Ekonomik Dalgalanmalar", "Yasal Düzenleme Değişiklikleri", "Doğal Afet Riski", "Rekabet Artışı", "Altyapı Projelerinin Gecikmesi"]
    };

    // SWOT ekleme fonksiyonu (Önceden tanımlı seçenekleri de ekleyebilecek şekilde güncellendi)
    window.ekleSwot = function (type, value = null) {
        const input = document.getElementById(
            `yeni${type.charAt(0).toUpperCase() + type.slice(1)}`,
        );
        const list = document.getElementById(`${type}List`);
        const hiddenInput = document.getElementById(`${type}sInput`);
        const itemValue = value || input.value.trim(); // Eğer değer parametre olarak gelmişse onu kullan, yoksa input'tan al

        if (itemValue) {
            // Aynı öğenin tekrar eklenmesini engelle (isteğe bağlı)
            const existingItems = Array.from(list.children).map(item => item.textContent.replace("×", "").trim());
            if (existingItems.includes(itemValue)) {
                alert("Bu madde zaten listede mevcut.");
                return;
            }

            const newItem = document.createElement("div");
            newItem.className =
                "list-group-item d-flex justify-content-between align-items-center"; // align-items-center eklendi
            newItem.innerHTML = `
                <span>${itemValue}</span>
                <button type="button" class="btn btn-sm btn-outline-danger p-1" onclick="removeSwotItem(this, '${type}')" style="line-height: 1;">×</button>
            `; // Buton stili ve içeriği güncellendi
            list.appendChild(newItem);

            if (!value) { // Eğer manuel ekleme yapıldıysa input'u temizle
                 input.value = "";
            }

            // Liste güncellemesini yap
            updateSwotList(type);
        }
    };

    // Önceden tanımlı SWOT seçeneklerini gösterme fonksiyonu
    window.gosterOnTanimliSwot = function(type) {
        const options = predefinedSwot[type];
        if (!options || options.length === 0) {
            alert("Bu kategori için önceden tanımlanmış seçenek bulunmamaktadır.");
            return;
        }

        // Seçenekleri kullanıcıya sunma (şimdilik basit bir prompt ile)
        // Daha gelişmiş bir arayüz için modal veya dropdown kullanılabilir.
        let message = `"${type.charAt(0).toUpperCase() + type.slice(1)}" için önerilen seçenekler:\n`;
        options.forEach((option, index) => {
            message += `${index + 1}. ${option}\n`;
        });
        message += "\nEklemek istediğiniz seçeneğin numarasını girin (veya iptal için boş bırakın):";

        const choice = prompt(message);
        if (choice) {
            const index = parseInt(choice) - 1;
            if (index >= 0 && index < options.length) {
                ekleSwot(type, options[index]); // Seçilen öğeyi ekleSwot fonksiyonuna gönder
            } else {
                alert("Geçersiz seçim.");
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
        const items = Array.from(list.children).map((item) =>
            // Sadece span içindeki metni al
            item.querySelector('span') ? item.querySelector('span').textContent.trim() : ''
        ).filter(item => item); // Boş stringleri filtrele

        // Doğru çoğul ID'leri için mapping
        const typeMapping = {
            strength: "strengths",
            weakness: "weaknesses",
            opportunity: "opportunities",
            threat: "threats",
        };

        const hiddenId = typeMapping[type] + "Input"; // Örn: weaknessesInput
        document.getElementById(hiddenId).value = JSON.stringify(items);
        console.log(`${type} updated:`, document.getElementById(hiddenId).value); // Güncellenen değeri logla
    }

    // --- SWOT Analizi Geliştirmeleri Bitiş ---


    // Metrekare fiyatı otomatik hesaplama
    const maliyetInput = document.getElementById("maliyet"); // ID 'maliyet' olarak güncellendi
    const metrekareInput = document.getElementById("metrekare");
    const birimMaliyetInput = document.getElementById('birim_maliyet'); // Birim maliyet alanı

    if (metrekareInput && birimMaliyetInput) { // fiyatInput kontrolü kaldırıldı, maliyet zaten var
        function hesaplaBirimMaliyet() {
            const maliyet = parseFloat(maliyetInput ? maliyetInput.value.replace(',', '.') : 0); // fiyatInput -> maliyetInput
            const metrekare = parseFloat(metrekareInput.value.replace(',', '.'));

            if (!isNaN(maliyet) && !isNaN(metrekare) && metrekare > 0) {
                const birimMaliyet = maliyet / metrekare;
                 birimMaliyetInput.value = birimMaliyet.toFixed(2);
                console.log(
                    `Birim Maliyet: ${birimMaliyet.toFixed(2)} TL/m²`,
                );
            } else {
                 birimMaliyetInput.value = '';
            }
        }

        if(maliyetInput) maliyetInput.addEventListener("input", hesaplaBirimMaliyet); // fiyatInput -> maliyetInput
        metrekareInput.addEventListener("input", hesaplaBirimMaliyet);
        // Ayrıca güncel değer için de benzer bir hesaplama yapılabilir (birim_deger alanı için)
    }

    // Sayısal girişler için doğrulama
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach((input) => {
        input.addEventListener("blur", () => {
            if (input.value !== "") {
                let value = parseFloat(input.value.replace(',', '.')); // Virgülü noktaya çevir
                if (!isNaN(value)) {
                    if (input.min && value < parseFloat(input.min)) { // min kontrolü eklendi
                        input.value = input.min;
                    }
                    if (input.max && value > parseFloat(input.max)) {
                        input.value = input.max;
                    }
                    // Adım kontrolü (step) - İsteğe bağlı
                    // if (input.step && input.step !== 'any') {
                    //     const step = parseFloat(input.step);
                    //     input.value = (Math.round(value / step) * step).toFixed(step.toString().split('.')[1]?.length || 0);
                    // }
                } else {
                    // Geçersiz sayısal giriş durumunda alanı temizle veya hata göster
                    // input.value = '';
                }
            }
        });
         // Virgül yerine nokta kullanımını sağlamak için input event'i
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(',', '.');
        });
    });

    // Form temizleme
    const clearFormButton = document.getElementById("clearForm"); // Butonu seç
    if (clearFormButton) { // Buton varsa event listener ekle
        clearFormButton.addEventListener("click", () => {
            const form = document.getElementById("arsaAnaliz"); // Form ID'si 'arsaAnaliz' olmalı, düzeltildi.
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

            // Hata stillerini kaldır
            form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

            // TAKS/KAKS alanını göster (varsayılan durum)
            const taksKaksContainer = document.getElementById('taks-kaks-container');
            if (taksKaksContainer) {
                taksKaksContainer.style.display = ''; // veya 'flex' veya 'block' duruma göre
            }

            alert("Form başarıyla temizlendi!");
        });
    } else {
        console.warn("Element with ID 'clearForm' not found."); // Buton bulunamazsa uyar
    }


    // Parsel bilgisi getirme işlemi (örnek)
    // const parselsorguButton = document.getElementById("parselsorgu"); // ID kontrolü
    // if (parselsorguButton) {
    //     parselsorguButton.addEventListener("click", () => {
    //         // Buraya API entegrasyonu veya mock veri çekme işlemi eklenebilir
    //         alert("Parsel sorgulama özelliği henüz aktif değil!");
    //     });
    // } else {
    //     console.warn("Element with ID 'parselsorgu' not found.");
    // }


    // Bölge fiyatı getirme işlemi (örnek)
    // const bolgeFiyatGetirButton = document.getElementById("bolgeFiyatGetir"); // ID kontrolü
    // if (bolgeFiyatGetirButton) {
    //     bolgeFiyatGetirButton.addEventListener("click", () => {
    //         // Buraya API entegrasyonu veya mock veri çekme işlemi eklenebilir
    //         alert("Bölge fiyatı getirme özelliği henüz aktif değil!");
    //     });
    // } else {
    //      console.warn("Element with ID 'bolgeFiyatGetir' not found.");
    // }

     // JSON Dosyası Yükleme ve Formu Doldurma
    const jsonDosyaInput = document.getElementById('jsonDosya');
    if (jsonDosyaInput) {
        console.log("JSON Dosya Input bulundu. Event listener ekleniyor."); // DEBUG
        jsonDosyaInput.addEventListener('change', function(event) {
            console.log("JSON Dosya seçildi."); // DEBUG
            const file = event.target.files[0];
            if (file && file.type === "application/json") {
                console.log("JSON Dosyası geçerli."); // DEBUG
                const reader = new FileReader();
                reader.onload = function(e) {
                    console.log("JSON Dosyası okundu."); // DEBUG
                    try {
                        const jsonData = JSON.parse(e.target.result);
                        console.log("JSON Parse edildi:", jsonData); // DEBUG
                        const form = document.getElementById('arsaAnaliz');
                        // TKGM JSON yapısına göre özelliklere erişim (features dizisinin ilk elemanı)
                        const properties = jsonData?.features?.[0]?.properties;

                        if (!properties) {
                             console.error("JSON 'properties' alanı bulunamadı."); // DEBUG
                             alert('JSON dosyasında beklenen "features[0].properties" alanı bulunamadı.');
                             event.target.value = null; // Dosya seçimini temizle
                             return;
                        }

                        console.log("JSON Properties:", properties); // Yüklenen özellikleri logla

                        // Alanları doldur (JSON anahtarlarının büyük/küçük harf duyarlılığına dikkat)
                        form.querySelector('#il').value = properties.Il || properties.il || '';
                        form.querySelector('#ilce').value = properties.Ilce || properties.ilce || '';
                        form.querySelector('#mahalle').value = properties.Mahalle || properties.mahalleAdi || ''; // TKGM'de MahalleAdi olabilir
                        form.querySelector('#ada').value = properties.Ada || properties.adaNo || ''; // TKGM'de adaNo olabilir
                        form.querySelector('#parsel').value = properties.ParselNo || properties.parselNo || '';
                        form.querySelector('#pafta').value = properties.Pafta || properties.pafta || '';

                        // Alan değerini temizle ve doldur (noktayı kaldır, virgülü noktaya çevir)
                        const alanStr = (properties.Alan || properties.alan || '').toString().replace(/\./g, '').replace(',', '.');
                        form.querySelector('#metrekare').value = parseFloat(alanStr) || '';
                        console.log("Metrekare dolduruldu:", form.querySelector('#metrekare').value); // DEBUG

                        // Nitelik alanını doldur
                        const nitelik = properties.Nitelik || properties.nitelik || properties.zeminKmdurum || ''; // Olası alan adları
                        const nitelikInput = form.querySelector('#nitelik');
                        if (nitelikInput) {
                            nitelikInput.value = nitelik;
                            console.log("Nitelik dolduruldu:", nitelik); // DEBUG
                        } else {
                            console.warn("Nitelik input alanı bulunamadı."); // DEBUG
                        }

                        // Koordinatları formatla (varsa)
                        const geometry = jsonData?.features?.[0]?.geometry;
                        let lat = '';
                        let lon = '';
                        // Doğrudan erişim denemesi
                        try {
                            if (geometry?.type === 'Polygon' && geometry?.coordinates?.[0]?.[0]?.length === 2) {
                                lon = geometry.coordinates[0][0][0]; // Longitude
                                lat = geometry.coordinates[0][0][1]; // Latitude
                                console.log(`Polygon koordinatları alındı (doğrudan): lat=${lat}, lon=${lon}`); // DEBUG
                            } else if (geometry?.type === 'Point' && geometry?.coordinates?.length === 2) {
                                lon = geometry.coordinates[0];
                                lat = geometry.coordinates[1];
                                console.log(`Point koordinatları alındı (doğrudan): lat=${lat}, lon=${lon}`); // DEBUG
                            } else {
                                console.warn("Desteklenmeyen geometri tipi veya geçersiz koordinat yapısı (doğrudan erişim):", geometry); // DEBUG
                            }
                        } catch (coordError) {
                             console.error("Koordinatlara erişirken hata:", coordError); // DEBUG
                             lat = '';
                             lon = '';
                        }


                        // Değerlerin geçerli olup olmadığını kontrol et
                        console.log(`Kontrol öncesi: lat=${lat} (${typeof lat}), lon=${lon} (${typeof lon})`); // DEBUG
                        if (typeof lat === 'number' && typeof lon === 'number' && !isNaN(lat) && !isNaN(lon)) {
                             form.querySelector('#koordinatlar').value = `${lat}, ${lon}`; // lat, lon formatında yaz
                             console.log("Koordinatlar dolduruldu:", form.querySelector('#koordinatlar').value); // DEBUG
                        } else {
                             form.querySelector('#koordinatlar').value = '';
                             console.log("Koordinatlar bulunamadı veya geçerli sayısal değerler değil."); // DEBUG
                        }

                        // Mevkii bilgisini Notlar alanına ekle (varsa)
                        const mevkii = properties.Mevkii || properties.mevkii || '';
                        const notlarInput = form.querySelector('#notlar');
                        if (notlarInput && mevkii) {
                            const mevcutNotlar = notlarInput.value ? notlarInput.value + '\n' : '';
                            notlarInput.value = mevcutNotlar + `Mevkii (JSON): ${mevkii}`;
                            console.log("Mevkii notlara eklendi."); // DEBUG
                        }

                        // Nitelik değerine göre TAKS/KAKS alanlarını gizle/göster
                        const taksKaksContainer = document.getElementById('taks-kaks-container');
                        if (taksKaksContainer) {
                            // Nitelik "Arsa" içeriyorsa göster, değilse gizle (büyük/küçük harf duyarsız)
                            console.log("Nitelik kontrolü (TAKS/KAKS için):", nitelik.toLowerCase()); // Kontrol edilecek değeri logla
                            if (nitelik && nitelik.toLowerCase().includes('arsa')) {
                                console.log("TAKS/KAKS gösteriliyor.");
                                taksKaksContainer.style.display = ''; // Varsayılan görünüm (row)
                            } else {
                                console.log("TAKS/KAKS gizleniyor.");
                                taksKaksContainer.style.display = 'none';
                            }
                        } else {
                             console.warn("TAKS/KAKS container bulunamadı."); // DEBUG
                        }


                        alert('JSON dosyasından bilgiler yüklendi.');
                        // Birim fiyatları yeniden hesapla (Maliyet ve Güncel Değer JSON'da olmadığı için hesaplanamaz)
                        // calculateBirimFiyat();

                    } catch (error) {
                        console.error("JSON parse veya alan doldurma hatası:", error); // DEBUG
                        alert('JSON dosyası işlenirken bir hata oluştu. Lütfen konsolu kontrol edin.');
                    }
                };
                reader.onerror = function(e) { // Hata durumunu yakala
                    console.error("FileReader hatası:", e); // DEBUG
                    alert('Dosya okunurken bir hata oluştu.');
                };
                reader.readAsText(file);
            } else if (file) {
                alert('Lütfen geçerli bir JSON dosyası seçin.');
                event.target.value = null; // Geçersiz dosya seçimini temizle
            }
        });
    } else {
        console.warn("Element with ID 'jsonDosya' not found."); // DEBUG
    }

     // Medya dosyası seçildiğinde isimlerini gösterme
    const medyaInput = document.getElementById('medya');
    const secilenDosyalarDiv = document.getElementById('secilenDosyalar');
    if (medyaInput && secilenDosyalarDiv) {
        medyaInput.addEventListener('change', function() {
            secilenDosyalarDiv.innerHTML = ''; // Önceki listeyi temizle
            if (this.files.length > 0) {
                const list = document.createElement('ul');
                list.classList.add('list-unstyled', 'list-group', 'list-group-flush');
                for (let i = 0; i < this.files.length; i++) {
                    const listItem = document.createElement('li');
                    listItem.classList.add('list-group-item', 'list-group-item-action', 'list-group-item-light', 'py-1', 'px-2', 'mb-1', 'rounded');
                    listItem.textContent = this.files[i].name;
                    list.appendChild(listItem);
                }
                secilenDosyalarDiv.appendChild(list);
            }
        });
    }

});
