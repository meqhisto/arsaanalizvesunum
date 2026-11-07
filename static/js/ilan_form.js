/* İlan formu: mal sahibi (tek seçim), sahibin gayrimenkulleri, teklif tipine göre alanlar, emsal satırları,
 * canlı özet ve karşılaştırma. Hesaplar modules/ilan_hesap.py ile aynı formülleri izler; kesin sonuç
 * sunucudaki ilan detay sayfasıdır. */
(function () {
  'use strict';
  const form = document.getElementById('ilanForm');
  if (!form) return;

  // ------------------------------------------------------------ sayı yardımcıları
  // ilan_hesap.tutar_ayristir ile aynı kurallar: '4.250.000' / '1.250,50' / '1250.5'
  function tutar(metin) {
    if (metin === null || metin === undefined) return null;
    let s = String(metin).trim().replace(/\s/g, '');
    if (!s) return null;
    if (s.indexOf('.') !== -1 && s.indexOf(',') !== -1) {
      s = s.replace(/\./g, '').replace(',', '.');
    } else if (s.indexOf(',') !== -1) {
      s = s.replace(',', '.');
    } else if (s.indexOf('.') !== -1) {
      const gruplar = s.split('.');
      const haneler = gruplar.join('').replace(/^[-+]/, '').length;
      const ilk = gruplar[0].replace(/^[-+]/, '');
      const binlik = gruplar[gruplar.length - 1].length === 3 && ilk !== '0' && (gruplar.length > 2 || haneler > 3);
      if (binlik) s = s.replace(/\./g, '');
    }
    if (!/^-?(\d+\.?\d*|\.\d+)$/.test(s)) return null;
    const n = parseFloat(s);
    return isFinite(n) ? n : null;
  }
  const bicim = new Intl.NumberFormat('tr-TR', {maximumFractionDigits: 2});
  const bicim1 = new Intl.NumberFormat('tr-TR', {maximumFractionDigits: 1});
  function sayi(n) { return n === null || n === undefined ? '—' : bicim.format(n); }
  function para(n) { return n === null || n === undefined ? '—' : bicim.format(Math.round(n)) + ' TL'; }

  function deger(ad) {
    const el = form.querySelector('[name="' + ad + '"]');
    return el ? tutar(el.value) : null;
  }

  // ------------------------------------------------------------ teklif tipi
  function tip() {
    const r = form.querySelector('input[name="teklif_tipi"]:checked');
    return r ? r.value : 'satilik';
  }
  function tipiUygula() {
    const t = tip();
    form.querySelectorAll('[data-teklif]').forEach(function (b) {
      b.classList.toggle('d-none', b.dataset.teklif.split(' ').indexOf(t) === -1);
    });
    hesapla();
  }
  form.querySelectorAll('input[name="teklif_tipi"]').forEach(function (r) { r.addEventListener('change', tipiUygula); });

  // ------------------------------------------------------------ gayrimenkul satırları
  const gmListe = document.getElementById('gmSatirlari');
  const gmBos = document.getElementById('gmBos');

  function satirDurumu(satir) {
    const kutu = satir.querySelector('input[name="gayrimenkul_id[]"]');
    const secili = kutu.checked;
    const ana = satir.querySelector('input[name="ana_gayrimenkul_id"]');
    ana.disabled = !secili;
    if (!secili) ana.checked = false;
  }
  function anaGuncelle() {
    const seciliAnalar = gmListe.querySelectorAll('input[name="ana_gayrimenkul_id"]:not(:disabled)');
    if (seciliAnalar.length && !gmListe.querySelector('input[name="ana_gayrimenkul_id"]:checked')) {
      seciliAnalar[0].checked = true;
    }
  }
  gmListe.addEventListener('change', function (e) {
    if (e.target.name === 'gayrimenkul_id[]') {
      satirDurumu(e.target.closest('[data-gm]'));
      anaGuncelle();
    }
    hesapla();
  });

  function gmSatiriEkle(g) {
    if (gmListe.querySelector('[data-gm][data-id="' + g.id + '"]')) return;
    const satir = document.createElement('div');
    satir.className = 'list-group-item px-2';
    satir.dataset.gm = '';
    satir.dataset.id = g.id;
    satir.dataset.m2 = g.m2 === null ? '' : g.m2;
    satir.dataset.kaks = g.kaks === null ? '' : g.kaks;

    const gizli = document.createElement('input');
    gizli.type = 'hidden'; gizli.name = 'gosterilen_gayrimenkul[]'; gizli.value = g.id;

    const sira = document.createElement('div');
    sira.className = 'row g-2 align-items-center';

    const sol = document.createElement('div');
    sol.className = 'col-12 col-md-7 d-flex gap-2 align-items-start';
    const kutu = document.createElement('input');
    kutu.className = 'form-check-input mt-1 flex-shrink-0'; kutu.type = 'checkbox'; kutu.id = 'gm' + g.id;
    kutu.name = 'gayrimenkul_id[]'; kutu.value = g.id; kutu.setAttribute('aria-label', 'İlana ekle');
    const etiket = document.createElement('label');
    etiket.className = 'form-check-label text-break'; etiket.htmlFor = kutu.id;
    const baslik = document.createElement('span'); baslik.className = 'fw-semibold'; baslik.textContent = g.baslik;
    etiket.appendChild(baslik);
    if (g.ozet) {
      const oz = document.createElement('span'); oz.className = 'd-block small text-muted'; oz.textContent = g.ozet;
      etiket.appendChild(oz);
    }
    if (g.aktif_ilan_kodu) {
      const uy = document.createElement('span'); uy.className = 'd-block small text-warning-emphasis';
      uy.textContent = g.aktif_ilan_kodu + ' numaralı aktif ilanda';
      etiket.appendChild(uy);
    }
    sol.append(kutu, etiket);

    const orta = document.createElement('div');
    orta.className = 'col-7 col-md-3';
    const fiyat = document.createElement('input');
    fiyat.className = 'form-control form-control-sm'; fiyat.name = 'parsel_fiyati[]'; fiyat.inputMode = 'decimal';
    fiyat.placeholder = 'Parsel fiyatı (TL)'; fiyat.setAttribute('aria-label', 'Parsel fiyatı');
    const fiyatId = document.createElement('input');
    fiyatId.type = 'hidden'; fiyatId.name = 'parsel_gayrimenkul_id[]'; fiyatId.value = g.id;
    orta.append(fiyatId, fiyat);

    const sag = document.createElement('div');
    sag.className = 'col-5 col-md-2';
    const fc = document.createElement('div'); fc.className = 'form-check mb-0';
    const ana = document.createElement('input');
    ana.className = 'form-check-input'; ana.type = 'radio'; ana.id = 'ana' + g.id; ana.name = 'ana_gayrimenkul_id';
    ana.value = g.id; ana.disabled = true;
    const anaEt = document.createElement('label'); anaEt.className = 'form-check-label small'; anaEt.htmlFor = ana.id;
    anaEt.textContent = 'Ana kayıt';
    fc.append(ana, anaEt);
    sag.appendChild(fc);

    sira.append(sol, orta, sag);
    satir.append(gizli, sira);
    gmListe.appendChild(satir);
    gmBos.classList.add('d-none');
  }

  // Sahip değişince: seçilmemiş satırları kaldır, sahibin gayrimenkullerini ekle
  async function sahipGayrimenkulleri(contactId) {
    gmListe.querySelectorAll('[data-gm]').forEach(function (s) {
      if (!s.querySelector('input[name="gayrimenkul_id[]"]').checked) s.remove();
    });
    if (contactId) {
      try {
        const url = form.dataset.sahipUrl.replace('/0/', '/' + encodeURIComponent(contactId) + '/');
        const r = await fetch(url, {headers: {'Accept': 'application/json'}});
        if (r.ok) (await r.json()).forEach(gmSatiriEkle);
      } catch (hata) { /* liste boş kalır */ }
    }
    gmBos.classList.toggle('d-none', gmListe.children.length > 0);
    hesapla();
  }

  // ------------------------------------------------------------ mal sahibi (tek seçim)
  const sahipKutusu = document.getElementById('sahipler');
  if (sahipKutusu) {
    const araUrl = sahipKutusu.dataset.araUrl, ekleUrl = sahipKutusu.dataset.ekleUrl;
    const ara = document.getElementById('sahipAra'), sonuclar = document.getElementById('sahipSonuclar');
    const govde = document.getElementById('sahipSatirlari'), bos = document.getElementById('sahipBos');

    function bosGuncelle() { bos.classList.toggle('d-none', govde.children.length > 0); }

    function sahipSec(k) {
      govde.innerHTML = '';
      const tr = document.createElement('tr');
      tr.dataset.id = k.id;
      const kisi = document.createElement('td');
      const ad = document.createElement('div'); ad.textContent = k.ad;
      const tel = document.createElement('div'); tel.className = 'small text-muted'; tel.textContent = k.telefon || '';
      const gizli = document.createElement('input'); gizli.type = 'hidden'; gizli.name = 'sahip'; gizli.value = k.id;
      kisi.append(ad, tel, gizli);
      const silTd = document.createElement('td'); silTd.className = 'text-end';
      silTd.innerHTML = '<button type="button" class="btn btn-sm btn-link text-danger p-0" data-sahip-cikar aria-label="Çıkar"><i class="fas fa-times"></i></button>';
      tr.append(kisi, silTd);
      govde.appendChild(tr);
      bosGuncelle();
      sahipGayrimenkulleri(k.id);
    }

    govde.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-sahip-cikar]');
      if (btn) { btn.closest('tr').remove(); bosGuncelle(); sahipGayrimenkulleri(null); }
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
            a.addEventListener('click', function () { sahipSec(k); ara.value = ''; sonuclar.classList.add('d-none'); });
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
        sahipSec(k);
        adEl.value = soyadEl.value = telEl.value = '';
      } catch (hata) {
        hataKutusu.textContent = hata.message || 'Müşteri eklenemedi.';
        hataKutusu.classList.remove('d-none');
      } finally {
        kaydet.disabled = false;
      }
    });
  }

  // ------------------------------------------------------------ emsaller
  const emsalListe = document.getElementById('emsalSatirlari');
  const emsalBos = document.getElementById('emsalBos');
  const emsalSablon = document.getElementById('emsalSablon');
  function emsalBosGuncelle() { emsalBos.classList.toggle('d-none', emsalListe.children.length > 0); }
  document.getElementById('emsalEkle').addEventListener('click', function () {
    emsalListe.appendChild(emsalSablon.content.cloneNode(true));
    emsalBosGuncelle();
    tipiUygula();
    const son = emsalListe.lastElementChild;
    if (son) { const ilk = son.querySelector('input'); if (ilk) ilk.focus(); }
  });
  emsalListe.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-emsal-sil]');
    if (btn) { btn.closest('[data-emsal-satir]').remove(); emsalBosGuncelle(); hesapla(); }
  });

  // ------------------------------------------------------------ canlı hesap (ilan_hesap ile aynı formüller)
  function seciliParseller() {
    return Array.from(gmListe.querySelectorAll('[data-gm]')).filter(function (s) {
      return s.querySelector('input[name="gayrimenkul_id[]"]').checked;
    }).map(function (s) {
      return {m2: tutar(s.dataset.m2), kaks: tutar(s.dataset.kaks)};
    });
  }

  function bolgeOrtalamasi(t) {
    const satirlar = Array.from(emsalListe.querySelectorAll('[data-emsal-satir]'));
    if (t === 'kat_karsiligi') {
      const paylar = satirlar.map(function (s) { return tutar(s.querySelector('[data-emsal="pay"]').value); })
        .filter(function (p) { return p !== null; });
      if (paylar.length) return {deger: paylar.reduce(function (a, b) { return a + b; }, 0) / paylar.length, kaynak: paylar.length + ' emsal'};
      const elle = deger('bolge_pay_yuzde_elle');
      return elle !== null ? {deger: elle, kaynak: 'elle girildi'} : null;
    }
    let m2 = 0, fiyat = 0, adet = 0;
    satirlar.forEach(function (s) {
      const em2 = tutar(s.querySelector('[data-emsal="m2"]').value);
      const ef = tutar(s.querySelector('[data-emsal="fiyat"]').value);
      if (em2 && ef !== null) { m2 += em2; fiyat += ef; adet += 1; }
    });
    if (m2) return {deger: fiyat / m2, kaynak: adet + ' emsal'};
    const elle = deger('bolge_m2_fiyat_elle');
    return elle !== null ? {deger: elle, kaynak: 'elle girildi'} : null;
  }

  function konumlandirma(t, fark) {
    if (fark === null) return null;
    if (fark < -5) return t === 'kat_karsiligi' ? 'Müteahhit için cazip' : 'Bölgeye göre uygun';
    if (fark <= 5) return 'Piyasa seviyesinde';
    return t === 'kat_karsiligi' ? 'Talep bölge ortalamasının üstünde' : 'Bölgenin üstünde';
  }

  function yaz(id, metin) { const el = document.getElementById(id); if (el) el.textContent = metin; }

  function hesapla() {
    const t = tip();
    const parseller = seciliParseller();
    const toplam = parseller.reduce(function (a, p) { return a + (p.m2 || 0); }, 0);
    const elle = deger('insaat_alani_elle');
    let insaat = null, eksik = 0;
    if (elle !== null) {
      insaat = elle;
    } else {
      eksik = parseller.filter(function (p) { return !p.kaks; }).length;
      if (parseller.length && eksik < parseller.length) {
        insaat = parseller.reduce(function (a, p) { return a + (p.kaks ? (p.m2 || 0) * p.kaks : 0); }, 0);
      }
    }
    const pay = deger('sahip_payi_yuzde');
    yaz('canliToplam', toplam ? sayi(toplam) + ' m²' : '—');
    yaz('canliInsaat', insaat !== null ? sayi(insaat) + ' m²' : '—');
    yaz('canliSahibe', insaat !== null && pay !== null ? sayi(insaat * pay / 100) + ' m²' : '—');
    const uyari = document.getElementById('canliKaksUyari');
    if (uyari) uyari.classList.toggle('d-none', !(eksik > 0 && elle === null));

    let istenen = null;
    if (t === 'kat_karsiligi') {
      istenen = pay;
    } else {
      const tutar_ = deger(t === 'kiralik' ? 'kira' : 'fiyat');
      if (tutar_ !== null && toplam) istenen = tutar_ / toplam;
    }
    yaz('canliM2', t !== 'kat_karsiligi' && istenen !== null ? para(istenen) + '/m²' : '—');

    const kutu = document.getElementById('karsilastirma');
    const bolge = bolgeOrtalamasi(t);
    kutu.innerHTML = '';
    const satir = document.createElement('div');
    if (!bolge) {
      satir.className = 'small text-muted';
      satir.textContent = 'Karşılaştırma için emsal ya da bölge değeri girin.';
      kutu.appendChild(satir);
      return;
    }
    const bolgeMetni = t === 'kat_karsiligi' ? '%' + bicim1.format(bolge.deger) : para(bolge.deger) + '/m²';
    let metin = 'Bölge ort. ' + bolgeMetni + ' (' + bolge.kaynak + ')';
    const fark = istenen !== null && bolge.deger ? (istenen - bolge.deger) / bolge.deger * 100 : null;
    if (fark !== null) {
      const yon = fark > 0 ? 'üstünde' : (fark < 0 ? 'altında' : 'eşit');
      metin += ', talep %' + bicim1.format(Math.abs(fark)) + ' ' + yon;
    }
    satir.textContent = metin;
    kutu.appendChild(satir);
    const konum = konumlandirma(t, fark);
    if (konum) {
      const k = document.createElement('div');
      k.className = 'fw-semibold';
      k.textContent = konum;
      kutu.appendChild(k);
    }
  }

  form.addEventListener('input', function (e) {
    if (e.target.id !== 'sahipAra') hesapla();
  });

  gmListe.querySelectorAll('[data-gm]').forEach(satirDurumu);
  anaGuncelle();
  tipiUygula();
})();
