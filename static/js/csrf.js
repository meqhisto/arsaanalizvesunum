/*
 * CSRF token'ını (meta[name="csrf-token"]) aynı kökene giden her yazma isteğine ekler:
 *  - POST formlarına gizli alan olarak (sonradan eklenen formlar ve form.submit() dahil),
 *  - fetch ve XMLHttpRequest isteklerine X-CSRFToken başlığı olarak.
 * <head> içinde, diğer betiklerden önce yüklenmelidir.
 */
(function () {
  'use strict';

  function token() {
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.getAttribute('content') : '';
  }

  function ayniKoken(adres) {
    try { return new URL(adres, window.location.href).origin === window.location.origin; }
    catch (e) { return false; }
  }

  function yazmaMi(yontem) {
    return !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(yontem || 'GET');
  }

  function formaEkle(form, gonderen) {
    if (!form || form.tagName !== 'FORM') return;
    var yontem = (gonderen && gonderen.getAttribute('formmethod')) || form.getAttribute('method') || 'get';
    if (!yazmaMi(yontem)) return;
    var hedef = (gonderen && gonderen.getAttribute('formaction')) || form.getAttribute('action') || window.location.href;
    if (!ayniKoken(hedef)) return;
    var alan = form.querySelector('input[name="csrf_token"]');
    if (!alan) {
      alan = document.createElement('input');
      alan.type = 'hidden';
      alan.name = 'csrf_token';
      form.appendChild(alan);
    }
    alan.value = token();
  }

  // Yakalama aşaması: sayfadaki diğer submit işleyicilerinden önce çalışır
  document.addEventListener('submit', function (e) { formaEkle(e.target, e.submitter); }, true);

  // form.submit() submit olayı üretmez
  var asilSubmit = HTMLFormElement.prototype.submit;
  HTMLFormElement.prototype.submit = function () { formaEkle(this); return asilSubmit.call(this); };

  if (window.fetch) {
    var asilFetch = window.fetch;
    window.fetch = function (girdi, secenek) {
      var istekMi = typeof Request !== 'undefined' && girdi instanceof Request;
      var yontem = (secenek && secenek.method) || (istekMi ? girdi.method : 'GET');
      var adres = istekMi ? girdi.url : String(girdi);
      if (yazmaMi(yontem) && ayniKoken(adres)) {
        var basliklar = new Headers((secenek && secenek.headers) || (istekMi ? girdi.headers : undefined));
        if (!basliklar.has('X-CSRFToken')) basliklar.set('X-CSRFToken', token());
        secenek = Object.assign({}, secenek, { headers: basliklar });
      }
      return asilFetch.call(this, girdi, secenek);
    };
  }

  var asilOpen = XMLHttpRequest.prototype.open;
  var asilSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (yontem, adres) {
    this._csrfEkle = yazmaMi(yontem) && ayniKoken(adres);
    return asilOpen.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function () {
    if (this._csrfEkle) {
      try { this.setRequestHeader('X-CSRFToken', token()); } catch (e) { /* istek açılmamış */ }
    }
    return asilSend.apply(this, arguments);
  };
})();
