FROM debian:stretch-slim

RUN apt-get update

# Download and install wkhtmltopdf
#RUN apt-get install -y build-essential wget 
RUN apt-get install -y wget xz-utils procps libqt5webkit5 ttf-liberation
RUN wget -q https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz && \ 
        tar xf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz --strip 1 && \
        rm wkhtml*


#ENTRYPOINT ["wkhtmltopdf"]
#wkhtmltopdf --disable-smart-shrinking --zoom 0.90 --page-height 5in --page-width 8in <URL>
astname&page=template' test.pdf
CMD ["bash"]

