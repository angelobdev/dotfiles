#!/usr/bin/env python3
"""Weather for the calendar panel, from Open-Meteo (no account).

now [CITY]: prints {"place", "current": {temp, feels, code, day, wind}, "hours": [{time, temp, code, rain}],
"days": [{date, code, max, min}], "updated", "stale", "error"}. The place is CITY when given (Open-Meteo's
geocoding), else where GeoClue says the machine is (city accuracy, kept 6 hours), named from OpenStreetMap.
The forecast is kept 30 minutes; offline, the last one is printed with "stale": true.
"""
from common import write_atomic
from i18n import language, tr
import json
import os
from pathlib import Path
import sys
import time
import urllib.parse
import urllib.request

CACHE = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'desktop'
LOCATION_AGE = 6 * 3600
FORECAST_AGE = 30 * 60
# A generic client name: Nominatim asks for one, and nothing personal goes with it.
AGENT = 'desktop-weather/1.0'


def fetch(url, timeout=10):
    request = urllib.request.Request(url, headers={'User-Agent': AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def read(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def geoclue():
    import gi
    gi.require_version('Geoclue', '2.0')
    from gi.repository import Geoclue
    simple = Geoclue.Simple.new_sync('desktop-weather', Geoclue.AccuracyLevel.CITY, None)
    location = simple.get_location()
    return round(location.get_property('latitude'), 3), round(location.get_property('longitude'), 3)


def place_name(latitude, longitude, code):
    query = urllib.parse.urlencode({'format': 'jsonv2', 'lat': latitude, 'lon': longitude, 'zoom': 10, 'accept-language': code})
    data = fetch('https://nominatim.openstreetmap.org/reverse?' + query)
    address = data.get('address', {})
    return address.get('city') or address.get('town') or address.get('village') or data.get('name') or ''


def locate(city, code):
    cache = CACHE / 'weather-location.json'
    cached = read(cache)
    if cached and cached.get('city') == city and cached.get('language') == code and time.time() - cached.get('at', 0) < LOCATION_AGE:
        return cached
    if city:
        query = urllib.parse.urlencode({'name': city, 'count': 1, 'language': code})
        results = fetch('https://geocoding-api.open-meteo.com/v1/search?' + query).get('results') or []
        if not results:
            raise ValueError(tr('weather.errors.cityNotFound', [city]))
        latitude, longitude, name = results[0]['latitude'], results[0]['longitude'], results[0]['name']
    else:
        latitude, longitude = geoclue()
        try:
            name = place_name(latitude, longitude, code)
        except (OSError, ValueError):
            name = ''
    found = {'city': city, 'language': code, 'at': time.time(), 'latitude': latitude, 'longitude': longitude, 'place': name}
    write_atomic(cache, json.dumps(found, ensure_ascii=False))
    return found


def forecast(location):
    query = urllib.parse.urlencode({
        'latitude': location['latitude'], 'longitude': location['longitude'], 'timezone': 'auto', 'forecast_days': 3,
        'current': 'temperature_2m,apparent_temperature,weather_code,is_day,wind_speed_10m',
        'hourly': 'temperature_2m,weather_code,precipitation_probability,is_day',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min'})
    data = fetch('https://api.open-meteo.com/v1/forecast?' + query)
    current = data['current']
    hourly = data['hourly']
    now = current['time'][:13]
    start = next((index for index, stamp in enumerate(hourly['time']) if stamp[:13] >= now), 0)
    hours = [{'time': hourly['time'][index][11:16], 'temp': round(hourly['temperature_2m'][index]),
              'code': hourly['weather_code'][index], 'rain': hourly['precipitation_probability'][index] or 0,
              'day': hourly['is_day'][index] == 1}
             for index in range(start + 1, min(start + 13, len(hourly['time'])), 2)]
    daily = data['daily']
    days = [{'date': daily['time'][index], 'code': daily['weather_code'][index], 'max': round(daily['temperature_2m_max'][index]),
             'min': round(daily['temperature_2m_min'][index])} for index in range(len(daily['time']))]
    return {'place': location['place'], 'updated': time.time(), 'hours': hours, 'days': days,
            'current': {'temp': round(current['temperature_2m']), 'feels': round(current['apparent_temperature']),
                        'code': current['weather_code'], 'day': current['is_day'] == 1, 'wind': round(current['wind_speed_10m'])}}


def now(city):
    code = 'it' if language() == 'it_IT' else 'en'
    cache = CACHE / 'weather.json'
    cached = read(cache)
    if cached and cached.get('city') == city and time.time() - cached.get('updated', 0) < FORECAST_AGE:
        return dict(cached, stale=False, error='')
    try:
        result = dict(forecast(locate(city, code)), city=city)
        write_atomic(cache, json.dumps(result, ensure_ascii=False))
        return dict(result, stale=False, error='')
    except ValueError as error:
        message = str(error)
    except (OSError, KeyError, IndexError, TypeError):
        message = tr('weather.errors.unavailable')
    except Exception:  # GeoClue raises GLib.Error, which only exists once gi is imported.
        message = tr('weather.errors.noLocation')
    if cached and cached.get('city') == city:
        return dict(cached, stale=True, error=message)
    return {'error': message, 'stale': True}


def main():
    if not sys.argv[1:2] == ['now'] or len(sys.argv) > 3:
        print(tr('weather.errors.usage'), file=sys.stderr)
        return 2
    print(json.dumps(now(sys.argv[2].strip() if len(sys.argv) == 3 else ''), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
