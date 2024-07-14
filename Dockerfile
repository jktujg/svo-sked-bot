FROM python:3.12-alpine

WORKDIR /svo-sked-bot

RUN apk add git

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ARG UPDATE_METHOD="long-polling"
ENV UPDATE_METHOD=${UPDATE_METHOD}

CMD python main.py --update-method ${UPDATE_METHOD}
