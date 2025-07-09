import os
from flask import Flask, render_template_string
import requests
from dotenv import load_dotenv
import configparser
import time

load_dotenv()

ZABBIX_USER = os.getenv('ZABBIX_USER')
ZABBIX_PASSWORD = os.getenv('ZABBIX_PASSWORD')
ZABBIX_URL = os.getenv('ZABBIX_URL')

if not ZABBIX_URL:
    raise ValueError("A variável de ambiente ZABBIX_URL não está definida.")

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
    response = requests.post(ZABBIX_URL, json=payload, verify=False)
    result = response.json()
    return result.get('result')

# Função para ler filtros do search.ini
def ler_filtros_search_ini():
    config = configparser.ConfigParser()
    config.read('search.ini')
    hosts = []
    itens = []
    if 'search' in config:
        hosts = [h.strip() for h in config['search'].get('hosts', '').split(',') if h.strip()]
        itens = [i.strip() for i in config['search'].get('itens', '').split(',') if i.strip()]
    return hosts, itens

# Função para buscar hosts filtrando por LIKE
def get_zabbix_hosts_like(auth_token, host_likes):
    hosts_encontrados = []
    for host_like in host_likes:
        termo = f"*{host_like}*" if not host_like.startswith('*') and not host_like.endswith('*') else host_like
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid", "host", "name"],
                "search": {"host": termo},
                "searchWildcardsEnabled": True
            },
            "auth": auth_token,
            "id": 2
        }
        response = requests.post(ZABBIX_URL, json=payload, verify=False)
        result = response.json()
        hosts_encontrados.extend(result.get('result', []))
    # Remover duplicados por hostid
    hosts_unicos = {h['hostid']: h for h in hosts_encontrados}.values()
    return list(hosts_unicos)

# Função para buscar itens filtrando por LIKE e pegar múltiplos valores e estatísticas
def get_latest_data_for_items(auth_token, hostid, item_likes):
    itens_encontrados = []
    agora = int(time.time())
    um_dia = 86400
    dois_dias = 2 * um_dia
    sete_dias = 7 * um_dia
    for item_like in item_likes:
        termo = f"*{item_like}*" if not item_like.startswith('*') and not item_like.endswith('*') else item_like
        payload = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["itemid", "name"],
                "hostids": hostid,
                "search": {"name": termo},
                "searchWildcardsEnabled": True
            },
            "auth": auth_token,
            "id": 3
        }
        response = requests.post(ZABBIX_URL, json=payload, verify=False)
        result = response.json()
        for item in result.get('result', []):
            # Buscar os 3 valores mais recentes
            payload_history_latest = {
                "jsonrpc": "2.0",
                "method": "history.get",
                "params": {
                    "output": "extend",
                    "history": 0,  # 0 = float, 3 = string, 1 = int
                    "itemids": item['itemid'],
                    "sortfield": "clock",
                    "sortorder": "DESC",
                    "limit": 3
                },
                "auth": auth_token,
                "id": 4
            }
            response_history_latest = requests.post(ZABBIX_URL, json=payload_history_latest, verify=False)
            history_latest = response_history_latest.json().get('result', [])
            latest_values = [h.get('value', 'N/A') for h in history_latest]
            # Buscar valores dos últimos 1, 2 e 7 dias
            def get_history_stats(period):
                payload_history = {
                    "jsonrpc": "2.0",
                    "method": "history.get",
                    "params": {
                        "output": "extend",
                        "history": 0,
                        "itemids": item['itemid'],
                        "sortfield": "clock",
                        "sortorder": "DESC",
                        "time_from": agora - period,
                        "limit": 10000
                    },
                    "auth": auth_token,
                    "id": 5
                }
                response_history = requests.post(ZABBIX_URL, json=payload_history, verify=False)
                history = response_history.json().get('result', [])
                valores = [float(h['value']) for h in history if 'value' in h]
                if valores:
                    media = sum(valores) / len(valores)
                    pico = max(valores)
                else:
                    media = 'N/A'
                    pico = 'N/A'
                return media, pico
            media_1d, _ = get_history_stats(um_dia)
            media_2d, _ = get_history_stats(dois_dias)
            media_7d, pico_7d = get_history_stats(sete_dias)
            itens_encontrados.append({
                'itemid': item['itemid'],
                'name': item['name'],
                'latest': latest_values[0] if len(latest_values) > 0 else 'N/A',
                'latest2': latest_values[1] if len(latest_values) > 1 else 'N/A',
                'latest3': latest_values[2] if len(latest_values) > 2 else 'N/A',
                'media_1d': media_1d,
                'media_2d': media_2d,
                'media_7d': media_7d,
                'pico_7d': pico_7d
            })
    return itens_encontrados

@app.route('/')
def index():
    auth_token = zabbix_login()
    if not auth_token:
        return "Erro ao autenticar no Zabbix", 500
    host_likes, item_likes = ler_filtros_search_ini()
    hosts = get_zabbix_hosts_like(auth_token, host_likes)
    hosts_itens = []
    for host in hosts:
        itens = get_latest_data_for_items(auth_token, host['hostid'], item_likes)
        hosts_itens.append({
            'hostid': host['hostid'],
            'host': host['host'],
            'name': host['name'],
            'itens': itens
        })
    html = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hosts e Itens do Zabbix</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; }
            .table-hosts { margin-bottom: 40px; }
            .table-items th, .table-items td { font-size: 0.95em; }
            .table-items th { background: #e9ecef; }
            .host-title { font-size: 1.2em; font-weight: bold; color: #0d6efd; }
        </style>
    </head>
    <body>
    <div class="container mt-5">
        <h1 class="mb-4">Hosts e Itens do Zabbix</h1>
        <table class="table table-bordered table-striped align-middle table-hosts">
            <thead class="table-dark">
                <tr><th>ID</th><th>Host</th><th>Nome</th></tr>
            </thead>
            <tbody>
            {% for host in hosts_itens %}
            <tr>
                <td>{{ host.hostid }}</td>
                <td class="host-title">{{ host.host }}</td>
                <td>{{ host.name }}</td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="table-responsive">
                    <table class="table table-bordered table-hover table-items mb-0">
                        <thead>
                        <tr>
                            <th>Item</th>
                            <th>Latest</th>
                            <th>Latest2</th>
                            <th>Latest3</th>
                            <th>Média 1d</th>
                            <th>Média 2d</th>
                            <th>Média 7d</th>
                            <th>Pico 7d</th>
                        </tr>
                        </thead>
                        <tbody>
                        {% for item in host.itens %}
                        <tr>
                            <td>{{ item.name }}</td>
                            <td>{{ item.latest }}</td>
                            <td>{{ item.latest2 }}</td>
                            <td>{{ item.latest3 }}</td>
                            <td>{{ item.media_1d }}</td>
                            <td>{{ item.media_2d }}</td>
                            <td>{{ item.media_7d }}</td>
                            <td>{{ item.pico_7d }}</td>
                        </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    </div>
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
    </body>
    </html>
    '''
    return render_template_string(html, hosts_itens=hosts_itens)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True) 