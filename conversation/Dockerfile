FROM ibaytar/python3.12-odbc-pandas-requests

WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN pip install --no-cache-dir "poetry==1.8.3"

COPY . /app
RUN poetry install

CMD ["poetry", "run", "uvicorn", "src.entrypoints.api.fastapi_main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]