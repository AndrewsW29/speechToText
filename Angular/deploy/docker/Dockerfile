# syntax=docker/dockerfile:1.7
# Build context: Angular/  (docker build -f deploy/docker/Dockerfile .)
FROM node:22.12.0-alpine3.21 AS build
WORKDIR /app
COPY package.json package-lock.json* ./
# Use `npm ci` once package-lock.json is committed (run `npm install` once to generate it).
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
COPY angular.json tsconfig*.json ./
COPY src ./src
RUN npx ng build --configuration production

FROM nginxinc/nginx-unprivileged:1.27.3-alpine3.20
COPY --chown=101:101 deploy/docker/nginx.conf /etc/nginx/nginx.conf
COPY --from=build --chown=101:101 /app/dist/voice-assistant-web/browser /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
CMD ["nginx", "-g", "daemon off;"]
