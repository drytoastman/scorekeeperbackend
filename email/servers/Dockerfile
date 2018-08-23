FROM python:3.6.5-slim-stretch

RUN apt-get update && apt-get install -y dovecot-imapd iputils-ping net-tools procps tcpdump vim

RUN openssl req -new -x509 -nodes -subj '/CN=testing.com/O=Testing/C=US' -days 3650 -out /etc/dovecot/cert.pem -keyout /etc/dovecot/key.pem
RUN chmod 0600 /etc/dovecot/key.pem
RUN useradd -d /home/testing -ms /bin/bash testing
RUN sh -c 'echo "testing\ntesting" | passwd testing'

COPY test-smtp.py /usr/bin
COPY dovecot.conf /etc/dovecot/dovecot.conf
COPY maildir /var/maildirs/testing
RUN  chown -R testing:testing /var/maildirs/testing

CMD ["bash"]

