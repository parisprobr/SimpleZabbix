# SimpleZabbix

## Objetivo

O SimpleZabbix é um projeto para facilitar a busca rápida de dados do Zabbix, permitindo filtrar hosts e itens de interesse de forma simples, sem a necessidade de navegar pela interface tradicional do Zabbix.

---

## Como usar

### 1. Configuração do `.env`

Crie um arquivo `.env` na raiz do projeto com as variáveis de ambiente necessárias para sua aplicação Python (exemplo):

```
ZABBIX_USER=Admin
ZABBIX_PASSWORD=zabbix
ZABBIX_URL=http://zabbix.local/api_jsonrpc.php
```

Ajuste conforme o ambiente e as credenciais do seu Zabbix.

---

### 2. Configuração do `search.ini`

O arquivo `search.ini` define os filtros de hosts e itens que você deseja buscar no Zabbix. Exemplo:

```
[search]
hosts = web, db, Storage-farm5
itens = cpu, mem, disco
```

- **hosts**: lista de nomes/parciais dos hosts (busca tipo LIKE)
- **itens**: lista de nomes/parciais dos itens (busca tipo LIKE)

---

### 3. Subindo o ambiente

Utilize o `Makefile` para facilitar os comandos:

- **Subir todo o ambiente (Zabbix, banco, app, proxy, etc):**
  ```sh
  make up
  ```

- **Subir apenas a aplicação web-simplezabbix:**
  ```sh
  make web
  ```

- **Ver os logs de todos os serviços:**
  ```sh
  make logs
  ```

- **Derrubar tudo e apagar volumes (reset total):**
  ```sh
  make down
  ```

---

## Acessando

- **Zabbix Web:** http://zabbix.local  (usuário: Admin, senha: zabbix)
- **SimpleZabbix App:** http://simplezabbix.local

> Lembre-se de adicionar as entradas no seu `/etc/hosts`:
> ```
> 127.0.0.1 zabbix.local simplezabbix.local
> ```

---

## Observações
- O ambiente é voltado para testes e desenvolvimento rápido.
- O script `zabbix-fix-agent` garante que o host padrão "Zabbix server" sempre aponte para o agente correto.
- O projeto utiliza Docker Compose para orquestração de todos os serviços.

---

## Licença
MIT 