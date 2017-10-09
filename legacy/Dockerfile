# docker build -t importer .
# docker run --rm -v {SOCKET_VOL}:/var/run/postgresql importer 
FROM drytoastman/scweb:latest
RUN mkdir -p /import/series /import/archived
COPY olddbimport.py /import
COPY series /import/series/
COPY archived /import/archived/
CMD /import/olddbimport.py '/import/archived/*.db' True && /import/olddbimport.py '/import/series/*.db' False
