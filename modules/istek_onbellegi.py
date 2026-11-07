# -*- coding: utf-8 -*-
"""Aynı istek içinde tekrar tekrar hesaplanan değerler (ör. yetki kümeleri) için küçük önbellek.

Uzak veritabanında (Supabase) her sorgu ~50 ms sürdüğünden, bir sayfada aynı yetki sorgusunun
satır başına tekrarlanması sayfayı saniyelerce yavaşlatıyordu. Değerler yalnız o isteğin
`flask.g` nesnesinde tutulur; istek dışında (betikler, testlerde app context'i yoksa) önbellek kullanılmaz.
"""
from flask import g, has_request_context


def istek_onbellegi(anahtar, hesapla):
    if not has_request_context():
        return hesapla()
    depo = g.setdefault('_istek_onbellegi', {})
    if anahtar not in depo:
        depo[anahtar] = hesapla()
    return depo[anahtar]
