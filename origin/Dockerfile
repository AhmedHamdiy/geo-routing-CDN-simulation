FROM nginx:stable-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY origin.conf /etc/nginx/conf.d/origin.conf
COPY index.html /usr/share/nginx/html

EXPOSE 8080