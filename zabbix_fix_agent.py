import requests
import time

ZABBIX_URL = "http://zabbix-web:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"
TARGET_HOST = "Zabbix server"
TARGET_AGENT = "zabbix-agent"

# Aguarda o Zabbix Web/API ficar disponível
# e também o banco de dados estar inicializado

def wait_zabbix():
    print("[INFO] Aguardando Zabbix Web/API ficar disponível...")
    for i in range(30):
        try:
            r = requests.get(ZABBIX_URL.replace("/api_jsonrpc.php", "/"))
            if r.status_code == 200:
                print(f"[INFO] Zabbix Web disponível após {i*5} segundos.")
                return
        except Exception as e:
            print(f"[DEBUG] Tentativa {i+1}: {e}")
        time.sleep(5)
    raise Exception("Zabbix Web não ficou disponível a tempo.")

def wait_zabbix_db_ready():
    print("[INFO] Aguardando banco de dados do Zabbix estar pronto...")
    for i in range(60):
        try:
            resp = requests.post(ZABBIX_URL, json={
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
                "id": 1
            })
            if resp.status_code == 200:
                data = resp.json()
                if 'result' in data:
                    print(f"[INFO] Login bem-sucedido após {i*5} segundos.")
                    return data['result']
                elif 'error' in data and 'dbversion' in str(data['error']):
                    print("[INFO] Banco de dados ainda não inicializado, aguardando...")
                else:
                    print(f"[DEBUG] Resposta inesperada: {data}")
        except Exception as e:
            print(f"[DEBUG] Tentativa login {i+1}: {e}")
        time.sleep(5)
    raise Exception("Banco de dados do Zabbix não ficou pronto a tempo.")

def zabbix_api(method, params, auth=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    if auth:
        payload["auth"] = auth
    print(f"[INFO] Chamando API: {method}")
    r = requests.post(ZABBIX_URL, json=payload)
    r.raise_for_status()
    resp = r.json()
    if 'error' in resp:
        print(f"[ERROR] Erro na API: {resp['error']}")
        raise Exception(resp['error'])
    return resp["result"]

def main():
    try:
        wait_zabbix()
        # Aguarda o banco de dados estar pronto e faz login
        auth = wait_zabbix_db_ready()
        print(f"[INFO] Token de autenticação: {auth}")
        # Busca host
        print(f"[INFO] Buscando host '{TARGET_HOST}'...")
        hosts = zabbix_api("host.get", {
            "output": ["hostid", "host"],
            "filter": {"host": [TARGET_HOST]}
        }, auth)
        if not hosts:
            print("[ERROR] Host não encontrado.")
            return
        hostid = hosts[0]["hostid"]
        print(f"[INFO] HostID encontrado: {hostid}")
        # Busca interfaces
        print("[INFO] Buscando interfaces do host...")
        interfaces = zabbix_api("hostinterface.get", {
            "hostids": hostid,
            "output": "extend"
        }, auth)
        if not interfaces:
            print("[ERROR] Nenhuma interface encontrada.")
            return
        agent_iface = [i for i in interfaces if i["type"] == "1"]
        if not agent_iface:
            print("[ERROR] Nenhuma interface de agente encontrada.")
            return
        iface = agent_iface[0]
        print(f"[INFO] Interface atual: DNS={iface['dns']} USEIP={iface['useip']}")
        if iface["dns"] == TARGET_AGENT and iface["useip"] == "0":
            print("[INFO] Já está correto. Nada a fazer.")
            return
        # Atualiza interface
        print(f"[INFO] Atualizando interface para DNS={TARGET_AGENT} USEIP=0...")
        zabbix_api("hostinterface.update", {
            "interfaceid": iface["interfaceid"],
            "dns": TARGET_AGENT,
            "useip": "0"
        }, auth)
        print("[INFO] Interface do agente atualizada para DNS:", TARGET_AGENT)
    except Exception as e:
        print(f"[FATAL] {e}")

if __name__ == "__main__":
    main() 