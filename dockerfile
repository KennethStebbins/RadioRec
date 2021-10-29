FROM python:3.9.7-slim-bullseye

COPY docker_prep_root.sh .
RUN /bin/bash docker_prep_root.sh

USER radiorec:radiorec
WORKDIR /home/radiorec

COPY docker_prep_user.sh .
RUN /bin/bash docker_prep_user.sh

COPY app app
COPY main.py .
COPY LICENSE .

ENV VIRTUAL_ENV="/home/radiorec/.pyvenv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

ENTRYPOINT [ "python", "main.py", "--output", "/output" ]