import os
from flask import Flask, render_template
import requests
from dotenv import load_dotenv

load_dotenv()

ZABBIX_USER = os.getenv('ZABBIX_USER')
ZABBIX_PASSWORD = os.getenv('ZABBIX_PASSWORD')
ZABBIX_URL = os.getenv('ZABBIX_URL')

app = Flask(__name__)

def zabbix_login():
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1,
        "auth": None
    }
    response = requests.post(ZABBIX_URL, json=payload)
    result = response.json()
    return result.get('result')

def get_zabbix_hosts(auth_token):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid", "host", "name"]
        },
        "auth": auth_token,
        "id": 2
    }
    response = requests.post(ZABBIX_URL, json=payload)
    result = response.json()
    return result.get('result', [])

@app.route('/')
def index():
    auth_token = zabbix_login()
    if not auth_token:
        return "Erro ao autenticar no Zabbix", 500
    hosts = get_zabbix_hosts(auth_token)
    return render_template('hosts.html', hosts=hosts)

if __name__ == '__main__':
    app.run(debug=True) 