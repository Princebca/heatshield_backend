"""
External API integration for weather and air quality data
"""
import requests
from datetime import datetime

from config import config

OPENWEATHER_API_KEY = config['API_KEYS']['OPENWEATHER_API_KEY']
MOCK_DATA_ENABLED = config['MOCK_DATA']['ENABLED']

class DataFetcher:
    """Fetch environmental data from external APIs"""
    
    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        self.use_mock = MOCK_DATA_ENABLED or self.api_key == "your_api_key_here"
    
    def get_weather_data(self, latitude, longitude):
        """
        Get current weather data for given coordinates
        Returns: temperature, heat_index, humidity, uv_index
        """
        if self.use_mock:
            return self._get_mock_weather()
        
        try:
            # OpenWeatherMap Current Weather API
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric'
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Calculate heat index (feels like temperature)
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            heat_index = self._calculate_heat_index(temp, humidity)
            
            # Get UV index from One Call API
            uv_url = f"https://api.openweathermap.org/data/2.5/uvi"
            uv_params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key
            }
            uv_response = requests.get(uv_url, params=uv_params, timeout=5)
            uv_data = uv_response.json() if uv_response.status_code == 200 else {}
            uv_index = uv_data.get('value', 5.0)
            
            return {
                'temperature': temp,
                'heat_index': heat_index,
                'humidity': humidity,
                'uv_index': uv_index,
                'description': data['weather'][0]['description'],
                'timestamp': datetime.utcnow().isoformat(),
                'location': data.get('name', 'Unknown')
            }
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return self._get_mock_weather()
    
    def get_aqi_data(self, latitude, longitude):
        """
        Get air quality index data for given coordinates
        Returns: AQI, PM2.5, PM10, NO2, SO2, CO, O3
        """
        if self.use_mock:
            return self._get_mock_aqi()
        
        try:
            # OpenWeatherMap Air Pollution API
            url = f"http://api.openweathermap.org/data/2.5/air_pollution"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            components = data['list'][0]['components']
            aqi = data['list'][0]['main']['aqi']
            
            # Convert AQI scale to Indian AQI (0-500)
            # OpenWeather uses 1-5 scale, convert to Indian standard
            aqi_mapping = {1: 50, 2: 100, 3: 200, 4: 300, 5: 400}
            indian_aqi = aqi_mapping.get(aqi, 100)
            
            return {
                'aqi': indian_aqi,
                'category': self._get_aqi_category(indian_aqi),
                'pm2_5': components.get('pm2_5', 0),
                'pm10': components.get('pm10', 0),
                'no2': components.get('no2', 0),
                'so2': components.get('so2', 0),
                'co': components.get('co', 0),
                'o3': components.get('o3', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error fetching AQI data: {e}")
            return self._get_mock_aqi()
    
    def _calculate_heat_index(self, temperature, humidity):
        """
        Calculate heat index (feels like temperature)
        Using simplified formula for Celsius
        """
        if temperature < 27:
            return temperature
        
        # Rothfusz regression formula adapted for Celsius
        T = temperature
        RH = humidity
        
        HI = (-8.78469475556 + 
              1.61139411 * T + 
              2.33854883889 * RH + 
              -0.14611605 * T * RH + 
              -0.012308094 * T * T + 
              -0.0164248277778 * RH * RH + 
              0.002211732 * T * T * RH + 
              0.00072546 * T * RH * RH + 
              -0.000003582 * T * T * RH * RH)
        
        return round(HI, 1)
    
    def _get_aqi_category(self, aqi):
        """Get AQI category based on Indian standards"""
        if aqi <= 50:
            return 'Good'
        elif aqi <= 100:
            return 'Satisfactory'
        elif aqi <= 200:
            return 'Moderate'
        elif aqi <= 300:
            return 'Poor'
        elif aqi <= 400:
            return 'Very Poor'
        else:
            return 'Severe'
    
    def _get_mock_weather(self):
        """Mock weather data for testing"""
        return {
            'temperature': 38.5,
            'heat_index': 45.2,
            'humidity': 65.0,
            'uv_index': 8.5,
            'description': 'hot and humid',
            'timestamp': datetime.utcnow().isoformat(),
            'location': 'Rourkela'
        }
    
    def _get_mock_aqi(self):
        """Mock AQI data for testing"""
        return {
            'aqi': 180,
            'category': 'Moderate',
            'pm2_5': 85.5,
            'pm10': 120.3,
            'no2': 45.2,
            'so2': 25.1,
            'co': 1200.5,
            'o3': 60.8,
            'timestamp': datetime.utcnow().isoformat()
        }

# Test the data fetcher
if __name__ == '__main__':
    print("Testing Data Fetcher...")
    fetcher = DataFetcher()
    
    # Test coordinates for Rourkela, India
    lat, lon = 22.2604, 84.8536
    
    print("\n--- Weather Data ---")
    weather = fetcher.get_weather_data(lat, lon)
    for key, value in weather.items():
        print(f"{key}: {value}")
    
    print("\n--- AQI Data ---")
    aqi = fetcher.get_aqi_data(lat, lon)
    for key, value in aqi.items():
        print(f"{key}: {value}")
