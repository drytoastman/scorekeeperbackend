FROM postgres:9.6.3-alpine
RUN apk --no-cache add openssl socat
ENV POSTGRES_DB=scorekeeper
ENV POSTGRES_PASSWORD=thisgetsoverwrittenlater
COPY docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
COPY custom-entrypoint.sh /usr/local/bin
ENTRYPOINT ["custom-entrypoint.sh"]
