FROM python:3.12

WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN pip install --no-cache-dir poetry==1.8.3

COPY . /app
RUN poetry install

CMD ["poetry", "run", "uvicorn", "src.entrypoints.api.handlers:fastapi_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]