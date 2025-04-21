# PDF Rapor Oluşturma
from fpdf import FPDF
import pandas as pd

class PDFRapor(FPDF):
    def baslik(self, title):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, title, 0, 1, 'C')
    
    def icerik(self, text):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, text)
    
    def tablo(self, df):
        self.set_font('Arial', 'B', 12)
        for col in df.columns:
            self.cell(40, 10, col, 1)
        self.ln()
        self.set_font('Arial', '', 12)
        for _, row in df.iterrows():
            for item in row:
                self.cell(40, 10, str(item), 1)
            self.ln()

# Kullanım
pdf = PDFRapor()
pdf.add_page()
pdf.baslik("Arsa Yatırım Analiz Raporu")
pdf.icerik("Detaylı analiz sonuçları ve öneriler:")
pdf.tablo(pd.DataFrame({
    'Gösterge': ['Fiyat', 'Metrekare', 'Getiri'],
    'Değer': ['1.5M TL', '1000m²', '%18.5']
}))
pdf.output('analiz_raporu.pdf')