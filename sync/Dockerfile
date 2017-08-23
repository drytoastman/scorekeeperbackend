FROM python:3.6.1-alpine
COPY requirements.txt /tmp
RUN apk add --no-cache libpq \
    && apk add --no-cache --virtual buildreq gcc musl-dev linux-headers postgresql-dev \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apk del buildreq
COPY . /tmp/app
RUN pip install /tmp/app
CMD ["syncserver.py"]
