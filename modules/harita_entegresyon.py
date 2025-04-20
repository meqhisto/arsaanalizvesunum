# Plotly ile 3D Harita Görselleştirme
import plotly.express as px
import pandas as pd

def harita_olustur(dosya_yolu):
    df = pd.read_csv(dosya_yolu)
    fig = px.scatter_3d(
        df,
        x='enlem',
        y='boylam',
        z='fiyat',
        color='imar_tipi',
        size='metrekare',
        hover_data=['bolge', 'tapu_durumu'],
        title='3D Arsa Haritası'
    )
    fig.update_layout(scene_zaxis_type="log")
    fig.show()

# Kullanım
harita_olustur('arsa_verileri.csv')