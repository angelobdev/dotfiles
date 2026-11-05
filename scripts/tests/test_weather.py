#!/usr/bin/env python3
"""weather.py: the forecast it prints, the cache, and what it says offline."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import weather  # noqa: E402

FORECAST = {
    'current': {'time': '2026-11-05T14:15', 'temperature_2m': 17.4, 'apparent_temperature': 14.7, 'weather_code': 0, 'is_day': 1,
                'wind_speed_10m': 15.9},
    'hourly': {'time': [f'2026-11-05T{hour:02}:00' for hour in range(24)], 'temperature_2m': [float(h) for h in range(24)],
               'weather_code': [61] * 24, 'precipitation_probability': [40] * 24, 'is_day': [1] * 18 + [0] * 6},
    'daily': {'time': ['2026-11-05', '2026-11-06'], 'weather_code': [3, 61], 'temperature_2m_max': [19.2, 16.0],
              'temperature_2m_min': [12.0, 11.6]},
}


class WeatherTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        for patcher in (mock.patch.object(weather, 'CACHE', Path(folder.name)), mock.patch.object(weather, 'language', return_value='it_IT'),
                        mock.patch.object(weather, 'tr', side_effect=lambda key, args=(): key)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def answers(self, url, timeout=10):
        if 'geocoding-api' in url:
            return {'results': [{'latitude': 39.3, 'longitude': 16.25, 'name': 'Cosenza'}]}
        if 'nominatim' in url:
            return {'address': {'town': 'Santa Maria a Vico'}}
        return FORECAST

    def test_now_from_geoclue_named_by_openstreetmap(self):
        with mock.patch.object(weather, 'fetch', side_effect=self.answers), mock.patch.object(weather, 'geoclue', return_value=(41.03, 14.47)):
            result = weather.now('')
        self.assertEqual((result['place'], result['current']['temp'], result['current']['feels'], result['error']), ('Santa Maria a Vico', 17, 15, ''))
        self.assertEqual([hour['time'] for hour in result['hours']], ['15:00', '17:00', '19:00', '21:00', '23:00'])
        self.assertEqual(result['days'][1], {'date': '2026-11-06', 'code': 61, 'max': 16, 'min': 12})

    def test_a_city_is_geocoded(self):
        with mock.patch.object(weather, 'fetch', side_effect=self.answers) as fetch, mock.patch.object(weather, 'geoclue') as geoclue:
            self.assertEqual(weather.now('Cosenza')['place'], 'Cosenza')
        geoclue.assert_not_called()
        self.assertTrue(any('geocoding-api' in call.args[0] for call in fetch.call_args_list))

    def test_an_unknown_city_says_so(self):
        with mock.patch.object(weather, 'fetch', return_value={'results': []}):
            self.assertEqual(weather.now('Atlantide')['error'], 'weather.errors.cityNotFound')

    def test_offline_shows_the_last_reading(self):
        with mock.patch.object(weather, 'fetch', side_effect=self.answers), mock.patch.object(weather, 'geoclue', return_value=(41.03, 14.47)):
            weather.now('')
        cache = weather.CACHE / 'weather.json'
        cache.write_text(json.dumps(dict(json.loads(cache.read_text()), updated=0)))
        with mock.patch.object(weather, 'fetch', side_effect=OSError('offline')):
            result = weather.now('')
        self.assertEqual((result['stale'], result['error'], result['current']['temp']), (True, 'weather.errors.unavailable', 17))


if __name__ == '__main__':
    unittest.main()
