/*
 * Fotoğrafları yüklemeden önce tarayıcıda küçültür.
 * Telefon fotoğrafları 3–6 MB (iPhone'da HEIC) olduğu için birkaç tanesi sunucu sınırını aşıyordu.
 * <input type="file" data-foto-kucult> olan alanlara uygulanır: her fotoğraf en fazla 2000 px,
 * JPEG (%85) olarak yeniden yazılır. Videolar ve çözülemeyen dosyalar olduğu gibi gönderilir.
 * Form, küçültme bitene kadar gönderilmez.
 */
(function () {
  'use strict';
  var EN_BUYUK_KENAR = 2000;
  var KALITE = 0.85;
  var SINIR_MB = 95; // sunucu sınırı 100 MB; formun diğer alanlarına pay

  function resimMi(f) {
    return /^image\//.test(f.type) || /\.(heic|heif|jpe?g|png|webp)$/i.test(f.name);
  }

  function resmiCoz(dosya) {
    if (window.createImageBitmap) {
      return createImageBitmap(dosya, { imageOrientation: 'from-image' }).catch(function () {
        return imgIleCoz(dosya);
      });
    }
    return imgIleCoz(dosya);
  }

  function imgIleCoz(dosya) {
    return new Promise(function (coz, reddet) {
      var url = URL.createObjectURL(dosya);
      var img = new Image();
      img.onload = function () { URL.revokeObjectURL(url); coz(img); };
      img.onerror = function () { URL.revokeObjectURL(url); reddet(new Error('çözülemedi')); };
      img.src = url;
    });
  }

  function kucult(dosya) {
    if (!resimMi(dosya) || dosya.type === 'image/gif') return Promise.resolve(dosya);
    return resmiCoz(dosya).then(function (img) {
      var w = img.width, h = img.height;
      var oran = Math.min(1, EN_BUYUK_KENAR / Math.max(w, h));
      // Zaten küçük bir JPEG ise dokunma
      if (oran === 1 && dosya.type === 'image/jpeg' && dosya.size < 1.5 * 1024 * 1024) return dosya;
      var c = document.createElement('canvas');
      c.width = Math.round(w * oran); c.height = Math.round(h * oran);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      if (img.close) img.close();
      return new Promise(function (coz) {
        c.toBlob(function (blob) {
          if (!blob) return coz(dosya);
          var ad = dosya.name.replace(/\.[^.]+$/, '') + '.jpg';
          coz(new File([blob], ad, { type: 'image/jpeg', lastModified: Date.now() }));
        }, 'image/jpeg', KALITE);
      });
    }).catch(function () { return dosya; });
  }

  function bilgi(input, metin) {
    var el = input._fotoBilgi;
    if (!el) {
      el = document.createElement('div');
      el.className = 'foto-kucult-bilgi form-text';
      el.setAttribute('aria-live', 'polite');
      (input.closest('.input-group') || input).insertAdjacentElement('afterend', el);
      input._fotoBilgi = el;
    }
    el.textContent = metin;
  }

  // Tek dosya en fazla bu kadar bekletilir; aşılırsa (ör. tarayıcı biçimi çözemiyor) orijinali gönderilir
  var DOSYA_BASI_BEKLEME_MS = 15000;

  function sureli(dosya) {
    return new Promise(function (coz) {
      var bitti = false;
      var t = setTimeout(function () { if (!bitti) { bitti = true; coz(dosya); } }, DOSYA_BASI_BEKLEME_MS);
      kucult(dosya).then(function (f) { if (!bitti) { bitti = true; clearTimeout(t); coz(f); } });
    });
  }

  // Sırayla işlenir: telefonda birkaç büyük fotoğrafı aynı anda açmak belleği tüketir
  function hepsiniKucult(dosyalar, ilerleme) {
    var sonuc = [];
    return dosyalar.reduce(function (zincir, d, i) {
      return zincir.then(function () {
        ilerleme(i + 1, dosyalar.length);
        return sureli(d).then(function (f) { sonuc.push(f); });
      });
    }, Promise.resolve()).then(function () { return sonuc; });
  }

  function bagla(input) {
    var form = input.form;
    var bekleyen = null;
    var sira = 0;

    input.addEventListener('change', function () {
      var dosyalar = Array.prototype.slice.call(input.files || []);
      var benim = ++sira;
      if (!dosyalar.some(resimMi) || typeof DataTransfer === 'undefined') { bekleyen = null; return; }
      bilgi(input, 'Fotoğraflar hazırlanıyor…');
      var is = hepsiniKucult(dosyalar, function (n, toplam) {
        if (benim === sira) bilgi(input, 'Fotoğraflar hazırlanıyor… (' + n + '/' + toplam + ')');
      }).then(function (yeni) {
        if (benim !== sira) return; // bu arada başka dosyalar seçildi
        try {
          var dt = new DataTransfer();
          yeni.forEach(function (f) { dt.items.add(f); });
          input.files = dt.files;
        } catch (e) { /* eski tarayıcı: orijinaller gönderilir */ }
        var toplam = Array.prototype.reduce.call(input.files, function (t, f) { return t + f.size; }, 0);
        bilgi(input, input.files.length + ' dosya hazır (' + (toplam / 1048576).toFixed(1) + ' MB). Kaydetmek için gönder düğmesine basın.');
      }).catch(function () {
        if (benim === sira) bilgi(input, '');
      }).then(function () { if (bekleyen === is) bekleyen = null; });
      bekleyen = is;
    });

    if (!form) return;
    form.addEventListener('submit', function (e) {
      if (e.defaultPrevented) return;
      if (bekleyen) {
        e.preventDefault();
        var gonderen = e.submitter;
        bilgi(input, 'Fotoğraflar hazırlanıyor, ardından gönderilecek…');
        bekleyen.then(function () {
          if (form.requestSubmit) form.requestSubmit(gonderen && !gonderen.disabled ? gonderen : undefined);
          else form.submit();
        });
        return;
      }
      var toplam = Array.prototype.reduce.call(input.files || [], function (t, f) { return t + f.size; }, 0);
      if (toplam > SINIR_MB * 1048576) {
        e.preventDefault();
        bilgi(input, 'Seçilen dosyalar toplam ' + (toplam / 1048576).toFixed(0) + ' MB; en fazla ' + SINIR_MB + ' MB yüklenebilir. Daha az dosya seçin.');
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('input[type="file"][data-foto-kucult]').forEach(bagla);
  });
})();
