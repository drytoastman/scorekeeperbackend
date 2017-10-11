FROM python:3.6.3-alpine3.6
COPY requirements.txt /tmp
RUN apk add --no-cache libpq libstdc++ libjpeg-turbo freetype \
    && apk add --no-cache --virtual buildreq g++ gcc musl-dev linux-headers libffi-dev libjpeg-turbo-dev freetype-dev postgresql-dev \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apk del buildreq
COPY . /tmp/app
RUN pip install /tmp/app
RUN assets_preload.py
CMD ["webserver.py"]
