FROM python:3.6.5-slim-stretch
RUN apt-get update && apt-get install --no-install-recommends -y git && rm -rf /var/lib/apt/lists/* /var/log/*

COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt 

COPY . /tmp/app
RUN pip install /tmp/app
CMD ["syncserver"]
