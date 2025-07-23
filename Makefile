black:
	cd slack_bot && poetry run black .

mypy:
	cd source_management && poetry run mypy --explicit-package-bases src

build:
	cd source_management && sam build --use-container

deploy:
	cd conversation && sam deploy --config-env dev

start:
	cd source_management && sam local start-api --debug --docker-network host

requirements:
	cd source_management && poetry export -f requirements.txt --output requirements.txt

migration:
	cd source_management && poetry run alembic revision --autogenerate

migrate:
	cd admin_panel && poetry run alembic upgrade head

build_image:
	docker build -t source-management ./source_management && docker build -t conversation ./conversation && docker build -t admin-panel ./admin_panel

