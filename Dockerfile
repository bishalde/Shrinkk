# Build CSS + icon sprite
FROM node:22-slim AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY assets ./assets
COPY scripts/build-icons.mjs ./scripts/
COPY templates ./templates
COPY services ./services
COPY public ./public
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0
COPY . .
COPY --from=assets /app/public/static ./public/static
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:create_app()"]
