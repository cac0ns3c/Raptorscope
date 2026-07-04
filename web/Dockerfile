# SPDX-License-Identifier: GPL-3.0-or-later
# Build the SPA and serve the static bundle via nginx, proxying /api -> api:8000.
FROM node:20-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE=/api
ARG VITE_KIBANA_URL=
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_KIBANA_URL=$VITE_KIBANA_URL
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
