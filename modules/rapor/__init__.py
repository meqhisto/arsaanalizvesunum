# -*- coding: utf-8 -*-
"""İlan / gayrimenkul raporları: PDF, Word ve PowerPoint.

Kullanım:
    model = build_report_model(ilan, ilan.ana_gayrimenkul, user, detail_url=...)   # ilan raporu
    model = build_report_model(None, gayrimenkul, user, detail_url=...)            # tanıtım raporu
    path = generate_report(model, 'pdf', out_dir)
"""
import os
import shutil
import tempfile

from .assets import build_assets  # noqa: F401
from .model import ReportModel, ascii_slug, build_report_model  # noqa: F401

EXTENSIONS = {'pdf': 'pdf', 'word': 'docx', 'pptx': 'pptx'}
MIMETYPES = {
    'pdf': 'application/pdf',
    'word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}


def generate_report(model, fmt, out_dir):
    """Raporu out_dir içine üretir ve dosya yolunu döndürür."""
    if fmt not in EXTENSIONS:
        raise ValueError(f"Desteklenmeyen format: {fmt}")
    assets = build_assets(model, os.path.join(out_dir, 'gorseller'))
    path = os.path.join(out_dir, f"rapor_{model.analiz_id}.{EXTENSIONS[fmt]}")
    if fmt == 'pdf':
        from .pdf import render_pdf
        return render_pdf(model, assets, path)
    if fmt == 'word':
        from .word import render_word
        return render_word(model, assets, path)
    from .pptx_ import render_pptx
    return render_pptx(model, assets, path)


def report_bytes(model, fmt):
    """Raporu geçici klasörde üretip içeriğini döndürür."""
    output_dir = tempfile.mkdtemp(prefix='rapor_')
    try:
        with open(generate_report(model, fmt, output_dir), 'rb') as f:
            return f.read()
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)


def report_response(model, fmt, filename_stem):
    """İndirilebilir Flask yanıtı: '<filename_stem>.<uzantı>'."""
    from flask import make_response
    response = make_response(report_bytes(model, fmt))
    response.headers['Content-Type'] = MIMETYPES[fmt]
    response.headers['Content-Disposition'] = f'attachment; filename="{filename_stem}.{EXTENSIONS[fmt]}"'
    return response
