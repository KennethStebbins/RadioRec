FROM python:3.9.7-slim-bullseye

WORKDIR /usr/local/radiorec

COPY docker_prep.sh .
RUN /bin/sh docker_prep.sh

COPY app app
COPY main.py .
COPY LICENSE .

#ENTRYPOINT [ "/usr/bin/python3", "main.py" ]
ENTRYPOINT [ "/bin/bash" ]