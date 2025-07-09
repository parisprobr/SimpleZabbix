up:
	docker-compose up -d

down:
	docker-compose down -v --remove-orphans

web:
	docker-compose up -d web-simplezabbix

logs:
	docker-compose logs -f 