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
    var el = input.parentNode.querySelector('.foto-kucult-bilgi');
    if (!el) {
      el = document.createElement('div');
      el.className = 'foto-kucult-bilgi form-text';
      el.setAttribute('aria-live', 'polite');
      (input.closest('.input-group') || input).insertAdjacentElement('afterend', el);
    }
    el.textContent = metin;
  }

  function bagla(input) {
    var form = input.form;
    var bekleyen = null;

    input.addEventListener('change', function () {
      var dosyalar = Array.prototype.slice.call(input.files || []);
      if (!dosyalar.some(resimMi) || typeof DataTransfer === 'undefined') return;
      bilgi(input, 'Fotoğraflar hazırlanıyor…');
      bekleyen = Promise.all(dosyalar.map(kucult)).then(function (yeni) {
        try {
          var dt = new DataTransfer();
          yeni.forEach(function (f) { dt.items.add(f); });
          input.files = dt.files;
        } catch (e) { /* eski tarayıcı: orijinaller gönderilir */ }
        var toplam = Array.prototype.reduce.call(input.files, function (t, f) { return t + f.size; }, 0);
        bilgi(input, input.files.length + ' dosya hazır (' + (toplam / 1048576).toFixed(1) + ' MB).');
        bekleyen = null;
      });
    });

    if (!form) return;
    form.addEventListener('submit', function (e) {
      if (bekleyen) {
        e.preventDefault();
        var gonderen = e.submitter;
        bekleyen.then(function () {
          if (form.requestSubmit) form.requestSubmit(gonderen || undefined); else form.submit();
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
