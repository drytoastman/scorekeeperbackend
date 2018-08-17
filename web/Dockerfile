FROM scpythonbase

# Install our basic requirements, mainly wkhtmltopdf here
RUN    apt-get update \
    && apt-get install --no-install-recommends -y libqt5webkit5 procps ttf-liberation wget xz-utils \
    && wget -q https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && tar xf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz --strip 1 \
    && rm -rf wkhtml* /bin/wkhtmltoimage /var/lib/apt/lists/* /var/log/*

# Install any build requirements, do the module install and then remove build requirements
COPY requirements.txt /tmp
RUN    apt-get update \
    && apt-get install -y gcc git \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && apt-get autoremove -y gcc git \
    && rm -rf /var/lib/apt/lists/* /var/log/*

COPY . /tmp/app
RUN pip install /tmp/app
RUN python3 /usr/local/bin/assets_preload.py
CMD ["python3", "/usr/local/bin/webserver.py"]
