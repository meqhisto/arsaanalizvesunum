import folium
import requests
from PIL import Image
from io import BytesIO
import os

class MapGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('MAPS_API_KEY')
        
    def generate_map(self, latitude, longitude, zoom=15):
        """Verilen koordinatlar için harita oluşturur"""
        try:
            # Folium ile harita oluştur
            m = folium.Map(location=[latitude, longitude], zoom_start=zoom)
            
            # Konumu işaretle
            folium.Marker(
                [latitude, longitude],
                popup='Arsa Konumu',
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
            
            # Geçici dosya olarak kaydet
            buffer = BytesIO()
            m.save(buffer)
            buffer.seek(0)
            return buffer
        except Exception as e:
            print(f"Harita oluşturma hatası: {e}")
            return None

    def get_static_map(self, latitude, longitude, zoom=15, width=800, height=600):
        """Statik harita görüntüsü alır (Google Maps veya OSM)"""
        try:
            if self.api_key:  # Google Maps kullan
                url = f"https://maps.googleapis.com/maps/api/staticmap"
                params = {
                    'center': f"{latitude},{longitude}",
                    'zoom': zoom,
                    'size': f"{width}x{height}",
                    'markers': f"color:red|{latitude},{longitude}",
                    'key': self.api_key
                }
                response = requests.get(url, params=params)
            else:  # OpenStreetMap kullan
                url = f"https://staticmap.openstreetmap.de/staticmap.php"
                params = {
                    'center': f"{latitude},{longitude}",
                    'zoom': zoom,
                    'size': f"{width}x{height}",
                    'markers': f"{latitude},{longitude},red-dot"
                }
                response = requests.get(url, params=params)
            
            if response.status_code == 200:
                buffer = BytesIO(response.content)
                return buffer
            return None
        except Exception as e:
            print(f"Statik harita alma hatası: {e}")
            return None

    def get_address_coordinates(self, address):
        """Adres metninden koordinatları alır (Geocoding)"""
        try:
            if self.api_key:  # Google Geocoding API
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    'address': address,
                    'key': self.api_key
                }
                response = requests.get(url, params=params)
                data = response.json()
                
                if data['status'] == 'OK':
                    location = data['results'][0]['geometry']['location']
                    return location['lat'], location['lng']
            else:  # Nominatim (OpenStreetMap)
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': address,
                    'format': 'json',
                    'limit': 1
                }
                headers = {'User-Agent': 'ArsaAnalizSistemi/1.0'}
                response = requests.get(url, params=params, headers=headers)
                data = response.json()
                
                if data:
                    return float(data[0]['lat']), float(data[0]['lon'])
            return None
        except Exception as e:
            print(f"Koordinat alma hatası: {e}")
            return None
