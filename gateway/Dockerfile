FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY main.py helpers.py config.yml ./

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV CONFIG_FILE=/app/config.yml

CMD ["python3", "main.py"]