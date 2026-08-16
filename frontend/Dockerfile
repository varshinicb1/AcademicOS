# Flutter web is built on the host (flutter build web --release) and this
# Dockerfile just packages the static output — running the Flutter SDK
# inside the image would mean a much larger build context and a much
# slower build for no benefit, since `flutter build web` output is just
# static HTML/JS/assets.
FROM nginx:1.27-alpine

COPY build/web /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Cloud Run injects the listen port via $PORT (default 8080); nginx's
# official image already runs envsubst over anything in
# /etc/nginx/templates/*.template into /etc/nginx/conf.d/ on startup, so
# ${PORT} in the template below gets substituted automatically — no custom
# entrypoint needed.
ENV PORT=8080
EXPOSE 8080
