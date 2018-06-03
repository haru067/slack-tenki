import os
import json
import requests
import configparser
from datetime import datetime
 
def get_timestamp_today():
    now = datetime.now()
    return int(datetime(now.year, now.month, now.day , 0, 0, 0).strftime('%s'))

def get_display_time_now():
    now = datetime.now()
    return now.strftime('%H:%M');

def get_rainfall(yahoo_key, coordinates):
    payload = {'appid': yahoo_key, 'coordinates': coordinates, 'output': 'json'}
    response = requests.get('https://map.yahooapis.jp/weather/V1/place', params=payload)
    if response.status_code != 200:
        return None
    j = json.loads(response.text)
    weathers = j['Feature'][0]['Property']['WeatherList']['Weather']
    current =  next(w for w in weathers if w['Type'] == 'observation')
    if 'Rainfall' not in current :
        return None
    return current['Rainfall']

def get_overview(darksky_key, coordinates):
    payload = {'lang': 'ja', 'units': 'si', 'exclude': 'minutely,hourly,alerts,flags'}
    url = f'https://api.darksky.net/forecast/{darksky_key}/{coordinates}'
    response = requests.get(url, params=payload)
    if response.status_code != 200:
        return None
    j = json.loads(response.text)

    current = j['currently']
    time_today = get_timestamp_today()
    today = next(d for d in j['daily']['data'] if d['time'] == time_today)

    result = {
        'icon': current['icon'],
        'temperature': current['temperature'],
        'temperatureMax': today['temperatureMax'],
        'temperatureMin': today['temperatureMin'],
        'summary': today['summary'],
        'summary2': current['summary']
    }
    return result

def main():
    # Init
    filedir = os.path.dirname(os.path.abspath(__file__))
    inifile = configparser.ConfigParser()
    inifile.read(filedir + '/config.ini', 'UTF-8')

    yahoo_key = inifile.get('api', 'yahooKey')
    darksky_key = inifile.get('api', 'darkskyKey')
    coordinates = inifile.get('api', 'coordinates')
    slack_key = inifile.get('api', 'slackKey')

    # Call APIs
    rainfall = get_rainfall(yahoo_key, coordinates)
    overview = get_overview(darksky_key, coordinates)

    # weather API to Slack icon alias
    dic = {
        'clear-day': 'sunny',
        'clear-night': 'crescent_moon',
        'rain': 'umbrella',
        'snow': 'snowman',
        'sleet': 'snowflake',
        'wind': 'cyclone',
        'fog': 'fog',
        'cloudy': 'cloud',
        'partly-cloudy-day': 'partly_sunny',
        'partly-cloudy-night': 'partly_sunny',
    }
    icon = ':tea:' # default
    if overview['icon'] in dic:
        icon = f":{dic[overview['icon']]}:"

    # Post to Slack
    temp = round(overview['temperature'])
    current_time = get_display_time_now()
    message = f"{overview['summary2']} {temp}℃ {current_time}"
    # message = f"{overview['icon']} {overview['summary2']} {overview['temperature']}℃ ({overview['temperatureMin']}℃ - {overview['temperatureMax']}℃)"
    if rainfall:
        message = message + rainfall
    endpoint = 'https://slack.com/api/users.profile.set'
    payload = json.dumps({
        'token': slack_key,
        'profile': {
            "status_text": message,
            "status_emoji": icon
        }
    })
    result = requests.post(endpoint, payload, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + slack_key})

if __name__ == '__main__': main()