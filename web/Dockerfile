FROM scpythonbase
COPY . /tmp/app
RUN pip install /tmp/app
RUN python3 /usr/local/bin/assets_preload.py
CMD ["python3", "/usr/local/bin/webserver.py"]
