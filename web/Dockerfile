FROM python:3.6.3-alpine3.6 as swaggerui
WORKDIR /tmp
RUN apk update && apk add ca-certificates && update-ca-certificates && apk add openssl
RUN wget https://github.com/swagger-api/swagger-ui/archive/v3.10.0.tar.gz
RUN tar xf *.gz
WORKDIR swagger-ui-3.10.0/dist
RUN rm *.map
RUN sed -i 's/http:\/\/petstore.swagger.io\/v2\/swagger.json/\/api\/swagger.yaml/' index.html


FROM python:3.6.3-alpine3.6
COPY requirements.txt /tmp
RUN apk add --no-cache libpq libstdc++ libjpeg-turbo freetype \
    && apk add --no-cache --virtual buildreq g++ gcc musl-dev linux-headers libffi-dev libjpeg-turbo-dev freetype-dev postgresql-dev git \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apk del buildreq
COPY . /tmp/app
COPY --from=swaggerui /tmp/swagger-ui-3.10.0/dist /tmp/app/nwrsc/static/swaggerui
RUN pip install /tmp/app
RUN python3 /usr/local/bin/assets_preload.py
CMD ["python3", "/usr/local/bin/webserver.py"]
