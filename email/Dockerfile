FROM python:3.6.5-slim-stretch

# Install any build requirements, do the module install and then remove build requirements
COPY requirements.txt /tmp
RUN    apt-get update \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -rf /var/lib/apt/lists/* /var/log/*

    #&& apt-get install -y redis \

COPY . /tmp/app
RUN pip install /tmp/app
RUN python3 /usr/local/bin/assets_preload.py
CMD ["python3", "/usr/local/bin/webserver.py"]
