FROM python:3.12-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем только файлы зависимостей сначала
COPY pyproject.toml poetry.lock* /app/

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Устанавливаем зависимости без создания виртуального окружения
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копируем оставшийся код
COPY . /app

# Указываем порт
EXPOSE 8000

# Команда запуска приложения
CMD ["uvicorn", "src.entrypoints.api.fastapi_main:app", "--host", "0.0.0.0", "--port", "8000"]
