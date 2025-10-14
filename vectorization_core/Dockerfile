# Builder стадия с компиляторами
FROM python:3.12-slim as builder

# Установить build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

# Собрать все пакеты включая fasttext
RUN poetry install --no-root --only main

# Runtime стадия без компиляторов
FROM python:3.12-slim as runtime

# Установить только runtime dependencies (если нужны)
RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Скопировать собранное виртуальное окружение
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Скопировать код
COPY src ./src

# В Dockerfile измените CMD:
CMD ["uvicorn", "src.entrypoints.api.fastapi_main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--timeout-keep-alive", "3000", \
     "--workers", "1"]

