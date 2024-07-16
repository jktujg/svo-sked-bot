FROM python:3.12-alpine

WORKDIR /svo-sked-bot

RUN apk add git

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD python main.py
