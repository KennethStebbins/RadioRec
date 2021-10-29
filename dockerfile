FROM selenium/standalone-firefox

WORKDIR /usr/local/radiorec

COPY docker_prep_b.sh .
RUN /bin/sh docker_prep_b.sh

COPY app app
COPY main.py .
COPY LICENSE .

#ENTRYPOINT [ "/usr/bin/python3", "main.py" ]
ENTRYPOINT [ "/bin/bash" ]