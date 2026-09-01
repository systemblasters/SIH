FROM python:3.11-slim

# Install Node.js for Next.js
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend Python packages
COPY backend/requirements.txt /app/backend/requirements.txt
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

# Copy backend code
COPY backend/ /app/backend/

# Copy frontend code
COPY frontend/ /app/frontend/

# Install frontend packages and build
WORKDIR /app/frontend
RUN npm install
RUN npm run build

WORKDIR /app

# Expose port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run backend and frontend together
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port 8000 & npm --prefix /app/frontend start"]