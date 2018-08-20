FROM python:3.6.5-slim-stretch as base

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

# Use pip to install packages to a known location in a builder image
FROM python:3.6.5-slim-stretch as builder
COPY . /tmp/base
RUN pip3 install --install-option="--prefix=/install" /tmp/base/common
RUN pip3 install --install-option="--prefix=/install" /tmp/base/email
RUN pip3 install --install-option="--prefix=/install" /tmp/base/sync
RUN pip3 install --install-option="--prefix=/install" /tmp/base/web

# Now create the final image from our base and builder pieces
FROM base
COPY --from=builder /install /usr/local
