/* Auto-generated from portfolio_detail.html */
import React from "react";

export const rawHtml = "<h2>{{ portfolio.title }}</h2>\r\n<p class=\"text-muted\">{{ portfolio.description }}</p>\r\n<p>\r\n    <strong>Analiz Sayısı:</strong> {{ portfolio.analizler.count() }}<br>\r\n    <strong>Toplam Değer:</strong> {{ \"{:,.2f}\".format(portfolio.analizler.with_entities(db.func.sum(ArsaAnaliz.fiyat)).scalar() or 0) }} TL<br>\r\n    <strong>Ortalama Fiyat:</strong> \r\n    {{ \"{:,.2f}\".format((portfolio.analizler.with_entities(db.func.avg(ArsaAnaliz.fiyat)).scalar() or 0)) }} TL\r\n</p>\r\n<hr>\r\n<h5>Portföydeki Analizler</h5>\r\n<table class=\"table\">\r\n    <thead>\r\n        <tr>\r\n            <th>İl</th>\r\n            <th>İlçe</th>\r\n            <th>Fiyat</th>\r\n            <th>İşlem</th>\r\n        </tr>\r\n    </thead>\r\n    <tbody>\r\n        {% for analiz in portfolio.analizler %}\r\n        <tr>\r\n            <td>{{ analiz.il }}</td>\r\n            <td>{{ analiz.ilce }}</td>\r\n            <td>{{ \"{:,.2f}\".format(analiz.fiyat) }} TL</td>\r\n            <td>\r\n                <form method=\"post\" action=\"{{ url_for('portfolio_remove_analiz', id=portfolio.id, analiz_id=analiz.id) }}\" style=\"display:inline;\">\r\n                    <button type=\"submit\" class=\"btn btn-danger btn-sm\">Çıkar</button>\r\n                </form>\r\n            </td>\r\n        </tr>\r\n        {% endfor %}\r\n    </tbody>\r\n</table>\r\n<a href=\"{{ url_for('portfolio_add_analiz', id=portfolio.id) }}\" class=\"btn btn-success\">Analiz Ekle</a>\r\n<a href=\"{{ url_for('portfolios') }}\" class=\"btn btn-secondary\">Geri</a> ";

export default function PortfolioDetail(props: { html?: string; wrapperClassName?: string }) {
  const { html = rawHtml, wrapperClassName } = props;
  return (
    <div className={wrapperClassName} dangerouslySetInnerHTML={{ __html: html }} />
  );
}
