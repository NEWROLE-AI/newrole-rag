black:
	cd source_management && poetry run black .

mypy:
	cd source_management && poetry run mypy --explicit-package-bases src

build:
	cd source_management && sam build --use-container

deploy:
	cd source_management && sam deploy --config-env dev

start:
	cd source_management && sam local start-api --debug --docker-network host

requirements:
	cd vectorization && poetry export -f requirements.txt --output requirements.txt

migration:
	cd source_management && poetry run alembic revision --autogenerate

migrate:
	cd source_management && poetry run alembic upgrade head
