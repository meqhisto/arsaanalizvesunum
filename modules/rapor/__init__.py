# -*- coding: utf-8 -*-
"""Arsa analiz raporları: PDF, Word ve PowerPoint.

Kullanım:
    model = build_report_model(analiz, user, detail_url=...)
    path = generate_report(model, 'pdf', out_dir)
"""
import os

from .assets import build_assets
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
