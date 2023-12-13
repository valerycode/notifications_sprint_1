# Базовый образ с общими системными зависимостями для dev и prod
FROM python:3.10.8-slim as python-base
ARG APP_NAME
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH="/opt/app:$PYTHONPATH"

RUN apt-get update \
    && apt-get --no-install-recommends install -y \
    libpq5 \
    netcat \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Билдер для установки Python пакетов и необходимых системных зависимостей
FROM python-base as builder-base
RUN apt-get update \
    && apt-get --no-install-recommends install -y \
    curl \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /opt/app
COPY requirements.txt .
RUN pip install -r requirements.txt

# development образ
FROM python-base as development

# Копируем python пакеты для продакшена из билдера
COPY --from=builder-base /opt/venv/ /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Устанавливаем dev python пакеты для работы в контейнере
WORKDIR /opt/app
COPY requirements.dev.txt .
RUN pip install -r requirements.dev.txt

COPY ./docker/entrypoint.sh ./docker/wait_for_services.py /opt/
RUN chmod +x /opt/entrypoint.sh

WORKDIR /opt/app
COPY ./src .

ENTRYPOINT ["/opt/entrypoint.sh"]
CMD ["python", "manage.py"]

# 'production' образ
FROM python-base as production

# Копируем только Python пакеты
COPY --from=builder-base /opt/venv/ /opt/venv/
ENV PATH="/opt/venv/bin:${PATH}"

COPY ./docker/entrypoint.sh ./docker/wait_for_services.py /opt/
RUN chmod +x /opt/entrypoint.sh

RUN mkdir -p /opt/app/var/log

WORKDIR /opt/app
COPY ./src .

RUN groupadd -r app && useradd -d /opt/app -r -g app app \
    && chown app:app -R /opt/app
USER app

ENTRYPOINT ["/opt/entrypoint.sh"]
CMD ["gunicorn", "gevent_app:app", "--bind", "0.0.0.0:5000"]
