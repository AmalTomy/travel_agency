import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class WeatherAPI:
    def get_alerts(self, latitude, longitude):
        url = f"http://api.openweathermap.org/data/2.5/onecall?lat={latitude}&lon={longitude}&exclude=minutely,hourly,daily&appid={settings.OPENWEATHERMAP_API_KEY}"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            data = response.json()
            return data.get('alerts', [])
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return []

class TrafficAPI:
    def get_incidents(self, latitude, longitude):
        # Implement this method using a traffic API of your choice
        # This is a placeholder and needs to be implemented with a real API
        return []  # Return an empty list for now
