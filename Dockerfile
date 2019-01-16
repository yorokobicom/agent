FROM python:alpine

RUN apk add make g++ zeromq-dev postgresql-dev git

RUN git clone https://github.com/yorokobicom/agent /opt/yorokobi

WORKDIR /opt/yorokobi
RUN python setup.py install

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

ENTRYPOINT ["yorokobid"]
