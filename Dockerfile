FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

WORKDIR /app/frontend
RUN npm install
RUN npm run build

WORKDIR /app

ENV PYTHONUNBUFFERED=1

EXPOSE 10000

CMD ["sh", "-c", "echo 'Starting FastAPI backend on internal port 8000...' && uvicorn backend.app:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 & echo 'Starting Next.js frontend on Render port...' && npm --prefix /app/frontend start -- -p ${PORT:-10000} -H 0.0.0.0"]