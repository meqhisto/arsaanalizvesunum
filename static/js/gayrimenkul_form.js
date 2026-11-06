/* Gayrimenkul formu: türe göre alanlar, JSON parsel yükleme, SWOT listeleri, mal sahipleri, hemen ilana çıkar. */
(function () {
  'use strict';
  const form = document.getElementById('gayrimenkulForm');
  if (!form) return;

  // ------------------------------------------------------------ türe göre alanlar
  function seciliTur() {
    const r = form.querySelector('input[name="tur"]:checked');
    return r ? r.value : 'arsa';
  }

  function turaUygun(el, tur) {
    for (let e = el; e && e !== form; e = e.parentElement) {
      if (e.dataset && e.dataset.turler && e.dataset.turler.split(' ').indexOf(tur) === -1) return false;
    }
    return true;
  }

  function turuUygula() {
    const tur = seciliTur();
    form.querySelectorAll('[data-turler]').forEach(function (blok) {
      blok.classList.toggle('d-none', blok.dataset.turler.split(' ').indexOf(tur) === -1);
    });
    // Gizlenen alanlar gönderilmez ve zorunlu sayılmaz
    form.querySelectorAll('input, select, textarea').forEach(function (alan) {
      if (alan.name === 'tur' || alan.id === 'jsonDosya' || alan.closest('#ilanAlanlari')) return;
      const uygun = turaUygun(alan, tur);
      alan.disabled = !uygun;
      const zorunlu = alan.hasAttribute('data-zorunlu') ||
        (alan.dataset.zorunluTur && alan.dataset.zorunluTur.split(' ').indexOf(tur) !== -1);
      alan.required = uygun && !!zorunlu;
    });
    // Alt tür seçenekleri
    const altTur = document.getElementById('alt_tur');
    if (altTur) {
      altTur.querySelectorAll('option[data-tur]').forEach(function (o) {
        o.hidden = o.dataset.tur !== tur;
        o.disabled = o.dataset.tur !== tur;
      });
      const secili = altTur.selectedOptions[0];
      if (secili && secili.dataset.tur && secili.dataset.tur !== tur) altTur.value = '';
    }
  }
  form.querySelectorAll('input[name="tur"]').forEach(function (r) { r.addEventListener('change', turuUygula); });
  turuUygula();

  // ------------------------------------------------------------ JSON ile parsel yükleme (TKGM)
  const jsonDosya = document.getElementById('jsonDosya');
  function yaz(id, deger) {
    const el = document.getElementById(id);
    if (el && deger !== undefined && deger !== null && deger !== '') el.value = deger;
  }
  if (jsonDosya) {
    jsonDosya.addEventListener('change', function (event) {
      const dosya = event.target.files[0];
      if (!dosya) return;
      const okuyucu = new FileReader();
      okuyucu.onload = function (e) {
        try {
          const veri = JSON.parse(e.target.result);
          const oz = (veri.features && veri.features[0] && veri.features[0].properties) || veri.properties;
          if (!oz) throw new Error('properties yok');
          yaz('il', oz.Il || oz.il || oz.ilAdi);
          yaz('ilce', oz.Ilce || oz.ilce || oz.ilceAdi);
          yaz('mahalle', oz.Mahalle || oz.mahalle || oz.mahalleAdi);
          yaz('ada', oz.Ada || oz.adaNo || oz.ada);
          yaz('parsel', oz.ParselNo || oz.parselNo || oz.parsel);
          yaz('pafta', oz.Pafta || oz.pafta);
          const alan = oz.Alan || oz.alan;
          if (alan !== undefined && alan !== null && alan !== '') {
            const s = String(alan);
            // "1.234,56" (TR) ya da "1234.56"
            const sayi = s.indexOf(',') !== -1 ? parseFloat(s.replace(/\./g, '').replace(',', '.')) : parseFloat(s);
            if (!isNaN(sayi)) yaz('metrekare', String(sayi).replace('.', ','));
          }
          const geo = (veri.features && veri.features[0] && veri.features[0].geometry) || veri.geometry;
          let nokta = null;
          if (geo && geo.type === 'Polygon') nokta = geo.coordinates[0][0];
          else if (geo && geo.type === 'MultiPolygon') nokta = geo.coordinates[0][0][0];
          else if (geo && geo.type === 'Point') nokta = geo.coordinates;
          if (nokta && typeof nokta[0] === 'number') yaz('koordinatlar', nokta[1] + ', ' + nokta[0]);
          const mevkii = oz.Mevkii || oz.mevkii;
          const notlar = document.getElementById('notlar');
          if (mevkii && notlar && notlar.value.indexOf(mevkii) === -1) {
            notlar.value = (notlar.value ? notlar.value + '\n' : '') + 'Mevkii: ' + mevkii;
          }
          bildir('Parsel bilgileri JSON dosyasından yüklendi.', 'success');
        } catch (hata) {
          bildir('JSON dosyası okunamadı veya beklenen biçimde değil.', 'error');
          event.target.value = '';
        }
      };
      okuyucu.readAsText(dosya);
    });
  }

  function bildir(mesaj, tip) {
    if (typeof window.showToast === 'function') window.showToast(mesaj, tip);
    else window.alert(mesaj);
  }

  // ------------------------------------------------------------ SWOT
  const ONERILER = {
    strength: ['Merkezi konum', 'Gelişen bölge', 'Ulaşım kolaylığı', 'Yüksek imar hakkı', 'Altyapı tamamlanmış'],
    weakness: ['İmar sorunları', 'Altyapı eksikliği', 'Ulaşım zorluğu', 'Hisseli tapu', 'Rekabet yoğunluğu'],
    opportunity: ['Bölgesel gelişim projeleri', 'Yeni ulaşım hatları', 'Artan talep', 'Turizm potansiyeli', 'Devlet teşvikleri'],
    threat: ['Ekonomik dalgalanmalar', 'Yasal düzenleme değişiklikleri', 'Doğal afet riski', 'Rekabet artışı', 'Altyapı projelerinin gecikmesi']
  };

  form.querySelectorAll('[data-swot]').forEach(function (kutu) {
    const tip = kutu.dataset.swot;
    const liste = kutu.querySelector('[data-swot-liste]');
    const gizli = kutu.querySelector('[data-swot-gizli]');
    const yeni = kutu.querySelector('[data-swot-yeni]');

    function maddeler() {
      return Array.from(liste.querySelectorAll('[data-madde]')).map(function (m) { return m.textContent; });
    }
    function guncelle() { gizli.value = JSON.stringify(maddeler()); }
    function ekle(metin) {
      metin = (metin || '').trim();
      if (!metin || maddeler().indexOf(metin) !== -1) return;
      const satir = document.createElement('div');
      satir.className = 'list-group-item d-flex justify-content-between align-items-center px-1 py-1';
      const yazi = document.createElement('span');
      yazi.dataset.madde = '';
      yazi.textContent = metin;
      const sil = document.createElement('button');
      sil.type = 'button';
      sil.className = 'btn btn-sm btn-link text-danger p-0';
      sil.setAttribute('aria-label', 'Sil');
      sil.innerHTML = '<i class="fas fa-times"></i>';
      sil.addEventListener('click', function () { satir.remove(); guncelle(); });
      satir.append(yazi, sil);
      liste.appendChild(satir);
      guncelle();
    }

    let mevcut = [];
    try { mevcut = JSON.parse(gizli.value || '[]'); } catch (e) { mevcut = []; }
    (Array.isArray(mevcut) ? mevcut : []).forEach(function (m) { ekle(String(m)); });

    kutu.querySelector('[data-swot-ekle]').addEventListener('click', function () { ekle(yeni.value); yeni.value = ''; });
    yeni.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); ekle(yeni.value); yeni.value = ''; }
    });
    kutu.querySelector('[data-swot-oneri]').addEventListener('click', function () {
      const secenekler = ONERILER[tip] || [];
      const secim = window.prompt('Önerilenler:\n' + secenekler.map(function (o, i) { return (i + 1) + '. ' + o; }).join('\n') +
        '\n\nEklemek istediğiniz numarayı yazın:');
      const i = parseInt(secim, 10) - 1;
      if (i >= 0 && i < secenekler.length) ekle(secenekler[i]);
    });
  });

  // ------------------------------------------------------------ seçilen fotoğraflar
  const medya = document.getElementById('medya');
  const secilen = document.getElementById('secilenDosyalar');
  if (medya && secilen) {
    medya.addEventListener('change', function () {
      secilen.textContent = Array.from(medya.files).map(function (f) { return f.name; }).join(', ');
    });
  }

  // ------------------------------------------------------------ mal sahipleri
  const sahipKutusu = document.getElementById('sahipler');
  if (sahipKutusu) {
    const araUrl = sahipKutusu.dataset.araUrl, ekleUrl = sahipKutusu.dataset.ekleUrl;
    const ara = document.getElementById('sahipAra'), sonuclar = document.getElementById('sahipSonuclar');
    const govde = document.getElementById('sahipSatirlari'), bos = document.getElementById('sahipBos');

    function bosGuncelle() { bos.classList.toggle('d-none', govde.children.length > 0); }

    function sahipEkle(k) {
      if (govde.querySelector('tr[data-id="' + k.id + '"]')) return;
      const tr = document.createElement('tr');
      tr.dataset.id = k.id;
      const kisi = document.createElement('td');
      const ad = document.createElement('div'); ad.textContent = k.ad;
      const tel = document.createElement('div'); tel.className = 'small text-muted'; tel.textContent = k.telefon || '';
      const gizli = document.createElement('input'); gizli.type = 'hidden'; gizli.name = 'sahip_contact_id[]'; gizli.value = k.id;
      kisi.append(ad, tel, gizli);
      const hisseTd = document.createElement('td');
      const hisse = document.createElement('input');
      hisse.className = 'form-control form-control-sm'; hisse.name = 'sahip_hisse[]'; hisse.maxLength = 20; hisse.placeholder = '1/2';
      hisseTd.appendChild(hisse);
      const irtTd = document.createElement('td'); irtTd.className = 'text-center';
      const irt = document.createElement('input');
      irt.className = 'form-check-input'; irt.type = 'radio'; irt.name = 'sahip_irtibat'; irt.value = k.id;
      irt.setAttribute('aria-label', 'İrtibat kişisi');
      if (!govde.querySelector('input[name="sahip_irtibat"]:checked')) irt.checked = true;
      irtTd.appendChild(irt);
      const silTd = document.createElement('td'); silTd.className = 'text-end';
      silTd.innerHTML = '<button type="button" class="btn btn-sm btn-link text-danger p-0" data-sahip-cikar aria-label="Çıkar"><i class="fas fa-times"></i></button>';
      tr.append(kisi, hisseTd, irtTd, silTd);
      govde.appendChild(tr);
      bosGuncelle();
    }

    govde.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-sahip-cikar]');
      if (btn) { btn.closest('tr').remove(); bosGuncelle(); }
    });

    let zamanlayici = null;
    ara.addEventListener('input', function () {
      clearTimeout(zamanlayici);
      const q = ara.value.trim();
      if (!q) { sonuclar.classList.add('d-none'); return; }
      zamanlayici = setTimeout(async function () {
        try {
          const r = await fetch(araUrl + '?q=' + encodeURIComponent(q), {headers: {'Accept': 'application/json'}});
          const liste = await r.json();
          sonuclar.innerHTML = '';
          if (!liste.length) {
            const yok = document.createElement('div');
            yok.className = 'list-group-item small text-muted';
            yok.textContent = 'Sonuç yok. "Yeni müşteri ekle" ile oluşturabilirsiniz.';
            sonuclar.appendChild(yok);
          }
          liste.forEach(function (k) {
            const a = document.createElement('button');
            a.type = 'button';
            a.className = 'list-group-item list-group-item-action small';
            a.textContent = k.ad + (k.telefon ? ' · ' + k.telefon : '');
            a.addEventListener('click', function () {
              sahipEkle(k); ara.value = ''; sonuclar.classList.add('d-none');
            });
            sonuclar.appendChild(a);
          });
          sonuclar.classList.remove('d-none');
        } catch (hata) {
          sonuclar.classList.add('d-none');
        }
      }, 250);
    });
    document.addEventListener('click', function (e) {
      if (!sahipKutusu.contains(e.target)) sonuclar.classList.add('d-none');
    });

    const kaydet = document.getElementById('yeniSahipKaydet'), hataKutusu = document.getElementById('yeniSahipHata');
    kaydet.addEventListener('click', async function () {
      const adEl = document.getElementById('yeniSahipAd');
      const soyadEl = document.getElementById('yeniSahipSoyad');
      const telEl = document.getElementById('yeniSahipTelefon');
      hataKutusu.classList.add('d-none');
      if (!adEl.value.trim()) {
        hataKutusu.textContent = 'Ad zorunludur.'; hataKutusu.classList.remove('d-none'); return;
      }
      kaydet.disabled = true;
      try {
        const csrf = form.querySelector('input[name="csrf_token"]');
        const basliklar = {'Content-Type': 'application/json', 'Accept': 'application/json'};
        if (csrf) basliklar['X-CSRFToken'] = csrf.value;
        const r = await fetch(ekleUrl, {
          method: 'POST', headers: basliklar,
          body: JSON.stringify({ad: adEl.value, soyad: soyadEl.value, telefon: telEl.value})
        });
        const k = await r.json();
        if (!r.ok) throw new Error(k.hata || 'Müşteri eklenemedi.');
        sahipEkle(k);
        adEl.value = soyadEl.value = telEl.value = '';
      } catch (hata) {
        hataKutusu.textContent = hata.message || 'Müşteri eklenemedi.';
        hataKutusu.classList.remove('d-none');
      } finally {
        kaydet.disabled = false;
      }
    });
  }

  // ------------------------------------------------------------ hemen ilana çıkar
  const ilanaCikar = document.getElementById('ilana_cikar');
  if (ilanaCikar) {
    const alanlar = document.getElementById('ilanAlanlari');
    const tip = document.getElementById('ilan_teklif_tipi');
    function ilanUygula() {
      alanlar.classList.toggle('d-none', !ilanaCikar.checked);
      alanlar.querySelectorAll('[data-teklif]').forEach(function (b) {
        const acik = ilanaCikar.checked && b.dataset.teklif === tip.value;
        b.classList.toggle('d-none', !acik);
        b.querySelectorAll('input').forEach(function (i) { i.disabled = !acik; });
      });
    }
    ilanaCikar.addEventListener('change', ilanUygula);
    tip.addEventListener('change', ilanUygula);
    ilanUygula();
  }
})();
