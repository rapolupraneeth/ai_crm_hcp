# Build the frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Build the backend
FROM python:3.11-slim AS backend-builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend
COPY --from=frontend-builder /app/frontend/dist ./backend/static

WORKDIR /app/backend
RUN mkdir -p /app/backend/uploads

EXPOSE 8000
ENV APP_ENV=production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
