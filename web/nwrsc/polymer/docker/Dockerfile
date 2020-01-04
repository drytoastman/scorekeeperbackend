FROM node:13.5.0-buster-slim
RUN npm install -g --unsafe-perm polymer-cli@1.9.1
RUN apt-get update && apt-get install -y nginx procps
RUN sed -i 's/root .*;/root \/code;/g' /etc/nginx/sites-available/default
WORKDIR /code
