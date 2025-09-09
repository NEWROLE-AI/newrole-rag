FROM python:3.11-slim

WORKDIR /app

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Установить Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Добавить Poetry в PATH
ENV PATH="/root/.local/bin:$PATH"

# Сначала скопировать только pyproject и poetry.lock
COPY pyproject.toml poetry.lock ./

# Сгенерировать requirements.txt
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt

# Установить зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать код приложения
COPY . .

# Создать пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.entrypoints.api.fastapi_main:app", "--host", "0.0.0.0", "--port", "8000"]
