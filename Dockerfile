FROM python:3.13.3-alpine3.20

# Установка зависимостей
RUN apk add --no-cache bash \
    gcc \
    musl-dev \
    libffi-dev \
    cargo \
    rust \
    openssl-dev \
    build-base \
    bash \
    curl \
    postgresql-client


# Устанавливаем Poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем pyproject.toml и poetry.lock (если есть)
COPY pyproject.toml poetry.lock* /app/

# Устанавливаем зависимости через Poetry (без создания виртуалки)
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Копируем всё остальное
COPY . /app/

# Подготавливаем entrypoint
RUN chmod +x /app/scripts/entrypoint_backend.sh && \
    dos2unix /app/scripts/entrypoint_backend.sh

COPY --chmod=0644 .env /app/