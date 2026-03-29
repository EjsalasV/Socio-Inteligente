FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

# Copiar solo lo necesario para FastAPI
COPY backend ./backend
COPY domain ./domain
COPY analysis ./analysis
COPY core ./core
COPY infra ./infra
COPY llm ./llm
COPY app ./app
COPY data/catalogos ./data/catalogos
COPY data/conocimiento_normativo ./data/conocimiento_normativo

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"]
