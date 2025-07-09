import os
from flask import Flask, render_template_string
import requests
from dotenv import load_dotenv

load_dotenv()

ZABBIX_USER = os.getenv('ZABBIX_USER')
ZABBIX_PASSWORD = os.getenv('ZABBIX_PASSWORD')
ZABBIX_URL = os.getenv('ZABBIX_URL')

app = Flask(__name__)

# Função para autenticar no Zabbix
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

# Função para buscar hosts
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
    html = '''
    <h1>Hosts do Zabbix</h1>
    <table border="1">
        <tr><th>ID</th><th>Host</th><th>Nome</th></tr>
        {% for host in hosts %}
        <tr>
            <td>{{ host.hostid }}</td>
            <td>{{ host.host }}</td>
            <td>{{ host.name }}</td>
        </tr>
        {% endfor %}
    </table>
    '''
    return render_template_string(html, hosts=hosts)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True) 