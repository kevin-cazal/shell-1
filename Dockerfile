# syntax=docker/dockerfile:1
# Static Shell 101–102 site (Vite dist), served by nginx.

FROM node:20-alpine AS build

RUN apk add --no-cache curl

WORKDIR /app

# Build context must include initialized submodules (CI: actions/checkout submodules: recursive).
COPY . .

RUN test -f submodules/v86-runner/package.json \
 || (echo "Missing submodules — run: git submodule update --init --recursive" >&2 && exit 1)

RUN npm ci \
 && npm ci --prefix submodules/v86-runner \
 && cp -f public/coi-serviceworker.js submodules/v86-runner/public/

ARG VITE_BASE=/
ARG VITE_OFFICIAL_BUNDLE_URL=https://cdn.cazal.eu/shell-1-256M.v86b
ARG VITE_MIRROR_BUNDLE_URL=https://github.com/kevin-cazal/vm-image-discover-linux-1/releases/latest/download/shell-1-256M.v86b
ARG VITE_VM_MEMORY_MB=256

ENV VITE_BASE=${VITE_BASE} \
    VITE_OFFICIAL_BUNDLE_URL=${VITE_OFFICIAL_BUNDLE_URL} \
    VITE_MIRROR_BUNDLE_URL=${VITE_MIRROR_BUNDLE_URL} \
    VITE_VM_MEMORY_MB=${VITE_VM_MEMORY_MB}

RUN npm run prepare && npm run build

FROM nginx:1.27-alpine AS runtime

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
