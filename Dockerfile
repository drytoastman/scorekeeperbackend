FROM python:3.7.5-slim-buster as base

# Install our basic requirements, mainly wkhtmltopdf here
RUN    apt-get update \
    && mkdir -p /usr/share/man/man1 /usr/share/man/man7 \
    && apt-get install --no-install-recommends -y \
            fonts-liberation \
            libfontconfig \
            libpq-dev \
            libxext6 \
            libxrender1 \
            nginx \
            postgresql-client \
            procps \
            vim \
            wget \
            xz-utils \
    && wget -q https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz \
    && tar xf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz --strip 1 \
    && rm -rf wkhtml* /bin/wkhtmltoimage /var/lib/apt/lists/* /var/log/*

# Install any build requirements, do the module install and then remove build requirements
COPY requirements.txt /tmp
RUN    apt-get update \
    && apt-get install -y gcc git \
    && pip install --no-cache-dir --disable-pip-version-check -r /tmp/requirements.txt \
    && apt-get autoremove -y gcc git \
    && rm -rf /var/lib/apt/lists/* /var/log/*

# Use pip to install packages to a known location in a builder image
FROM python:3.7.5-slim-buster as builder
COPY . /tmp/base
ENV PYTHONWARNINGS="ignore"
RUN pip3 install --no-deps --disable-pip-version-check --install-option='--prefix=/install' /tmp/base/common /tmp/base/email /tmp/base/sync /tmp/base/web /tmp/base/dns

# Now create the final image from our base and builder pieces
FROM base
COPY --from=builder /install /usr/local
STOPSIGNAL SIGINT
