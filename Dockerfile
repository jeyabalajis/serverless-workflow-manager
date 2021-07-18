FROM python:3.7-alpine as base

RUN apk update && apk add python3-dev \
                        gcc \
                        libc-dev

FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN python -m pip install --user boto3

COPY . /app

WORKDIR /app

CMD ["python", "./sqs_poller.py"]