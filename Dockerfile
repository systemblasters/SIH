FROM python:3.11-slim

# Install Node.js 20, needed to build and run the Next.js frontend.
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend Python dependencies first, so Docker can cache this layer.
COPY backend/requirements.txt /app/backend/requirements.txt

WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend source code.
WORKDIR /app
COPY backend/ /app/backend/
COPY aasist/ /app/aasist/
COPY frontend/ /app/frontend/

# Install and build the frontend.
WORKDIR /app/frontend
RUN npm install
RUN npm run build

WORKDIR /app

# Show Python logs immediately in Render logs.
ENV PYTHONUNBUFFERED=1

# Render gives a public PORT at runtime; 10000 is only a fallback.
EXPOSE 10000

# Start FastAPI internally at port 8000 and Next.js publicly on Render's PORT.
CMD ["sh", "-c", "echo 'Starting FastAPI backend on internal port 8000...' ; uvicorn backend.app:app --host 0.0.0.0 --port 8000 & echo 'Starting Next.js frontend on Render port...' ; npm --prefix /app/frontend start -- -p ${PORT:-10000} -H 0.0.0.0"]