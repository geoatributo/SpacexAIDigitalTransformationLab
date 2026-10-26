# Painel Goldilocks RAG: API FastAPI + front em web/dist. Sem chaves na imagem.
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
# Mesmo origin no Cloud Run: pedidos relativos (/dashboard, /session, …).
ENV VITE_API_URL=
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    PORT=8080 \
    ALLOW_GENERATION=0
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
COPY data/ data/
COPY --from=web /web/dist web/dist
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn lab.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
