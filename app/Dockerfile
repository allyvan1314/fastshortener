FROM python:3.8-slim-buster

WORKDIR /app  

COPY ./requirements.txt .

RUN pip install -U pip && \
    pip install -r requirements.txt

COPY . .