FROM python:3.10.10-slim as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH="/opt/app:$PYTHONPATH"

WORKDIR /opt/app

COPY ./requirements.txt  ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./

CMD ["python", "main.py"]
