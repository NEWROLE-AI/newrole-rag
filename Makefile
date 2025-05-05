black:
	cd slack_bot && poetry run black .

mypy:
	cd source_management && poetry run mypy --explicit-package-bases src

build:
	cd conversation && sam build --use-container

deploy:
	cd conversation && sam deploy --config-env dev

start:
	cd vectorization && sam local start-api --debug --docker-network host

requirements:
	cd conversation && poetry export -f requirements.txt --output requirements.txt

migration:
	cd source_management && poetry run alembic revision --autogenerate

migrate:
	cd admin_panel && poetry run alembic upgrade head
