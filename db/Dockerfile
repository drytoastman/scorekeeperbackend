FROM postgres:9.6.3-alpine
RUN apk --no-cache add openssl
ENV POSTGRES_DB=scorekeeper
COPY docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
