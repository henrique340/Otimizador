FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html
COPY frontend/index.html ./index.html
COPY frontend/styles.css ./styles.css
COPY frontend/app.js ./app.js

EXPOSE 80
