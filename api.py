import json
import requests
import time
import threading
from flask import Flask
from datetime import date, timedelta, datetime

today = date.today()
yesterday = today - timedelta(days = 1)
hour = str(datetime.now()) +':00'

def token():
    payload_token = "{\"Email\":\"<EMAIL>\",\"PhoneNumber\":\"<PHONE>\"}"
    headers_token = {
        'accept-encoding': 'gzip',
        'content-type': 'application/json',
        'host': 'rocme.ute.com.uy',
        'user-agent': 'okhttp/3.8.1',
    }

    return 'Bearer ' + requests.request("POST", "https://rocme.ute.com.uy/api/v1/token", headers=headers_token, data=payload_token).text

def active_energy():
    url = "https://rocme.ute.com.uy/api/v2/device/<ID>/curvefromtodate/H/" + \
        str(yesterday) + "/"+str(today)
    headers = {
        'accept-encoding': 'gzip',
        'content-type': 'application/json',
        'host': 'rocme.ute.com.uy',
        'user-agent': 'okhttp/3.8.1',
        'Authorization': str(token())
    }

    response = requests.request("GET", url, headers=headers).json()
    for x in response['data']:
        if str(x['label']) == hour and x['magnitudeVO'] == 'IMPORT_ACTIVE_ENERGY':
            return x['value']

def reading_request():
    url = "https://rocme.ute.com.uy/api/v1/device/readingRequest"

    payload = "{\"AccountServicePointId\":<ID>}"
    headers = {
    'accept-encoding': 'gzip',
    'connection': 'Keep-Alive',
    'content-length': '32',
    'content-type': 'application/json; charset=utf-8',
    'host': 'rocme.ute.com.uy',
    'user-agent': 'okhttp/3.8.1',
    'Authorization': str(token())
    }

    response = requests.request("POST", url, headers=headers, data=payload).json()
    return response

def reading_get():
    url = "https://rocme.ute.com.uy/api/v1/device/<ID>/lastReading/30"

    headers = {
    'accept-encoding': 'gzip',
    'content-type': 'application/json',
    'host': 'rocme.ute.com.uy',
    'user-agent': 'okhttp/3.8.1',
    'Authorization': str(token())
    }

    response = requests.request("GET", url, headers=headers).json()
    reading = {}
    try:
        reading['V'] = float(response['data']['readings'][0]['valor'])
        reading['I'] = float(response['data']['readings'][1]['valor'])
        reading['kW'] = (float(reading['V'])*float(reading['I']))/1000
        reading['kWh'] = active_energy()
        reading['hour'] = (datetime.now() - timedelta(hours= 3)).strftime("%H:%M")
    finally:
        return reading

def current_reading():
    reading_request()
    while reading_get() == '{}':
        time.sleep(15)
    else:
        return reading_get()
    
def data():
    while True:
        while current_reading() == {}:
            print('wait')
            time.sleep(15)
        else:
            print('ok')
            current = current_reading()
            try:
                with open('energy.json','r+') as file:
                    file_data = json.load(file)
                    file_data['energy'].append(current)
                    file.seek(0)
                    json.dump(file_data, file, indent = 4)
                    print('1')
            except:
                with open('energy.json','w') as file:
                    wr= {"energy":[current]}
                    json_object = json.dumps(wr, indent=4)
                    file.write(json_object)
                    print('2')
            time.sleep(300)
            pass

def get_data():
    with open('energy.json','r') as file:
            file_data = json.load(file)
            return file_data['energy'][-1]

global th
th = threading.Thread(target=data)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def energy():
    if not th.is_alive():
        th.start()
    return get_data()

@app.route('/data', methods=['GET'])
def all_data():
    with open('energy.json','r') as file:
        file_data = json.load(file)
        return file_data

app.run(debug=True)
